"""The one engine behind the planner view, the validation view and the evaluation."""
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from . import physics, rules
from .data import features, inputs_frame, row_inputs
from .model import BLEND_TARGETS, ORDER, DesignModel, Neighbours
from .schema import LABEL, TARGETS, UNIT, Design, HomeInputs

NOUN = {"pv_kwp": "PV", "battery_kwh": "a battery", "heat_pump_kw": "a heat pump", "wallbox_kw": "a wallbox"}
NAME = {"pv_kwp": "PV system", "battery_kwh": "battery", "heat_pump_kw": "heat pump", "wallbox_kw": "wallbox"}


def _got(col: pd.Series) -> pd.Series:
    """Neighbour received the component (NaN = offered, size unknown)."""
    return col.gt(0) | col.isna()


@dataclass
class Designer:
    model: DesignModel
    neighbours: Neighbours
    catalog: dict[str, list[float]]
    blend: float = 0.0  # weight given to the median size of the most similar past homes (0 = model only)

    @classmethod
    def train(cls, df: pd.DataFrame, sizing: str = "mean", sample_weight=None, params: dict | None = None,
              blend: float = 0.0, battery_catalog_top: int = 15) -> "Designer":
        """battery_catalog_top: how many of the most common battery sizes the design snaps to (15 = as before; 40 = all
        sizes installers used). Snapping to only 15 cost battery accuracy: see scripts/improvement_ideas.py."""
        X, Y = features(df), df[list(TARGETS)].astype(float)
        catalog = {t: rules.common_sizes(Y[t].to_numpy(), top=battery_catalog_top if t == "battery_kwh" else 15) for t in TARGETS}
        return cls(DesignModel(sizing, params).fit(X, Y, sample_weight), Neighbours().fit(X, Y), catalog, blend)

    def save(self, path: str | Path) -> None:
        joblib.dump(self, path)

    @staticmethod
    def load(path: str | Path) -> "Designer":
        return joblib.load(path)

    # -- core ---------------------------------------------------------------------------------
    def _run(self, X: pd.DataFrame, inputs: list[HomeInputs], locked: dict[str, float]):
        """Decide component by component; rule adjustments upstream are fed to the model downstream."""
        fixed: dict[str, np.ndarray] = {}
        notes = [[] for _ in inputs]
        flags = [[] for _ in inputs]
        probs = None
        similar = self.neighbours.median_sizes(X, BLEND_TARGETS) if self.blend else None
        for t in ORDER:
            pred = self.model.predict(X, {**fixed, **({t: locked[t]} if t in locked else {})}, similar, self.blend)
            probs = pred if probs is None else probs.assign(**{f"p_{t}": pred[f"p_{t}"]})
            vals = []
            for i, inp in enumerate(inputs):
                current = {k: float(v[i]) for k, v in fixed.items()}
                v, n, f = rules.apply_one(t, pred[t].iat[i], current, inp, self.catalog, locked=t in locked)
                vals.append(v)
                notes[i] += n
                flags[i] += f
            fixed[t] = np.array(vals)
        return fixed, probs, notes, flags

    def design_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        fixed, _, _, _ = self._run(features(df), row_inputs(df), {})
        return pd.DataFrame({t: fixed[t] for t in TARGETS}, index=df.index)

    def design(self, inputs: HomeInputs, locked: dict[str, float] | None = None) -> Design:
        locked = locked or {}
        X = features(inputs_frame(inputs))
        fixed, probs, notes, flags = self._run(X, [inputs], locked)
        values = {t: float(fixed[t][0]) for t in TARGETS}
        p = {t: float(probs[f"p_{t}"].iat[0]) for t in TARGETS}
        flags = flags[0] + self.validate(inputs, values, X)
        return Design(**values, probability=p, explanation=self._explain(inputs, values, p, X, locked),
                      rules_applied=notes[0], flags=flags)

    # -- validation & explanation ---------------------------------------------------------------
    def validate(self, inputs: HomeInputs, values: dict[str, float], X: pd.DataFrame | None = None) -> list[str]:
        """Compare a design (ours or the planner's) with what experts did for similar homes."""
        X = features(inputs_frame(inputs)) if X is None else X
        nb = self.neighbours.query(X)[0]
        out = []
        for t in TARGETS:
            v, col = values[t], nb[t]
            share = _got(col).mean()
            if v > 0 and share < 0.2:
                out.append(f"Unusual: only {share:.0%} of similar homes got {NOUN[t]}.")
            elif v == 0 and share > 0.8:
                out.append(f"Unusual: {share:.0%} of similar homes got {NOUN[t]}, this design has none.")
            elif v > 0 and (col > 0).sum() >= 5:
                pct = (col[col > 0] < v).mean()
                if pct >= 0.9:
                    out.append(f"Unusually large {NAME[t]}: bigger than {pct:.0%} of similar homes.")
                elif pct <= 0.1 and (col[col > 0] > v).mean() >= 0.9:
                    out.append(f"Unusually small {NAME[t]}: smaller than {1 - pct:.0%} of similar homes.")
        return out

    def _explain(self, inputs: HomeInputs, values, p, X, locked) -> list[str]:
        nb = self.neighbours.query(X)[0]
        lines = []
        for t in ORDER:
            v, col = values[t], nb[t]
            share = _got(col).mean()
            med = col[col > 0].median() if (col > 0).any() else 0.0
            if t in locked:
                who = "set by planner"
            elif t == "wallbox_kw":
                who = "rule: home has an EV" if p[t] >= 1.0 else "rule: no EV in the home"
            else:
                who = f"model {p[t]:.0%} sure to include"
            if v > 0:
                lines.append(f"{LABEL[t]} {v:g} {UNIT[t]} ({who}); {share:.0%} of {len(col)} similar homes got one, median {med:g} {UNIT[t]}.")
            else:
                lines.append(f"No {NAME[t]} ({who}); {share:.0%} of {len(col)} similar homes got one.")

        base = physics.num(inputs.annual_consumption_kwh)
        if base:
            ev = physics.ev_demand_kwh(inputs.has_ev, inputs.ev_km_per_year)
            hd = physics.num(inputs.heating_demand_kwh) or physics.heat_demand_kwh(inputs.heated_area_m2)
            hp = physics.heat_pump_electricity_kwh(hd) if values["heat_pump_kw"] > 0 and hd else 0.0
            total = base + ev + hp
            lines.append(f"Expected demand ≈ {total:,.0f} kWh/yr (household {base:,.0f} + EV {ev:,.0f} + heat pump {hp:,.0f}).")
            existing = physics.num(inputs.existing_pv_kwp) or 0.0
            if existing:
                lines.append(f"The home already has {existing:g} kWp of PV.")
            if values["pv_kwp"] > 0:
                gen = physics.pv_yield_kwh(values["pv_kwp"])
                sc = physics.self_consumption_ratio(total, gen, values["battery_kwh"])
                save = physics.annual_pv_savings_eur(total, values["pv_kwp"], values["battery_kwh"],
                                                     inputs.electricity_price_eur_kwh)
                cost = physics.capex_eur(values["pv_kwp"], values["battery_kwh"], 0)
                lines.append(f"PV yields ≈ {gen:,.0f} kWh/yr, ≈{sc:.0%} used at home, saving ≈ €{save:,.0f}/yr; "
                             f"PV+battery payback ≈ {cost / save:.1f} years (rough assumptions).")
        else:
            lines.append("Annual consumption unknown: design relies on similar homes only, so confidence is lower.")
        return lines

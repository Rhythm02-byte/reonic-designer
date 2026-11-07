"""The learned installer policy as one object: train / save / load / design / design_batch / validate / explain.

Decision order heat pump -> PV -> battery -> wallbox. After each step the hard rules (R01-R05, snapping) run and
their result is fed to the next model, so rule adjustments and planner locks flow downstream.

Three modes (config/policy.json, picked on the VALIDATION split by eval/run.py --select):
  "learned"  M1: every component from the learned chain.
  "composite" per-component source chosen on validation: config "sources" maps pv / battery / heatPump / wallbox to one of
             B0 (installer median), B0c (median conditioned on demand bucket / EV / heating), M1 (learned chain),
             H1 (hybrid rule: installer's usual battery, structural heat-pump rule, EV rule), SIM (battery = the simulator's
             economic optimum among the installer's sizes). Rules (R01-R05), snapping, locks and downstream propagation
             (the battery sees the FINAL PV) are identical for every source.
  "hybrid"   H1 (default): learned PV gate + size, battery = the installer's usual (median) battery snapped to its sizes
             (only when there is new or trusted existing PV and the installer usually includes one), heat pump =
             structural rule (baseline.hp_rule), wallbox = EV rule. Rationale: battery size follows kWp at ~0.93 kWh/kWp in
             every segment, and battery presence is not predictable from the inputs beyond the majority class.
"""
from __future__ import annotations

import dataclasses
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import joblib
import numpy as np
import pandas as pd

from engine import baseline as bl
from engine.etl.normalize import DEFAULT_DEMAND_KWH
from engine.models.schemas import Flag, HomeInputs, Interval, ReasonCode
from engine.policy import physics, rules
from engine.policy.chain import ORDER, DesignModel
from engine.policy.features import TARGETS, features, row_from_inputs, targets
from engine.policy.neighbours import Neighbours

COMP = {"pv_kwp": "pv", "battery_kwh": "battery", "heat_pump_kw": "heatPump", "wallbox_kw": "wallbox"}
TARGET_OF = {v: k for k, v in COMP.items()}
LABEL = {"pv_kwp": "PV", "battery_kwh": "Battery", "heat_pump_kw": "Heat pump", "wallbox_kw": "Wallbox"}
NOUN = {"pv_kwp": "PV", "battery_kwh": "a battery", "heat_pump_kw": "a heat pump", "wallbox_kw": "a wallbox"}
NAME = {"pv_kwp": "PV system", "battery_kwh": "battery", "heat_pump_kw": "heat pump", "wallbox_kw": "wallbox"}
UNIT = {"pv_kwp": "kWp", "battery_kwh": "kWh", "heat_pump_kw": "kW", "wallbox_kw": "kW"}
CODE = {"pv_kwp": "PV", "battery_kwh": "BATTERY", "heat_pump_kw": "HEAT_PUMP", "wallbox_kw": "WALLBOX"}

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "policy.json"
DEFAULT_CONFIG = {"mode": "hybrid", "pvGate": 0.5}
MODES = ("hybrid", "learned", "composite")
SOURCES = ("B0", "B0c", "M1", "H1", "SIM")
EXTRA_KEYS = ("sources", "features", "model", "conformal", "sizing")  # optional blocks of config/policy.json
DEFAULT_BATTERY_CATALOG_TOP = 15
SIZING_KEYS = {"coverage", "coverageCandidates", "blend", "batteryCatalogTop"}
MIN_BATTERY_SHARE = 0.5


def load_config(path: str | Path | None = None) -> dict:
    """{"mode": "hybrid"|"learned"|"composite", "pvGate": float, + optional sources / features / model / conformal} from config/policy.json (env ENGINE_POLICY_CONFIG), else defaults."""
    p = Path(path or os.environ.get("ENGINE_POLICY_CONFIG") or CONFIG_PATH)
    cfg = dict(DEFAULT_CONFIG)
    if p.exists():
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if raw.get("mode") in MODES:
                cfg["mode"] = raw["mode"]
            if isinstance(raw.get("pvGate"), (int, float)):
                cfg["pvGate"] = float(raw["pvGate"])
            for k in EXTRA_KEYS:
                if isinstance(raw.get(k), dict):
                    cfg[k] = raw[k]
        except ValueError:
            pass
    return cfg


def sizing_cfg(raw: Mapping | None) -> dict:
    """Validate the opt-in "sizing" block of config/policy.json (all keys optional; {} = the original behaviour):
      coverage            ["pv", "battery"]: size = the value within tolerance of the most plausible expert sizes (quantile spread)
      coverageCandidates  "samples" (default: the quantile predictions) | "catalog" (the battery catalog sizes)
      blend               0..1: weight of the median size of the 25 most similar past homes (PV and battery, before rules + snapping)
      batteryCatalogTop   how many of the most common battery sizes the design snaps to (15 = original; 0 = every installed size)"""
    raw = dict(raw or {})
    bad = set(raw) - SIZING_KEYS
    if bad:
        raise ValueError(f"unknown sizing key(s) {sorted(bad)}")
    out: dict = {}
    cov = [c for c in (raw.get("coverage") or []) if c]
    if set(cov) - {"pv", "battery"}:
        raise ValueError("sizing.coverage may only contain 'pv' and 'battery'")
    if cov:
        out["coverage"] = sorted(set(cov))
    if raw.get("coverageCandidates") not in (None, "samples", "catalog"):
        raise ValueError("sizing.coverageCandidates must be 'samples' or 'catalog'")
    if raw.get("coverageCandidates") == "catalog":
        out["coverageCandidates"] = "catalog"
    b = float(raw.get("blend") or 0.0)
    if not 0.0 <= b <= 1.0:
        raise ValueError("sizing.blend must be in [0, 1]")
    if b:
        out["blend"] = b
    top = raw.get("batteryCatalogTop")
    if top is not None and int(top) != DEFAULT_BATTERY_CATALOG_TOP:
        out["batteryCatalogTop"] = int(top)
    return out


def catalog_counts(Y: pd.DataFrame) -> dict[str, list[list[float]]]:
    """Per target [size, count] of the installed sizes (aggregates only; lets a decision config rebuild the catalog)."""
    out = {}
    for t in TARGETS:
        v = np.round(Y[t].to_numpy(float), 1)
        vals, counts = np.unique(v[v > 0], return_counts=True)
        out[t] = [[float(a), int(c)] for a, c in zip(vals, counts)]
    return out


def catalog_from_counts(counts: list[list[float]], top: int | None) -> list[float]:
    if not counts:
        return []
    return rules.common_sizes(np.repeat([a for a, _ in counts], [int(c) for _, c in counts]), top=top or None)


def installer_battery_stats(df: pd.DataFrame) -> dict[str, dict]:
    """Per installer (and pooled under "all"): how often it includes a battery and which one. Stored in the artifact."""
    if "battery_kwh" not in df:
        return {}
    d = df[df["demand_kwh"].notna()] if "demand_kwh" in df else df
    groups = [("all", d)] + ([(str(i), g) for i, g in d.groupby("installer_id")] if "installer_id" in d else [])
    out = {}
    for key, g in groups:
        if len(g) == 0:
            continue
        bat = g["battery_kwh"]
        has = bat.gt(0) | bat.isna()          # NaN = offered, size unknown
        sized = bat[bat > 0]
        if len(sized):
            freq = sized.round(1).value_counts(normalize=True)
            sizes = sorted(float(x) for x in freq[freq >= 0.02].index) or [float(sized.median())]
            q = [float(v) for v in np.quantile(sized, [0.1, 0.5, 0.9])]
        else:
            sizes, q = [], [0.0, 0.0, 0.0]
        step = float(np.median(np.diff(sizes))) if len(sizes) > 1 else 1.0
        out[key] = {"n": int(len(g)), "share": float(has.mean()), "median": q[1], "p10": q[0], "p90": q[2],
                    "sizes": sizes, "step": max(step, 1.0)}
    return out


def baseline_stats_from(df: pd.DataFrame) -> dict:
    """bl.Stats per installer (and pooled under "all") from the training frame, for the B0 / B0c composite sources."""
    if not {"pv_kwp", "battery_kwh", "wallbox_kw", "demand_kwh"} <= set(df.columns):
        return {}
    d = df.assign(has_pv=df["pv_kwp"] > 0, kwp=df["pv_kwp"], has_battery=df["battery_kwh"] > 0,
                  has_wallbox=df["wallbox_kw"] > 0)
    groups = [("all", d)] + ([(str(i), g) for i, g in d.groupby("installer_id")] if "installer_id" in d else [])
    out = {}
    for key, g in groups:
        try:
            out[key] = bl.fit_stats(g, key)
        except (ValueError, IndexError, KeyError):  # an installer without PV or battery rows: falls back to "all"
            continue
    return out


def _bl_home(row: Mapping) -> dict:
    """Baseline home mapping (same as eval): masked booleans count as no, a missing demand as the tool default."""
    h = dict(row)
    for k in ("has_ev", "has_existing_wallbox"):
        v = h.get(k)
        h[k] = False if v is None or (isinstance(v, float) and np.isnan(v)) else bool(v)
    if h.get("demand_kwh") is None or pd.isna(h["demand_kwh"]):
        h["demand_kwh"] = DEFAULT_DEMAND_KWH
    return h


def _got(col: pd.Series) -> pd.Series:
    """Neighbour received the component (NaN = offered, size unknown)."""
    return col.gt(0) | col.isna()


def _ask_stats(df: pd.DataFrame) -> dict:
    from engine.ask_next import stats_from
    return stats_from(df)


def hit_to_flag(h: rules.Hit) -> Flag:
    return Flag(severity="error" if h.severity == "red" else "warn", code=h.id, message=h.text,
                component=COMP[h.target])


@dataclass
class PolicyDesign:
    values: dict[str, float]                          # target -> size (0 = none)
    probability: dict[str, float]                     # P(component included) from the model / EV rule
    intervals: dict[str, tuple[float, float, float]]  # target -> p10, p50, p90 size if included
    reasons: list[ReasonCode] = field(default_factory=list)
    flags: list[Flag] = field(default_factory=list)
    rules_applied: list[rules.Hit] = field(default_factory=list)

    def confidence(self) -> dict[str, Interval]:
        return {COMP[t]: Interval(p10=round(lo, 2), p50=round(m, 2), p90=round(hi, 2), prob_included=round(self.probability[t], 3))
                for t, (lo, m, hi) in self.intervals.items()}


@dataclass
class Validation:
    flags: list[Flag]
    percentiles: dict[str, float | None]   # component -> percentile (0-100) of the size among similar homes that got one
    similar_share: dict[str, float]        # component -> share of similar homes that got one
    n_similar: int


@dataclass
class Designer:
    model: DesignModel
    neighbours: Neighbours
    catalog: dict[str, list[float]]
    installers: tuple[str, ...] = ()
    n_train: int = 0
    battery_stats: dict = field(default_factory=dict)   # installer (or "all") -> share / median / p10 / p90 / sizes / step
    mode: str = "hybrid"                                # "hybrid" (H1) | "learned" (M1) | "composite"
    pv_gate: float = 0.5                                # P(PV) needed to include PV
    synthetic: bool = False                             # trained on fake data (demo without the confidential dataset)
    baseline_stats: dict | None = None                  # installer (or "all") -> bl.Stats, for the B0 / B0c sources
    feature_cfg: dict | None = None                     # {"physics": bool, "installerPrior": bool}: baked into the trained model
    model_params: dict | None = None                    # regularisation of the boosted trees (training time)
    pv_prior: object | None = None                      # physics.PvPrior fitted on the training rows
    sources: dict | None = None                         # composite: {"pv"|"battery"|"heatPump"|"wallbox": B0|B0c|M1|H1|SIM}
    conformal: dict | None = None                       # target -> split-conformal widening (kWp / kWh) of the p10-p90 interval
    ask_stats: dict | None = None                       # installer (or "all") -> input distributions for "Ask next" (engine/ask_next.py)
    sizing: dict | None = None                          # opt-in sizing options (sizing_cfg): coverage / blend / battery catalog size
    size_counts: dict | None = None                     # target -> [[size, count]] installed sizes, to rebuild the catalog

    # -- training / persistence ---------------------------------------------------------------------
    @classmethod
    def train(cls, df: pd.DataFrame, k: int = 25, config: Mapping | None = None, synthetic: bool = False) -> "Designer":
        """df: canonical training frame (features.training_frame or equivalent): inputs + the four targets.
        `config` ({"mode", "pvGate", "sources", "features", "model", "conformal"}) defaults to config/policy.json."""
        cfg = {**load_config(), **(config or {})}
        installers = tuple(sorted(df["installer_id"].dropna().astype(str).unique())) if "installer_id" in df else ()
        fcfg, params = dict(cfg.get("features") or {}), dict(cfg.get("model") or {})
        Y = targets(df)
        prior = physics.PvPrior().fit(df) if fcfg.get("installerPrior") else None
        X = features(df, installers, physics=bool(fcfg.get("physics")),
                     prior_values=physics.PvPrior.oof(df) if prior is not None else None)
        Xb = features(df, installers) if (fcfg.get("physics") or prior is not None) else X  # neighbours stay on the base features
        sz = sizing_cfg(cfg.get("sizing"))
        counts = catalog_counts(Y)
        catalog = {t: rules.common_sizes(Y[t].to_numpy()) for t in TARGETS}
        if "batteryCatalogTop" in sz:
            catalog["battery_kwh"] = catalog_from_counts(counts["battery_kwh"], sz["batteryCatalogTop"])
        cov = tuple(TARGET_OF[c] for c in sz.get("coverage", ()))
        return cls(DesignModel().fit(X, Y, params, coverage=cov), Neighbours().fit(Xb, Y, k), catalog, installers, len(df),
                   installer_battery_stats(df), cfg["mode"], float(cfg["pvGate"]), synthetic,
                   baseline_stats_from(df), fcfg, params, prior, dict(cfg.get("sources") or {}) or None,
                   dict(cfg.get("conformal") or {}) or None, ask_stats=_ask_stats(df), sizing=sz or None, size_counts=counts)

    def with_config(self, mode: str | None = None, pv_gate: float | None = None, sources: Mapping | None = None,
                    conformal: Mapping | None = None, sizing: Mapping | None = None) -> "Designer":
        """Same trained models, different decision config (shallow copy; used by model selection).
        `sources` / `conformal` / `sizing` replace the stored ones when given (pass {} to clear). Coverage sizing needs the
        quantile models, i.e. a Designer trained with sizing.coverage (otherwise it silently falls back to the plain size)."""
        if mode is not None and mode not in MODES:
            raise ValueError(f"unknown mode {mode!r}")
        extra = {}
        if sources is not None:
            bad = {v for v in sources.values() if v not in SOURCES} | {k for k in sources if k not in TARGET_OF}
            if bad:
                raise ValueError(f"unknown composite source(s) {sorted(bad)}")
            extra["sources"] = dict(sources)
        if conformal is not None:
            extra["conformal"] = dict(conformal) or None
        if sizing is not None:
            sz = sizing_cfg(sizing)
            extra["sizing"] = sz or None
            counts = (getattr(self, "size_counts", None) or {}).get("battery_kwh")
            if counts:
                extra["catalog"] = {**self.catalog, "battery_kwh": catalog_from_counts(counts, sz.get("batteryCatalogTop", DEFAULT_BATTERY_CATALOG_TOP))}
        return dataclasses.replace(self, mode=mode or self.mode, pv_gate=self.pv_gate if pv_gate is None else float(pv_gate), **extra)

    def _X(self, df: pd.DataFrame) -> pd.DataFrame:
        f = self.feature_cfg or {}
        return features(df, self.installers, physics=bool(f.get("physics")), prior=self.pv_prior if f.get("installerPrior") else None)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: str | Path, apply_config: bool = True) -> "Designer":
        """Load the artifact; the decision config in config/policy.json (written by eval --select) wins over the stored one."""
        d = joblib.load(path)
        if not hasattr(d, "battery_stats"):  # artifact from before H1
            d.battery_stats, d.mode, d.pv_gate, d.synthetic = {}, "learned", 0.5, False
        elif apply_config and (CONFIG_PATH.exists() or os.environ.get("ENGINE_POLICY_CONFIG")) and d.battery_stats:
            cfg = load_config()
            d = d.with_config(cfg["mode"], cfg["pvGate"], cfg.get("sources"), cfg.get("conformal"), cfg.get("sizing"))
        return d

    def _stats_for(self, installer) -> dict | None:
        return self.battery_stats.get(str(installer)) or self.battery_stats.get("all")

    def hybrid_active(self) -> bool:
        return self.mode == "hybrid" and bool(self.battery_stats)

    def effective_sources(self) -> dict[str, str]:
        """target -> source in force: M1 everywhere ("learned"), H1 battery + heat pump ("hybrid"), or the composite config."""
        src = {t: "M1" for t in ORDER}
        if self.mode == "hybrid" and self.battery_stats:
            src["heat_pump_kw"] = src["battery_kwh"] = "H1"
        elif self.mode == "composite":
            for comp, s in (self.sources or {}).items():
                if comp in TARGET_OF and s in SOURCES:
                    src[TARGET_OF[comp]] = s
        return src

    def _bstats(self, installer) -> bl.Stats:
        bs = self.baseline_stats or {}
        return bs.get(str(installer)) or bs.get("all") or bl.FALLBACK

    def _baseline_value(self, src: str, t: str, row: Mapping):
        """B0 (installer median bundle) / B0c (median conditioned on demand bucket, EV, heating) for one target."""
        s, home = self._bstats(row.get("installer_id")), _bl_home(row)
        pred = bl.median_bundle(s) if src == "B0" else bl.conditioned(s, home)
        k = -1 if src == "B0" else bl.demand_bucket(home["demand_kwh"])
        if t == "pv_kwp":
            return float(pred.kwp), None, 1.0, bl._pick(s.kwp, k)
        if t == "battery_kwh":
            v = float(pred.battery_kwh)
            return v, list(s.battery_sizes), float(v > 0), bl._pick(s.battery, k)
        if t == "heat_pump_kw":
            v = float(pred.hp_kw)
            return v, [], float(v > 0), (v, v, v)
        v = float(self.model.steps["wallbox_kw"][1]) if pred.wallbox else 0.0
        return v, None, float(v > 0), (v, v, v)

    def _sim_battery(self, i: int, row: Mapping, fixed: dict[str, np.ndarray]):
        """Battery = the simulator's economic optimum for this home with the FINAL PV, among the installer's sizes."""
        st = self._stats_for(row.get("installer_id"))
        if not st or not st["sizes"]:
            return 0.0, [], 0.0, (0.0, 0.0, 0.0)
        sizes, q = list(st["sizes"]), (st["p10"], st["median"], st["p90"])
        pv = fixed["pv_kwp"][i]
        pv = 0.0 if pv != pv else float(pv)
        ex = rules._num(row.get("existing_pv_kwp")) or 0.0
        if not (pv > 0 or (bool(row.get("existing_pv_trusted")) and ex > 0)):
            return 0.0, sizes, 0.0, q
        hp = fixed["heat_pump_kw"][i]
        v = physics.economic_battery(row, pv, sizes, 0.0 if hp != hp else float(hp))
        return v, sizes, float(v > 0), q

    def _source_value(self, src: str, t: str, i: int, row: Mapping, fixed: dict[str, np.ndarray]):
        """Non-learned decision for target t: (raw value, catalog override or None, P(included), (p10, p50, p90))."""
        if src == "H1":
            if t in ("heat_pump_kw", "battery_kwh"):
                return self._hybrid_value(t, i, row, fixed)
            return self._baseline_value("B0c", t, row)  # wallbox: the EV rule
        if src == "SIM" and t == "battery_kwh":
            return self._sim_battery(i, row, fixed)
        return self._baseline_value("B0c" if src == "SIM" else src, t, row)

    # -- core ---------------------------------------------------------------------------------------
    def _hybrid_value(self, t: str, i: int, row: Mapping, fixed: dict[str, np.ndarray]):
        """H1 decision for heat pump / battery: (raw value, catalog override, P(included), (p10, p50, p90))."""
        if t == "heat_pump_kw":
            v = float(bl.hp_rule(row))
            return v, [], float(v > 0), (v, v, v)
        st = self._stats_for(row.get("installer_id"))
        pv = fixed["pv_kwp"][i]
        pv = 0.0 if pv != pv else float(pv)
        ex = rules._num(row.get("existing_pv_kwp")) or 0.0
        eligible = pv > 0 or (bool(row.get("existing_pv_trusted")) and ex > 0)
        if not st:
            return 0.0, [], 0.0, (0.0, 0.0, 0.0)
        sizes, q = list(st["sizes"]), (st["p10"], st["median"], st["p90"])
        if sizes and eligible and st["share"] >= MIN_BATTERY_SHARE:
            return bl.snap(st["median"], sizes), sizes, float(st["share"]), q
        return 0.0, sizes, (float(st["share"]) if eligible else 0.0), q

    def _run(self, X: pd.DataFrame, ctxs: list[Mapping], locked: dict[str, float], rows: list[Mapping] | None = None):
        srcs = self.effective_sources() if rows is not None else {t: "M1" for t in ORDER}
        fixed: dict[str, np.ndarray] = {}
        applied = [[] for _ in ctxs]
        flags = [[] for _ in ctxs]
        probs: dict[str, np.ndarray] = {}
        iv: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
        gate = {"pv_kwp": self.pv_gate}
        sz = getattr(self, "sizing", None) or {}
        cover = tuple(TARGET_OF[c] for c in sz.get("coverage", ()))
        blend = float(sz.get("blend", 0.0))
        similar = None
        if blend and any(srcs[t] == "M1" for t in ("pv_kwp", "battery_kwh")):  # one neighbour query for the whole batch
            similar = self.neighbours.median_sizes(X, ("pv_kwp", "battery_kwh"))
        for t in ORDER:
            ruled = srcs[t] != "M1" and t not in locked
            if ruled:  # decided by rule / installer stats / simulator: no model call needed
                raw, p_t, lo_t, size_t, hi_t = (np.zeros(len(ctxs)) for _ in range(5))
            else:
                cc = {"battery_kwh": self.catalog.get("battery_kwh")} if sz.get("coverageCandidates") == "catalog" else None
                pred = self.model.predict(X, {**fixed, **({t: locked[t]} if t in locked else {})}, thresholds=gate, only=t,
                                          coverage=cover, cover_catalog=cc, similar=similar, blend=blend)
                raw = pred[t].to_numpy(float).copy()
                p_t, lo_t, size_t, hi_t = (pred[f"{k}_{t}"].to_numpy(float).copy() for k in ("p", "lo", "size", "hi"))
            cats = [self.catalog] * len(ctxs)
            if ruled:
                for i, row in enumerate(rows):
                    raw[i], override, p_t[i], (lo_t[i], size_t[i], hi_t[i]) = self._source_value(srcs[t], t, i, row, fixed)
                    if override is not None:
                        cats[i] = {**self.catalog, t: override}
            vals = []
            for i, ctx in enumerate(ctxs):
                current = {k: float(v[i]) for k, v in fixed.items()}
                v, a, f = rules.apply_one(t, raw[i], current, ctx, cats[i], locked=t in locked)
                vals.append(v)
                applied[i] += a
                flags[i] += f
            fixed[t] = np.array(vals)
            probs[t] = p_t
            q = (self.conformal or {}).get(t)
            if q and t not in locked:  # split-conformal widening of the p10-p90 interval (calibrated on the validation split)
                lo_t = np.minimum(np.maximum(lo_t - q, 0.0), size_t)
                hi_t = np.maximum(hi_t + q, size_t)
            if t in locked:
                size_t = lo_t = hi_t = fixed[t]
            iv[t] = (lo_t, size_t, hi_t)
        return fixed, probs, iv, applied, flags

    def design_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.design_batch_full(df)[0]

    def design_batch_full(self, df: pd.DataFrame):
        """-> (sizes per target, p_<t> / lo_<t> / hi_<t> columns)."""
        X = self._X(df)
        rows = df.to_dict("records")
        ctxs = [rules.ctx_from_row(r) for r in rows]
        fixed, probs, iv, _, _ = self._run(X, ctxs, {}, rows)
        sizes = pd.DataFrame({t: fixed[t] for t in TARGETS}, index=df.index)
        extra = pd.DataFrame({**{f"p_{t}": probs[t] for t in TARGETS}, **{f"lo_{t}": iv[t][0] for t in TARGETS},
                              **{f"hi_{t}": iv[t][2] for t in TARGETS}}, index=df.index)
        return sizes, extra

    def design(self, inputs: HomeInputs, locked: dict[str, float] | None = None, module_wp: float = 450.0) -> PolicyDesign:
        return self.design_row(row_from_inputs(inputs, module_wp), locked)

    def design_row(self, row: Mapping, locked: dict[str, float] | None = None) -> PolicyDesign:
        """`locked` maps target (pv_kwp, ...) -> planner-set size (0 = planner wants none)."""
        locked = locked or {}
        df = pd.DataFrame([dict(row)])
        X = self._X(df)
        ctx = rules.ctx_from_row(row)
        fixed, probs, iv, applied, flags = self._run(X, [ctx], locked, [dict(row)])
        values = {t: float(fixed[t][0]) for t in TARGETS}
        p = {t: float(probs[t][0]) for t in TARGETS}
        intervals = {t: tuple(float(a[0]) for a in iv[t]) for t in TARGETS}
        nb = self.neighbours.query(X)[0]
        nb_flags, _, _, _ = self._neighbour_checks(X, values, nb)
        reasons = self.explain(X, values, p, locked, applied[0], hybrid=self.hybrid_active(), nb=nb,
                               sources=self.effective_sources())
        return PolicyDesign(values, p, intervals, reasons, [hit_to_flag(h) for h in flags[0]] + nb_flags, applied[0])

    # -- validation ---------------------------------------------------------------------------------
    def _neighbour_checks(self, X: pd.DataFrame, values: Mapping[str, float], nb: pd.DataFrame | None = None):
        nb = self.neighbours.query(X)[0] if nb is None else nb
        flags: list[Flag] = []
        pct: dict[str, float | None] = {}
        share_by: dict[str, float] = {}
        for t in TARGETS:
            v, col = float(values[t]), nb[t]
            share = float(_got(col).mean())
            share_by[COMP[t]] = share
            sized = col[col > 0]
            pct[COMP[t]] = float((sized < v).mean() * 100) if v > 0 and len(sized) >= 5 else None
            c = COMP[t]
            if v > 0 and share < 0.2:
                flags.append(Flag(severity="warn", code="UNUSUAL_COMPONENT", component=c,
                                  message=f"Unusual: only {share:.0%} of similar homes got {NOUN[t]}."))
            elif v == 0 and share > 0.8:
                flags.append(Flag(severity="warn", code="UNUSUAL_OMISSION", component=c,
                                  message=f"Unusual: {share:.0%} of similar homes got {NOUN[t]}, this design has none."))
            elif v > 0 and len(sized) >= 5:
                below = float((sized < v).mean())
                if below >= 0.9:
                    flags.append(Flag(severity="warn", code="UNUSUAL_LARGE", component=c, percentile=below * 100,
                                      message=f"Unusually large {NAME[t]}: bigger than {below:.0%} of similar homes."))
                elif below <= 0.1 and float((sized > v).mean()) >= 0.9:
                    flags.append(Flag(severity="warn", code="UNUSUAL_SMALL", component=c, percentile=below * 100,
                                      message=f"Unusually small {NAME[t]}: smaller than {1 - below:.0%} of similar homes."))
        return flags, pct, share_by, len(nb)

    def validate(self, inputs: HomeInputs | Mapping, values: Mapping[str, float], module_wp: float = 450.0) -> Validation:
        """Compare a design (ours or the planner's) with hard rules and with what experts did for similar homes."""
        row = row_from_inputs(inputs, module_wp) if isinstance(inputs, HomeInputs) else dict(inputs)
        X = features(pd.DataFrame([row]), self.installers)
        rule_flags = [hit_to_flag(h) for h in rules.audit(values, rules.ctx_from_row(row), self.catalog)]
        nb_flags, pct, share, n = self._neighbour_checks(X, values)
        return Validation(rule_flags + nb_flags, pct, share, n)

    # -- explanation --------------------------------------------------------------------------------
    def explain(self, X: pd.DataFrame, values: Mapping[str, float], p: Mapping[str, float], locked: Mapping,
                applied: list[rules.Hit] | None = None, hybrid: bool = False,
                nb: pd.DataFrame | None = None, sources: Mapping[str, str] | None = None) -> list[ReasonCode]:
        """One reason per component (model/rule/lock decision + what similar homes got) plus every rule that fired.
        Physics / payback lines are deliberately absent: the hourly simulator attaches metrics (see design.attach_metrics)."""
        nb = self.neighbours.query(X)[0] if nb is None else nb
        out: list[ReasonCode] = []
        for t in ORDER:
            v, col = float(values[t]), nb[t]
            share = float(_got(col).mean())
            sized = col[col > 0]
            med = float(sized.median()) if len(sized) else 0.0
            if t in locked:
                who, kind = "set by planner", "LOCKED"
            elif sources and sources.get(t) in ("B0", "B0c", "SIM") and not (t == "wallbox_kw" and sources[t] == "B0c"):
                src = sources[t]
                if src == "SIM":
                    who, kind = ("the simulator's economic-optimum battery" if v > 0 else "simulator: no battery pays back"), "SIM_OPTIMUM"
                else:
                    who, kind = f"the installer's {'typical' if src == 'B0' else 'typical, demand-matched'} choice", "INSTALLER_USUAL"
            elif hybrid and t == "heat_pump_kw":
                who, kind = (f"rule: heat demand / {bl.HP_FULL_LOAD_HOURS:g} full-load hours", "RULE") if v > 0 else                     ("rule: no fossil heating or no known heat demand", "NO_RULE")
            elif hybrid and t == "battery_kwh":
                who, kind = ("the installer's usual battery", "INSTALLER_USUAL") if v > 0 else                     ("no PV, or this installer rarely includes one", "NONE_RULE")
            elif t == "wallbox_kw":
                ev = p[t] >= 1.0
                who, kind = ("rule: home has an EV", "EV_RULE") if ev else ("rule: no EV in the home", "NO_EV_RULE")
            else:
                who, kind = f"model {p[t]:.0%} sure to include", "MODEL_INCLUDE" if v > 0 else "MODEL_EXCLUDE"
            if v > 0:
                text = (f"{LABEL[t]} {v:g} {UNIT[t]} ({who}); {share:.0%} of {len(col)} similar homes got one, "
                        f"median {med:g} {UNIT[t]}.")
            else:
                text = f"No {NAME[t]} ({who}); {share:.0%} of {len(col)} similar homes got one."
            out.append(ReasonCode(
                code=f"{CODE[t]}_{kind}", component=COMP[t], value=round(v, 2), text=text,
                evidence={"probability": round(float(p[t]), 3), "similar_share": round(share, 3),
                          "similar_median": round(med, 2), "n_similar": int(len(col))}))
        for h in applied or []:
            out.append(ReasonCode(code=h.id, component=COMP[h.target], text=h.text,
                                  evidence={k: v for k, v in h.evidence.items() if isinstance(v, (int, float, str, bool))}))
        return out

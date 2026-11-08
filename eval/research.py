"""Pre-registered research tournament (protocol + candidates: research/experiments.md).

    pnpm x:research -- <id>[:<setting>] ... | all       e.g.  pnpm x:research -- pkg   |   pnpm x:research -- habit:90d
    pnpm x:research -- combo --fresh                    combined winner on fresh split seeds 20..39 (never used to select)
    pnpm x:research -- combo:<s> --shuffle              shuffled-label control on the 2025 Q4 fold

Rows: offers <= 2025-12-31 only (asserted; the 2026 test is never loaded into a split). Units: 4 expanding quarterly folds
(train `when` < quarter start, validate on 2025 Q1..Q4) + 20 random 80/20 splits (honesty.SPLIT_SEEDS). Reference = the
current default (config/policy.json) trained on the same rows; every gain is paired on the same validation rows.
Adopt iff mean fold gain > 0 AND mean split gain > 1 sd of the split gains AND fold EMS drop <= 1 point.
Writes aggregates only: eval/research/results/<id>__<setting>.json + one `kind: "research"` line in eval/history/runs.jsonl.
Per-row caches (default predictions, trained defaults) stay under data/processed/research_cache/ (gitignored).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run as R  # noqa: E402
import record  # noqa: E402
from honesty import SPLIT_SEEDS, shuffle_labels  # noqa: E402
from metrics import expert_match, policy_metrics  # noqa: E402
from research.lib import TARGETS, hits, predictor, row_ok  # noqa: E402

from engine import baseline as bl  # noqa: E402
from engine.policy import physics  # noqa: E402
from engine.policy.designer import CONFIG_PATH, Designer, load_config  # noqa: E402

ROOT = HERE.parent
PROCESSED = ROOT / "data" / "processed"
CACHE = PROCESSED / "research_cache"
RESULTS = HERE / "research" / "results"
PHYSICS = PROCESSED / "physics_cache.pkl"
QUARTERS = (("2025Q1", "2025-01-01", "2025-04-01"), ("2025Q2", "2025-04-01", "2025-07-01"),
            ("2025Q3", "2025-07-01", "2025-10-01"), ("2025Q4", "2025-10-01", "2026-01-01"))
FRESH_SEEDS = tuple(range(20, 40))
CANDIDATES = ("pkg", "habit", "repeat", "placeholder", "lag", "joint", "tolpv", "wbx", "recency", "blend")  # `all`; combo and haiku run by name


# ---- data / units -----------------------------------------------------------------------------------------------------
def pre_cutoff(D: pd.DataFrame) -> pd.DataFrame:
    """Offers <= 2025-12-31 only; refuses to continue if anything later slips through."""
    pre = D[D["when"] <= R.CUTOFF].reset_index(drop=True)
    assert len(pre) and pre["when"].max() <= R.CUTOFF, "research rows must be offers <= 2025-12-31"
    return pre


def units(pre: pd.DataFrame, seeds=SPLIT_SEEDS, folds: bool = True):
    """-> [(name, train, val)]: the 4 expanding quarterly folds, then one 80/20 split per seed."""
    assert pre["when"].max() <= R.CUTOFF
    out = []
    if folds:
        for name, a, b in QUARTERS:
            tr, va = pre[pre["when"] < pd.Timestamp(a)], pre[(pre["when"] >= pd.Timestamp(a)) & (pre["when"] < pd.Timestamp(b))]
            out.append((name, tr, va))
    for s in seeds:
        tr, va = train_test_split(pre, test_size=0.2, random_state=s)
        out.append((f"s{s}", tr, va))
    return out


def option_targets(O: pd.DataFrame) -> pd.DataFrame:
    """Every expert option as a target row (same encoding as features.training_frame), for the any-option match."""
    o = O.copy()
    sol = o["has_solar_tech"].fillna(False).astype(bool) if "has_solar_tech" in o else False
    return pd.DataFrame({
        "project_id": o["project_id"],
        "pv_kwp": np.where(o["has_pv"], o["kwp"], np.where(sol, np.nan, 0.0)),
        "battery_kwh": np.where(o["has_battery"], o["battery_kwh"], 0.0),
        "heat_pump_kw": np.where(o["has_heatpump"], np.where(o["hp_kw"] > 0, o["hp_kw"], np.nan), 0.0),
        "wallbox_kw": np.where(o["has_wallbox"], 11.0, 0.0)})


# ---- scoring ----------------------------------------------------------------------------------------------------------
def confidence(sizes: pd.DataFrame, extra: pd.DataFrame | None) -> np.ndarray | None:
    """Selective prediction (#41): include certainty of PV and battery x PV interval tightness (higher = surer)."""
    if extra is None or "p_pv_kwp" not in extra:
        return None
    cert = lambda p: np.abs(2 * np.nan_to_num(p.to_numpy(float), nan=0.5) - 1)  # noqa: E731
    pv = np.maximum(np.nan_to_num(sizes["pv_kwp"].to_numpy(float)), 1.0)
    width = np.nan_to_num((extra["hi_pv_kwp"] - extra["lo_pv_kwp"]).to_numpy(float), nan=10.0) / pv
    return (0.5 + 0.5 * cert(extra["p_pv_kwp"])) * (0.5 + 0.5 * cert(extra["p_battery_kwh"])) / (1 + width)


def score(sizes: pd.DataFrame, extra, val: pd.DataFrame, prim: pd.DataFrame, opts: pd.DataFrame) -> dict:
    truth = val[list(TARGETS)].astype(float)
    sizes = sizes.reindex(val.index)[list(TARGETS)].astype(float)
    ok = row_ok(sizes, truth)
    pm = policy_metrics(sizes.reset_index(drop=True), truth.reset_index(drop=True))
    assert abs(pm["wholeDesignWithinTolerance"] - ok.mean()) < 1e-9, "row_ok drifted from metrics.policy_metrics"
    ems = []
    for pid, r in zip(val["project_id"], sizes.itertuples()):
        f = lambda v: 0.0 if v != v else float(v)  # noqa: E731
        ems.append(expert_match(bl.Pred(f(r.pv_kwp), f(r.battery_kwh), f(r.wallbox_kw) > 0, f(r.heat_pump_kw)), prim.loc[pid]))
    # any-option whole design (#42)
    po = opts[opts["project_id"].isin(set(val["project_id"]))]
    pr = sizes.set_axis(val["project_id"].to_numpy()).loc[po["project_id"]]
    okany = pd.Series(row_ok(pr.reset_index(drop=True), po[list(TARGETS)].reset_index(drop=True)), index=po["project_id"].to_numpy())
    anyopt = okany.groupby(level=0).max().reindex(val["project_id"]).fillna(False).to_numpy() | ok
    out = {"n": int(len(val)), "whole": float(ok.mean()), "ems": float(np.mean(ems)), "anyOption": float(anyopt.mean()),
           "pv": float(pm["pv_kwp"]["withinTolerance"]), "battery": float(pm["battery_kwh"]["withinTolerance"]),
           "wallbox": float(pm["wallbox_kw"]["withinTolerance"])}
    c = confidence(sizes, extra)
    if c is not None:
        order = np.argsort(-c, kind="stable")
        for q in (30, 50):
            top = order[: max(1, int(round(len(order) * q / 100)))]
            out[f"selective{q}"] = float(ok[top].mean())
    return out


# ---- reference (cached) -----------------------------------------------------------------------------------------------
def policy_hash() -> str:
    return hashlib.sha256(json.dumps(load_config(), sort_keys=True).encode()).hexdigest()[:10]


class Ctx:
    """Per unit: lazily trained default Designer (disk-cached) and its predictions."""
    def __init__(self, unit: str, train: pd.DataFrame, cache: Path | None):
        self.unit, self.train, self.cache, self._dz = unit, train, cache, None

    def _key(self) -> str:
        h = hashlib.sha256(pd.util.hash_pandas_object(self.train[["project_id"]], index=False).values.tobytes()).hexdigest()[:10]
        return f"{self.unit}_{h}"

    def base(self) -> Designer:
        if self._dz is None:
            p = self.cache / f"designer_{self._key()}.joblib" if self.cache else None
            if p is not None and p.exists():
                self._dz = Designer.load(p, apply_config=False)
            else:
                self._dz = Designer.train(self.train)
                if p is not None:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    self._dz.save(p)
        return self._dz

    def base_predictor(self):
        return predictor(self.base())

    def base_out(self, val: pd.DataFrame):
        p = self.cache / f"pred_{self._key()}.pkl" if self.cache else None
        if p is not None and p.exists():
            with p.open("rb") as f:
                return pickle.load(f)
        out = self.base_predictor()(val)
        if p is not None:
            with p.open("wb") as f:
                pickle.dump(out, f)
        return out


# ---- one setting ------------------------------------------------------------------------------------------------------
def _ms(v) -> dict:
    v = np.asarray(list(v), float)
    return {"mean": float(v.mean()), "sd": float(v.std(ddof=1)) if len(v) > 1 else 0.0, "n": int(len(v))}


def decide(folds: list[dict], splits: list[dict]) -> dict:
    fg = [u["cand"]["whole"] - u["base"]["whole"] for u in folds]
    sg = [u["cand"]["whole"] - u["base"]["whole"] for u in splits]
    ems_drop = float(np.mean([u["base"]["ems"] - u["cand"]["ems"] for u in folds])) if folds else 0.0
    s = _ms(sg) if splits else {"mean": 0.0, "sd": 0.0, "n": 0}
    out = {"foldGains": fg, "foldGainMean": float(np.mean(fg)) if fg else None, "splitGain": s, "emsDropFolds": ems_drop,
           "passFold": bool(fg) and float(np.mean(fg)) > 0, "passSplit": bool(splits) and s["mean"] > s["sd"],
           "passEms": ems_drop <= 1.0}
    out["adopt"] = out["passFold"] and out["passSplit"] and out["passEms"]
    return out


def run_setting(cid: str, sname: str, setting: dict, us, prim, opts, cache: Path | None, shuffle: bool = False) -> dict:
    mod = importlib.import_module(f"research.candidates.{cid}")
    t0 = time.time()
    per = []
    if getattr(mod, "FOLDS_ONLY", False):  # e.g. the Haiku picker: pre-registered on the 4 validation folds only
        us = [u for u in us if u[0].startswith("2025Q")]
    for name, tr, va in us:
        assert tr["when"].max() <= R.CUTOFF and va["when"].max() <= R.CUTOFF
        ctx = Ctx(name, tr, cache)
        base_sizes, base_extra = ctx.base_out(va)
        trc = shuffle_labels(tr, 0) if shuffle else tr
        cctx = Ctx(name + "_shuf", trc, None) if shuffle else ctx
        sizes, extra = mod.fit(trc, setting, cctx)(va)
        u = {"unit": name, "base": score(base_sizes, base_extra, va, prim, opts), "cand": score(sizes, extra, va, prim, opts)}
        per.append(u)
        print(f"  {cid}:{sname} {name:<7} n={u['base']['n']:<4} whole {100 * u['base']['whole']:5.1f} -> {100 * u['cand']['whole']:5.1f}"
              f"  ems {u['base']['ems']:5.1f} -> {u['cand']['ems']:5.1f}  ({time.time() - t0:5.0f}s)", flush=True)
    folds = [u for u in per if u["unit"].startswith("2025Q")]
    splits = [u for u in per if not u["unit"].startswith("2025Q")]
    res = {"candidate": cid, "setting": sname, "params": setting, "kind": getattr(mod, "KIND", "?"), "policyHash": policy_hash(),
           "shuffle": shuffle, "seeds": [int(u["unit"][1:]) for u in splits], "units": per, "decision": decide(folds, splits),
           "durationSec": round(time.time() - t0, 1)}
    return res


def summary_line(res: dict) -> str:
    d = res["decision"]
    fg = " / ".join(f"{100 * g:+.1f}" for g in d["foldGains"])
    s = d["splitGain"]
    return (f"| {res['candidate']}:{res['setting']} | {fg} | {100 * (d['foldGainMean'] or 0):+.2f} | {100 * s['mean']:+.2f} ± {100 * s['sd']:.2f}"
            f" | {-d['emsDropFolds']:+.2f} | {'ADOPT' if d['adopt'] else 'no effect'} |")


def save(res: dict, fresh: bool) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = f"{res['candidate']}__{res['setting']}" + ("__fresh" if fresh else "") + ("__shuffle" if res["shuffle"] else "")
    (RESULTS / f"{tag}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    folds = [u for u in res["units"] if u["unit"].startswith("2025Q")]
    splits = [u for u in res["units"] if not u["unit"].startswith("2025Q")]
    mean = lambda us, k: {m: float(np.mean([u[k][m] for u in us])) for m in ("whole", "ems", "pv", "battery", "wallbox")}  # noqa: E731
    val = None
    if folds:
        b, c = mean(folds, "base"), mean(folds, "cand")
        conv = lambda x: {"ems": x["ems"], "wholeDesign": x["whole"], "pv": x["pv"], "battery": x["battery"], "wallbox": x["wallbox"]}  # noqa: E731
        val = {"n": int(sum(u["base"]["n"] for u in folds)), "models": {"default": conv(b), tag: conv(c)}}
    rep = None
    if splits:
        rep = {"ours": {"whole": _ms(u["cand"]["whole"] for u in splits)}, "b0": {"whole": _ms(u["base"]["whole"] for u in splits)},
               "oursMinusB0": {"whole": res["decision"]["splitGain"]}}
    rec = record.build("research", label=f"research {tag} vs default ({'adopt' if res['decision']['adopt'] else 'no effect'})",
                       duration_sec=res["durationSec"], validation=val, repeated=rep,
                       policy={"base": record.policy_summary(), "candidate": res["candidate"], "setting": res["setting"]})
    record.append(rec)


def resolve(names: list[str]) -> list[tuple[str, str, dict]]:
    out = []
    for n in names:
        for cid in (CANDIDATES if n == "all" else [n.split(":")[0]]):
            mod = importlib.import_module(f"research.candidates.{cid}")
            want = n.split(":", 1)[1] if ":" in n else None
            for s, p in mod.SETTINGS.items():
                if want in (None, s):
                    out.append((cid, s, p))
            if want and want not in mod.SETTINGS:
                raise SystemExit(f"unknown setting {n}; have {list(mod.SETTINGS)}")
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="+")
    ap.add_argument("--fresh", action="store_true", help="split seeds 20..39 (confirmation of the combined winner)")
    ap.add_argument("--shuffle", action="store_true", help="shuffled-label control on the 2025 Q4 fold")
    ap.add_argument("--no-record", action="store_true")
    a = ap.parse_args(argv)
    P, O, D = R.load(PROCESSED)
    pre = pre_cutoff(D)
    us = units(pre, FRESH_SEEDS if a.fresh else SPLIT_SEEDS)
    if a.shuffle:
        us = [u for u in us if u[0] == "2025Q4"]
    prim = O[O.is_primary].set_index("project_id")
    opts = option_targets(O)
    cache = CACHE / policy_hash()
    physics.load_cache(PHYSICS)
    try:
        for cid, s, p in resolve(a.names):
            print(f"== {cid}:{s} {p}", flush=True)
            res = run_setting(cid, s, p, us, prim, opts, cache, shuffle=a.shuffle)
            print(summary_line(res), flush=True)
            if not a.no_record:
                save(res, a.fresh)
            physics.save_cache(PHYSICS)
    finally:
        physics.save_cache(PHYSICS)


if __name__ == "__main__":
    main()

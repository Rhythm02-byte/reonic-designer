"""Run history for the Test Lab: one compact JSON line per eval run in eval/history/runs.jsonl.

Aggregates only (scores, n, git, config); never project ids, inputs or installer ids.
`append()` is called by eval/run.py at the end of every run. `python eval/record.py` re-records eval/results/latest.json.
"""
from __future__ import annotations

import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "eval" / "history" / "runs.jsonl"
CONFIG = ROOT / "services" / "engine" / "config" / "policy.json"
KEYS = ("ems", "wholeDesign", "pv", "battery", "heatPump", "wallbox", "latencyP50ms")


def _num(v):
    return round(float(v), 4) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def _clean(scores: dict | None) -> dict:
    return {k: _num((scores or {}).get(k)) for k in KEYS if _num((scores or {}).get(k)) is not None}


def _ms(mean_sd: dict | None) -> dict | None:
    return {"mean": _num(mean_sd.get("mean")), "sd": _num(mean_sd.get("sd")), "n": mean_sd.get("n")} if mean_sd else None


def git_info(root: Path = ROOT) -> dict:
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.DEVNULL, text=True).strip()
    try:
        return {"branch": git("rev-parse", "--abbrev-ref", "HEAD"), "commit": git("rev-parse", "--short", "HEAD"),
                "dirty": bool(git("status", "--porcelain", "--untracked-files=no"))}
    except (OSError, subprocess.CalledProcessError):
        return {"branch": "local", "commit": None, "dirty": False}


def policy_summary() -> dict:
    try:
        c = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return {k: c[k] for k in ("mode", "sources", "sizing", "features", "model") if k in c}


def build(kind: str, *, duration_sec: float | None = None, label: str | None = None, validation: dict | None = None,
          test: dict | None = None, repeated: dict | None = None, honesty: dict | None = None, oracle: dict | None = None,
          git: dict | None = None, policy: dict | None = None) -> dict:
    """validation/test: {"n": int, "models": {name: scores}}; repeated: honesty.repeated_splits() output;
    honesty: the honesty block of latest.json; oracle: the oracle block of latest.json."""
    rec: dict = {"id": uuid4().hex[:12], "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "kind": kind,
                 "label": label, "git": git or git_info(), "policy": policy if policy is not None else policy_summary(),
                 "durationSec": _num(duration_sec), "testScored": test is not None}
    for name, block in (("validation", validation), ("test", test)):
        if block:
            rec[name] = {"n": block.get("n"), "models": {m: _clean(s) for m, s in block["models"].items()}}
    if repeated:
        rec["repeated"] = {"ours": _ms(repeated["ours"]["whole"]), "b0": _ms(repeated["b0"]["whole"]),
                           "gap": _ms(repeated["oursMinusB0"]["whole"])}
    if honesty:
        sh, fz = honesty.get("shuffledLabels") or {}, honesty.get("fuzz") or {}
        rec["honesty"] = {"realWhole": _num((sh.get("real") or {}).get("whole")),
                          "shuffledWhole": _num(((sh.get("shuffled") or {}).get("whole") or {}).get("mean")),
                          "fuzzBroken": fz.get("broken"), "fuzzN": fz.get("n")}
        if "repeated" not in rec and honesty.get("repeatedSplits"):
            rec["repeated"] = build("x", repeated=honesty["repeatedSplits"], git={}, policy={})["repeated"]
    if oracle and oracle.get("fields"):
        rec["oracle"] = {k: {"gainWhole": _num((v.get("gain") or {}).get("wholeDesign")), "upperBound": v.get("kind") == "upperBound"}
                         for k, v in oracle["fields"].items() if k in ("demand", "ev", "heat", "roof")}
    return {k: v for k, v in rec.items() if v is not None}


def append(rec: dict, path: Path = HISTORY) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, separators=(",", ":"), allow_nan=False) + "\n")
    print(f"recorded run {rec['id']} ({rec['kind']}, {rec['git'].get('branch')}) -> {path.relative_to(ROOT)}")
    try:  # optional Slack #runs post; a no-op until tools/slack.py and a token exist
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        from slack import notify_run  # type: ignore
        notify_run(rec)
    except Exception:
        pass
    return rec


def from_latest(latest: dict) -> dict:
    """Re-record a full eval report (eval/results/latest.json)."""
    sel = latest.get("selection") or {}
    test = {"n": sel.get("nTest"), "models": {m: sel["test"][m] for m in ("B0", "B1", "composite") if m in sel.get("test", {})}} if sel else None
    t = (latest.get("splits") or {}).get("temporal")
    if t and not test:
        test = {"n": t.get("nTest"), "models": {m: _overall(v) for m, v in t["baselines"].items() if m in ("B0", "B1", "M1", "ours")}}
    if test and "composite" in test["models"]:
        test["models"]["ours"] = test["models"].pop("composite")
    return build("full", test=test, honesty=latest.get("honesty"), oracle=latest.get("oracle"), duration_sec=latest.get("durationSec"))


def _overall(v: dict) -> dict:
    o = v["overall"]
    p = o["policy"]
    return {"ems": o["expertMatchPrimary"], "wholeDesign": p["wholeDesignWithinTolerance"], "pv": p["pv_kwp"]["withinTolerance"],
            "battery": p["battery_kwh"]["withinTolerance"], "latencyP50ms": o["runtimeMs"]["p50"]}


if __name__ == "__main__":
    append(from_latest(json.loads((ROOT / "eval" / "results" / "latest.json").read_text(encoding="utf-8"))))

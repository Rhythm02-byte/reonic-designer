"""Append allowlisted, aggregate-only evaluation history. No engine imports."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
METRICS = ("ems", "wholeDesign", "pv", "battery", "heatPump", "wallbox", "latencyP50ms", "latencyP95ms")


def obj(value):
    return value if isinstance(value, dict) else {}


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def scores(value):
    value = obj(value)
    overall = obj(value.get("overall", value))
    policy = obj(overall.get("policy"))
    runtime = obj(overall.get("runtimeMs"))
    out = {key: number(value.get(key)) for key in METRICS}
    aliases = {"ems": overall.get("expertMatchPrimary"), "wholeDesign": policy.get("wholeDesignWithinTolerance"),
               "latencyP50ms": runtime.get("p50"), "latencyP95ms": runtime.get("p95")}
    for key, source in (("pv", "pv_kwp"), ("battery", "battery_kwh"), ("heatPump", "heat_pump_kw"), ("wallbox", "wallbox_kw")):
        aliases[key] = obj(policy.get(source)).get("withinTolerance")
    for key, value in aliases.items():
        if out[key] is None:
            out[key] = number(value)
    return out


def git_info(root):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.DEVNULL, text=True).strip()
    try:
        return {"branch": git("rev-parse", "--abbrev-ref", "HEAD"), "commit": git("rev-parse", "HEAD"),
                "dirty": bool(git("status", "--porcelain"))}
    except (OSError, subprocess.CalledProcessError):
        return {"branch": "local", "commit": None, "dirty": False}


def build_record(latest, policy_config=None, git=None):
    """Project only known aggregate fields; never copy report blocks wholesale."""
    latest = obj(latest)
    splits = {}
    for name, raw in obj(latest.get("splits")).items():
        # LOIO split names in this report contain installer identifiers.
        safe_name = name if name in ("temporal", "random", "random80_20", "validation") else None
        if safe_name is None:
            continue
        raw = obj(raw)
        models = {key: scores(value) for key, value in obj(raw.get("models", raw.get("baselines"))).items()
                  if key in ("B0", "B1", "B0c", "M1", "M1+", "H1", "composite")}
        splits[safe_name] = {"nTest": number(raw.get("nTest")), "models": models}
    selection = obj(latest.get("selection"))
    test = obj(selection.get("test"))
    if test:
        temporal = splits.setdefault("temporal", {"nTest": None, "models": {}})
        temporal["nTest"] = number(selection.get("nTest")) or temporal["nTest"]
        for model in ("B0", "B1", "M1", "composite"):
            if model in test:
                old = temporal["models"].get(model, {})
                # Do not borrow latency from a different model/configuration.
                temporal["models"][model] = {**scores(test[model])}
                if model in ("B0", "B1"):
                    for key in ("latencyP50ms", "latencyP95ms"):
                        temporal["models"][model][key] = old.get(key)
    chosen = obj(selection.get("chosen"))
    record = {"id": str(uuid4()), "timestamp": latest.get("generatedAt") or datetime.now(timezone.utc).isoformat(),
              "git": git or {"branch": "local", "commit": None, "dirty": False},
              "engineVersion": latest.get("engineVersion") if isinstance(latest.get("engineVersion"), str) else None,
              "policyConfig": policy_config or {}, "durationSec": number(latest.get("durationSec")), "splits": splits}
    if selection:
        record["selection"] = {"model": chosen.get("model") if chosen.get("model") in ("composite", "M1", "H1", "B0", "B1") else None,
                               "nValidation": number(selection.get("nValidation")),
                               "config": obj(chosen.get("config"))}
    fields = obj(obj(latest.get("oracle")).get("fields"))
    if fields:
        record["oracle"] = {key: {"n": number(obj(value).get("n")), "upperBound": key == "roof",
                                  **{part: scores(obj(value).get(part)) for part in ("unknown", "answered", "gain")}}
                            for key, value in fields.items() if key in ("demand", "ev", "evAssumedNo", "heat", "roof")}
    honesty = obj(latest.get("honesty"))
    if honesty:
        repeated = obj(honesty.get("repeatedSplit"))
        fuzz = obj(honesty.get("fuzz"))
        shuffled = obj(honesty.get("shuffledLabel"))
        record["honesty"] = {"shuffledLabel": {"ems": number(shuffled.get("ems")), "passed": shuffled.get("passed") if isinstance(shuffled.get("passed"), bool) else None},
                             "repeatedSplit": {key: number(repeated.get(key)) for key in ("mean", "sd", "n")},
                             "fuzz": {key: number(fuzz.get(key)) for key in ("passed", "total")}}
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latest", type=Path, default=ROOT / "eval/results/latest.json")
    parser.add_argument("--output", type=Path, default=ROOT / "eval/history/runs.jsonl")
    args = parser.parse_args()
    latest = json.loads(args.latest.read_text(encoding="utf-8-sig"))
    config = ROOT / "services/engine/config/policy.json"
    policy = json.loads(config.read_text(encoding="utf-8-sig")) if config.exists() else {}
    record = build_record(latest, policy, git_info(ROOT))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, separators=(",", ":"), allow_nan=False) + "\n")
    print(f"Recorded {record['id']} ({record['git']['branch']})")


if __name__ == "__main__":
    main()

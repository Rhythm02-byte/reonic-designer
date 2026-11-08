import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("record", Path(__file__).with_name("record.py"))
record = importlib.util.module_from_spec(spec)
spec.loader.exec_module(record)
GIT = {"branch": "next", "commit": "abc1234", "dirty": False}


def test_quick_record_keeps_only_aggregates(tmp_path):
    val = {"n": 232, "models": {"B0": {"ems": 58.1, "wholeDesign": 0.2, "pv": 0.4, "battery": 0.5, "rows": ["PRIVATE"]},
                                "ours": {"ems": float("nan"), "wholeDesign": 0.24}}}
    rep = {k: {"whole": {"mean": 0.15, "sd": 0.02, "n": 5}} for k in ("ours", "b0", "oursMinusB0")}
    rec = record.build("quick", validation=val, repeated=rep, git=GIT, policy={}, duration_sec=61.23)
    assert rec["testScored"] is False and "test" not in rec
    assert rec["validation"]["models"]["ours"] == {"wholeDesign": 0.24}  # NaN dropped
    assert rec["repeated"]["gap"]["mean"] == 0.15
    assert "PRIVATE" not in json.dumps(rec)
    out = tmp_path / "runs.jsonl"
    record.append(rec, out) if False else out.write_text(json.dumps(rec) + "\n")
    assert json.loads(out.read_text())["kind"] == "quick"


def test_test_scored_and_oracle_upper_bound():
    rec = record.build("quick", test={"n": 325, "models": {"ours": {"ems": 61.0}}}, git=GIT, policy={},
                       oracle={"fields": {"roof": {"kind": "upperBound", "gain": {"wholeDesign": 0.12}, "inputs": "PRIVATE"}}})
    assert rec["testScored"] is True
    assert rec["oracle"]["roof"] == {"gainWhole": 0.12, "upperBound": True}
    assert "PRIVATE" not in json.dumps(rec)

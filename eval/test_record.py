import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("record", Path(__file__).with_name("record.py"))
record = importlib.util.module_from_spec(spec)
spec.loader.exec_module(record)


def test_aggregate_projection_and_selected_test_scores():
    latest = json.loads('''{"projectId":"PRIVATE", "inputs":{"demand":123},
      "splits":{"temporal":{"nTest":325,"baselines":{"B0":{"overall":{
      "expertMatchPrimary":61.1,"runtimeMs":{"p50":1,"p95":401},
      "policy":{"wholeDesignWithinTolerance":0.206}}},"M1":{"overall":{"expertMatchPrimary":50}}}}},
      "selection":{"nTest":325,"chosen":{"model":"composite"},"test":{"composite":{"ems":60.4,"pv":0.597,"rows":["PRIVATE"]}}},
      "oracle":{"fields":{"roof":{"n":325,"gain":{"wholeDesign":0.12},"inputs":"PRIVATE"}}}}''')
    result = record.build_record(latest)
    models = result["splits"]["temporal"]["models"]
    assert models["composite"]["ems"] == 60.4
    assert models["composite"]["latencyP50ms"] is None
    assert models["B0"]["latencyP95ms"] == 401
    assert result["oracle"]["roof"]["upperBound"] is True
    assert "PRIVATE" not in json.dumps(result)
    assert result["durationSec"] is None


def test_missing_blocks_and_nonfinite_values():
    assert record.build_record({})["splits"] == {}
    assert record.scores({"ems": float("nan"), "pv": True})["ems"] is None
    assert record.scores({"pv": True})["pv"] is None
    json.dumps(record.build_record({}), allow_nan=False)

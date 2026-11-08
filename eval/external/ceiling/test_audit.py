import importlib.util
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("ceiling_audit", Path(__file__).with_name("audit.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_oracle_finds_overlap_between_observed_predictions():
    # Neither observed PV size matches the other, but 1.12 matches both.
    assert audit.maximum_tolerance_overlap([[1, 2, 0, 0], [1.4, 2, 0, 0]]) == 2


def test_incompatible_inclusion_and_unknown_size():
    assert audit.maximum_tolerance_overlap([[0, 0, 0, 0], [np.nan, 0, 0, 0]]) == 1
    assert audit.maximum_tolerance_overlap([[np.nan, 0, 0, 0], [12, 0, 0, 0]]) == 2


def test_joint_oracle_does_not_multiply_marginal_maxima():
    assert audit.maximum_tolerance_overlap([[1, 1, 0, 0], [1, 10, 0, 0], [10, 1, 0, 0]]) == 1


def test_module_tolerance_keeps_presence_gate():
    assert not audit.whole_hits([[0, 0, 0, 0]], [[0.2, 0, 0, 0]], "relative_or_one_module")[0]
    assert audit.whole_hits([[1.4, 0, 0, 11]], [[1, 0, 0, 22]], "relative_or_one_module")[0]

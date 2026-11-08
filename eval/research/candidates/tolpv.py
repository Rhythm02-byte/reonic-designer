"""Tolerance-mode PV (idea 3): size PV like the battery already is, at the value within tolerance of the most predicted
expert sizes (sizing.coverage), instead of the median regressor. Pure config override of the default."""
from __future__ import annotations

from research.lib import predictor, train_designer

KIND = "config"
SETTINGS = {"cov_samples": {"sizing": {"coverage": ["pv", "battery"]}},
            "cov_catalog": {"sizing": {"coverage": ["pv", "battery"], "coverageCandidates": "catalog"}}}


def fit(train, setting, ctx):
    return predictor(train_designer(train, config=setting))

"""Recency weighting (idea 20): every boosted tree of the chain is fitted with sample weight
0.5 ** (age / half-life), age measured from the newest training offer. Default config otherwise."""
from __future__ import annotations

from research.lib import predictor, train_designer

KIND = "model"
SETTINGS = {"6m": {"half_life_days": 182.6}, "12m": {"half_life_days": 365.25}}


def weights(train, half_life_days):
    age = (train["when"].max() - train["when"]).dt.total_seconds() / 86400.0
    return 0.5 ** (age / half_life_days)


def fit(train, setting, ctx):
    return predictor(train_designer(train, weights=weights(train, setting["half_life_days"])))

"""kNN + GBM blend (idea 21): PV and battery size = (1 - w) * model + w * median of the 25 most similar past homes
(the existing sizing.blend option; default sizing otherwise unchanged)."""
from __future__ import annotations

from research.lib import load_config, predictor, train_designer

KIND = "config"
SETTINGS = {"w0.3": {"blend": 0.3}, "w0.5": {"blend": 0.5}}


def fit(train, setting, ctx):
    sizing = {**(load_config().get("sizing") or {}), **setting}
    return predictor(train_designer(train, config={"sizing": sizing}))

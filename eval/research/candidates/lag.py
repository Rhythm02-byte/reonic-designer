"""Request -> offer lag in days (idea 12; NaN when either date is missing). Caveat: in the product the draft is made at
request time, so this feature is not available there; it is tested as a diagnostic of 'template packages'."""
from __future__ import annotations

import pandas as pd

from research.lib import predictor, train_designer

KIND = "feature"
SETTINGS = {"days": {}}


def lag_days(df):
    lag = (pd.to_datetime(df["offer_at"]) - pd.to_datetime(df["request_at"])).dt.total_seconds() / 86400.0
    return pd.DataFrame({"lag_days": lag.where(lag >= 0)}, index=df.index)


def fit(train, setting, ctx):
    return predictor(train_designer(train, extra=lag_days), extra=lag_days)

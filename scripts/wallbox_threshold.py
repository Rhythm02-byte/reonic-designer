"""Wallbox: 5-fold cross-validation on the training split, input features only, against the "has an EV" rule.

    python scripts/wallbox_threshold.py

- Training split only: the same random 80/20 split as `reonic eval` (seed 0). The 20% test split is not touched.
- The classifier sees raw inputs only. No upstream predicted sizes (PV, battery, heat pump) and no
  features derived from them. Columns that are entirely empty in the export are dropped and listed.
- Baselines: include a wallbox if the home has an EV (baseline.py), and never include one (majority-class reference).
- Metrics per fold and as mean ± standard deviation: accuracy, precision, recall, F1, ROC AUC. The model
  uses the default 0.5 cut-off, so no threshold is tuned here.

Writes reports/wallbox_cv.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

from reonic import data, evaluate
from reonic.schema import INPUT_FIELDS, TARGETS

SEED = 0
# Raw input fields only. Derived features (ev_kwh, future_demand_kwh, ...) and predicted sizes are excluded on purpose.
RAW_FEATURES = [
    "annual_consumption_kwh", "electricity_price_eur_kwh", "energy_price_increase", "ev_km_per_year",
    "heating_demand_kwh", "existing_pv_kwp", "existing_battery_kwh", "has_ev", "has_flexible_tariff",
    "has_existing_wallbox",
]
PROFILE_COLS = ["profile_H0", "profile_FamilyOfFour", "profile_SeniorOnePerson", "profile_PartTimeOnePerson",
                "profile_HomeOfficeOnePerson", "profile_CustomFromEditor"]
TARGET_LIKE = {"pv_kwp", "battery_kwh", "heat_pump_kw", "wallbox_kw", "ev_kwh", "future_demand_kwh",
               "heat_demand_kwh", "pv_kwp_for_full_demand"}


def canonical(df: pd.DataFrame) -> pd.DataFrame:
    for c in INPUT_FIELDS:
        if c not in df.columns:
            df[c] = np.nan
    df[list(TARGETS)] = df[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    return df


def raw_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Raw input columns only, with one-hot load profile. Columns that are entirely empty are dropped."""
    X = pd.DataFrame(index=df.index)
    for c in RAW_FEATURES:
        X[c] = pd.to_numeric(df[c], errors="coerce") if c not in ("has_ev", "has_flexible_tariff", "has_existing_wallbox") \
            else df[c].map(lambda v: np.nan if pd.isna(v) else float(bool(v) if not isinstance(v, str) else v.lower() in {"1", "true", "yes"}))
    profile = df["load_profile"].astype("string")
    for lp in ["H0", "FamilyOfFour", "SeniorOnePerson", "PartTimeOnePerson", "HomeOfficeOnePerson", "CustomFromEditor"]:
        X[f"profile_{lp}"] = (profile == lp).astype(float).where(profile.notna())
    leaked = set(X.columns) & TARGET_LIKE
    assert not leaked, f"target-derived columns in wallbox features: {leaked}"
    empty = [c for c in X.columns if X[c].notna().sum() == 0]
    return X.drop(columns=empty), empty


full = canonical(data.load_raw("data/raw"))
train, _ = evaluate.split(full, 0.2, SEED, None)  # test split is not used here
X, dropped = raw_matrix(train)
y = (train["wallbox_kw"].to_numpy() > 0).astype(int)
ev = train["has_ev"].map(lambda v: False if pd.isna(v) else bool(v) if not isinstance(v, str) else v.lower() in {"1", "true", "yes"}).to_numpy().astype(int)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
rows = []
for fold, (tr, va) in enumerate(skf.split(X, y), 1):
    clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, random_state=SEED).fit(X.iloc[tr], y[tr])
    p = clf.predict_proba(X.iloc[va])[:, 1]
    pred = (p >= 0.5).astype(int)
    yv, ev_v = y[va], ev[va]
    rows.append({
        "fold": fold, "n_val": int(len(va)),
        "model_accuracy": accuracy_score(yv, pred), "model_precision": precision_score(yv, pred, zero_division=0),
        "model_recall": recall_score(yv, pred, zero_division=0), "model_f1": f1_score(yv, pred, zero_division=0),
        "model_auc": roc_auc_score(yv, p),
        "ev_rule_accuracy": accuracy_score(yv, ev_v), "ev_rule_precision": precision_score(yv, ev_v, zero_division=0),
        "ev_rule_recall": recall_score(yv, ev_v, zero_division=0), "ev_rule_f1": f1_score(yv, ev_v, zero_division=0),
        "ev_rule_auc": roc_auc_score(yv, ev_v),
        "never_rule_accuracy": accuracy_score(yv, np.zeros_like(yv)),  # always "no wallbox"
    })

cv = pd.DataFrame(rows)
keys = [c for c in cv.columns if c not in ("fold", "n_val")]
summary = pd.DataFrame({"mean": cv[keys].mean(), "sd": cv[keys].std()})

print(f"train rows: {len(train)}  wallbox share: {y.mean():.3f}  features: {X.shape[1]}")
print(f"dropped (entirely empty in the export): {dropped}")
print(f"features used: {list(X.columns)}")
print()
print(cv.round(3).to_string(index=False))
print()
print("5-fold CV, mean and standard deviation:")
print(summary.round(3).to_string())
print()
print("never-include rule accuracy:", f"{summary.loc['never_rule_accuracy', 'mean']:.3f}")
print("model vs EV rule (accuracy):",
      f"{summary.loc['model_accuracy', 'mean']:.3f} ± {summary.loc['model_accuracy', 'sd']:.3f}",
      "vs", f"{summary.loc['ev_rule_accuracy', 'mean']:.3f} ± {summary.loc['ev_rule_accuracy', 'sd']:.3f}")

Path("reports").mkdir(exist_ok=True)
Path("reports/wallbox_cv.json").write_text(json.dumps({
    "features": list(X.columns), "dropped_empty": dropped, "n_train": int(len(train)),
    "folds": rows, "summary": {k: {"mean": float(summary.loc[k, "mean"]), "sd": float(summary.loc[k, "sd"])} for k in keys},
}, indent=2, default=float))

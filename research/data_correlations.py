"""Aggregate-only correlation report. Reads data/processed (ETL output), writes research/data-correlations.md.

    services/engine/.venv/Scripts/python research/data_correlations.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.tree import DecisionTreeClassifier, export_text

ROOT = Path(__file__).resolve().parents[1]
P = pd.read_parquet(ROOT / "data/processed/projects.parquet")
O = pd.read_parquet(ROOT / "data/processed/options.parquet")
J = O[O.is_primary].merge(P, on=["project_id", "installer_id"])
INTERPRETATION = (ROOT / "research/data-correlations.interpretation.txt")


def md(df: pd.DataFrame, floatfmt="{:.2f}") -> str:
    df = df.reset_index()
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    rows = ["| " + " | ".join(floatfmt.format(v) if isinstance(v, (float, np.floating)) and not pd.isna(v) else ("" if pd.isna(v) else str(v))
                              for v in r) + " |" for r in df.itertuples(index=False)]
    return head + "\n".join(rows) + "\n"


# ---- feature frame (inputs the planner knows; roof is the one optional "mined" input)
F = pd.DataFrame(index=J.index)
F["demand_kwh"] = J.demand_kwh
F["demand_is_default"] = J.demand_is_default.astype(float)
F["price_eur_kwh"] = J.price_eur_kwh
F["price_escalation"] = J.price_escalation
F["has_ev"] = J.has_ev.astype(float)
F["ev_km"] = J.ev_km.fillna(0)
for t in ("Gas", "Oil", "Heatpump"):
    F[f"heating_{t}"] = (J.heating_type == t).astype(float)
F["hp_elec_existing_kwh"] = J.hp_elec_existing_kwh.fillna(0)
F["load_family"] = J.load_family.map({"H0": 0, "family": 1, "senior": 2, "home_office": 3, "custom": 4, "other": 5}).astype(float)
for r, keys in (("concrete_tile", ["concrete_tile"]), ("clay_tile", ["clay_tile"]), ("flat", ["flat", "flat_ew"]), ("metal", ["metal", "trapezoid", "standing_seam"])):
    F[f"roof_{r}"] = np.where(J.roof_type == "unknown", np.nan, J.roof_type.isin(keys).astype(float))
F["has_existing_pv"] = J.has_existing_pv.astype(float)
F["installer_2a8ba8e2"] = (J.installer_id == "2a8ba8e2").astype(float)

T = pd.DataFrame({"kwp": J.kwp.where(J.has_pv), "battery_kwh": J.battery_kwh, "has_battery": J.has_battery.astype(float),
                  "has_wallbox": J.has_wallbox.astype(float), "hp_kw": J.hp_kw, "has_pv": J.has_pv.astype(float)})

out = ["# Data correlations (aggregates only)\n",
       f"Source: `data/processed` (ETL output). Unit of analysis: the **primary option** (lowest option_number) of each project with parts, n = {len(J)} "
       f"({', '.join(f'{k}: {v}' for k, v in J.installer_id.value_counts().items())}). Spearman rank correlations, pairwise-complete. "
       "`kwp` is over options that contain PV. `roof_*` is mined from the parts list (planner-known at design time, otherwise leakage); NaN when unparseable.\n"]

# 1) Spearman
S = pd.concat([F, T], axis=1).corr(method="spearman").loc[F.columns, T.columns]
out += ["## 1. Spearman: inputs vs outputs (all installers)\n", md(S, "{:+.2f}")]
for inst, g in J.groupby("installer_id"):
    Si = pd.concat([F.loc[g.index].drop(columns="installer_2a8ba8e2"), T.loc[g.index]], axis=1).corr(method="spearman")
    Si = Si.loc[[c for c in F.columns if c != "installer_2a8ba8e2"], T.columns]
    out += [f"### Installer {inst} (n={len(g)})\n", md(Si, "{:+.2f}")]

# 2) battery / kWp ratio by segment
R = J[J.has_pv & J.has_battery].copy()
R["ratio"] = R.battery_kwh / R.kwp
R["demand_bucket"] = pd.cut(R.demand_kwh, [0, 3500, 5000, 7000, 1e9], labels=["<3.5k", "3.5-5k", "5-7k", ">7k"])
seg = []
for name, col in (("installer", "installer_id"), ("has_ev", "has_ev"), ("heating", "heating_type"), ("demand_bucket", "demand_bucket"),
                  ("existing_pv", "has_existing_pv")):
    g = R.groupby(col, observed=True).ratio.agg(n="size", p25=lambda x: x.quantile(.25), median="median", p75=lambda x: x.quantile(.75))
    g.index = [f"{name}={i}" for i in g.index]
    seg.append(g[g.n >= 5])
out += ["## 2. Battery kWh per kWp by segment (options with PV and battery)\n", md(pd.concat(seg)), ]

# 3) kWp by demand bucket per installer
K = J[J.has_pv].copy()
K["demand_bucket"] = pd.cut(K.demand_kwh, [0, 2500, 3500, 4500.5, 5500, 7000, 10000, 1e9],
                            labels=["<2.5k", "2.5-3.5k", "3.5-4.5k(def=4.5k)", "4.5-5.5k", "5.5-7k", "7-10k", ">10k"])
t = K.groupby(["installer_id", "demand_bucket"], observed=True).kwp.agg(n="size", p25=lambda x: x.quantile(.25), median="median", p75=lambda x: x.quantile(.75))
out += ["## 3. kWp by demand bucket per installer (PV options)\n", md(t)]
dflt = K.groupby(["installer_id", "demand_is_default"]).kwp.agg(n="size", median="median")
out += ["kWp for default-like demand (exactly 4,500 kWh) vs other:\n", md(dflt)]

# 4) shallow trees
X = F.fillna(-1)
def tree(y, title, names=None):
    m = y.notna()
    clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=20, random_state=0).fit(X[m], y[m].astype(int))
    acc = clf.score(X[m], y[m].astype(int)); base = y[m].astype(int).value_counts(normalize=True).max()
    return f"### {title}\nTrain accuracy {acc:.2f} vs majority-class {base:.2f} (n={int(m.sum())}).\n\n```\n" + export_text(clf, feature_names=list(X.columns), class_names=names) + "```\n"
kb = pd.qcut(T.kwp, 3, labels=False, duplicates="drop")
q = T.kwp.quantile([1 / 3, 2 / 3]).round(1).tolist()
out += ["## 4. Depth-3 decision-tree rules (min leaf 20; descriptive, not a validated model)\n",
        tree(T.has_battery, "has_battery", ["no", "yes"]),
        tree(kb, f"kWp tercile (0: <= {q[0]}, 1: <= {q[1]}, 2: above)", [f"<={q[0]}", f"<={q[1]}", f">{q[1]}"]),
        tree(T.has_wallbox, "has_wallbox", ["no", "yes"])]

# 5) mutual information
mi = {}
Xm = X.values
for tname, y, fn in (("kwp", T.kwp, mutual_info_regression), ("battery_kwh", T.battery_kwh, mutual_info_regression),
                     ("has_battery", T.has_battery, mutual_info_classif), ("has_wallbox", T.has_wallbox, mutual_info_classif)):
    m = y.notna().values
    mi[tname] = pd.Series(fn(Xm[m], y[m].values, random_state=0), index=X.columns)
MI = pd.DataFrame(mi)
MI["rank_sum"] = MI.rank(ascending=False).sum(axis=1)
out += ["## 5. Mutual information (nats; higher = more informative, no linearity assumed; sorted by combined rank)\n",
        md(MI.sort_values("rank_sum").drop(columns="rank_sum"), "{:.3f}")]

if INTERPRETATION.exists():
    out += ["## 6. Interpretation\n", INTERPRETATION.read_text(encoding="utf-8"), "\n"]
(ROOT / "research/data-correlations.md").write_text("\n".join(out), encoding="utf-8")
print("wrote research/data-correlations.md", file=sys.stderr)

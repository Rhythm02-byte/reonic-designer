"""Three checks that our headline score is not inflated.

    python scripts/leakage_checks.py

1a. Customer-grouped split. 42 customers have 2+ projects (85 projects). In a random split the same customer can sit
    in both train and test, and a customer's projects may be near-copies. Grouping by customer removes that.
1b. Shuffled labels. Train on targets permuted across homes (inputs unchanged), score against the true targets.
    This is a "model with no information" reference. If it scored near the real model, the score would be an artefact.
1c. Time split. Within each installer, train on the earliest 80% of offers and test on the latest 20%.

Same metric as evaluate.py. Real export only. Writes reports/leakage_checks.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split

from reonic import data, evaluate
from reonic.baseline import rule_of_thumb
from reonic.engine import Designer
from reonic.schema import INPUT_FIELDS, TARGETS

SEEDS_GROUP = range(10)
SEEDS_SHUFFLE = range(5)


def canonical(df: pd.DataFrame) -> pd.DataFrame:
    for c in INPUT_FIELDS:
        if c not in df.columns:
            df[c] = np.nan
    df[list(TARGETS)] = df[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    return df


def score(designer: Designer, test: pd.DataFrame) -> dict:
    t = test.reset_index(drop=True)
    m = evaluate.metrics(designer.design_batch(t), t)
    b = evaluate.metrics(rule_of_thumb(t), t)
    return {"whole": m["whole_design_within_tolerance"], "pv": m["pv_kwp"]["within_tolerance"],
            "battery": m["battery_kwh"]["within_tolerance"], "baseline_whole": b["whole_design_within_tolerance"]}


def summarise(rows: list[dict]) -> dict:
    df = pd.DataFrame(rows)
    return {k: {"mean": float(df[k].mean()), "sd": float(df[k].std(ddof=1)) if len(df) > 1 else 0.0} for k in df.columns}


full = canonical(data.load_raw("data/raw"))
cust = pd.concat([pd.read_csv(f"data/raw/{d.name}/projects_status_quo.csv")[["project_id", "customer_contact_id"]]
                  for d in sorted(Path("data/raw").iterdir()) if (d / "projects_status_quo.csv").exists()])
assert not cust.project_id.duplicated().any(), "project ids are not unique across folders"
full = full.merge(cust, on="project_id", how="left").reset_index(drop=True)
report: dict = {"n_projects": int(len(full))}

# ---- 1a. customer-grouped vs random split, same seeds ----------------------------------------------
repeat = full["customer_contact_id"].map(full["customer_contact_id"].value_counts()) > 1
report["customers"] = {"distinct": int(full.customer_contact_id.nunique()), "with_2plus_projects": int(full.customer_contact_id.map(full.customer_contact_id.value_counts()).gt(1).groupby(full.customer_contact_id).first().sum()),
                       "projects_of_repeat_customers": int(repeat.sum())}

# Mechanism: are a repeat customer's projects near-copies of each other?
rng = np.random.default_rng(0)
same_cust, random_pairs = [], []
for _, g in full[repeat].groupby("customer_contact_id"):
    idx = g.index.to_list()
    for i in range(len(idx)):
        for j in range(i + 1, len(idx)):
            a, b = full.loc[idx[i]], full.loc[idx[j]]
            same_cust.append(bool(a.battery_kwh == b.battery_kwh and a.installer_id == b.installer_id))
for _ in range(len(same_cust) * 20):
    ia, ib = rng.choice(len(full), 2, replace=False)
    a, b = full.loc[ia], full.loc[ib]
    if a.installer_id == b.installer_id:
        random_pairs.append(bool(a.battery_kwh == b.battery_kwh))
report["same_customer_pairs_with_identical_battery"] = {"n_pairs": len(same_cust), "share": float(np.mean(same_cust)),
                                                         "random_pairs_same_installer_share": float(np.mean(random_pairs))}

rand_rows, group_rows, exposure = [], [], []
for seed in SEEDS_GROUP:
    tr, te = train_test_split(full, test_size=0.2, random_state=seed)
    exposure.append(float(te.customer_contact_id.isin(set(tr.customer_contact_id)).mean()))
    d = Designer.train(tr)
    rand_rows.append(score(d, te))
    tr_i, te_i = next(GroupShuffleSplit(1, test_size=0.2, random_state=seed).split(full, groups=full.customer_contact_id))
    d = Designer.train(full.iloc[tr_i])
    group_rows.append(score(d, full.iloc[te_i]))
rand_s, group_s = summarise(rand_rows), summarise(group_rows)
report["1a_customer_grouped"] = {"random_split": rand_s, "customer_grouped_split": group_s,
                                 "share_of_test_projects_whose_customer_is_also_in_train_under_random_split": float(np.mean(exposure)),
                                 "paired_difference_whole_design": float(np.mean([g["whole"] - r["whole"] for g, r in zip(group_rows, rand_rows)]))}

# ---- 1b. shuffled labels ---------------------------------------------------------------------------
real_rows, shuf_rows = [], []
for seed in SEEDS_SHUFFLE:
    tr, te = train_test_split(full, test_size=0.2, random_state=seed)
    real_rows.append(score(Designer.train(tr), te))
    shuffled = tr.copy()
    perm = np.random.default_rng(seed).permutation(len(tr))
    shuffled[list(TARGETS)] = tr[list(TARGETS)].to_numpy()[perm]  # one permutation for all targets, designs stay coherent
    shuf_rows.append(score(Designer.train(shuffled), te))
report["1b_shuffled_labels"] = {"real_labels": summarise(real_rows), "shuffled_labels": summarise(shuf_rows)}

# ---- 1c. time split inside each installer ----------------------------------------------------------
dated = full[full["offer_created_at"].notna()].copy()
parts_tr, parts_te, spans = [], [], {}
for inst, g in dated.groupby("installer_id"):
    g = g.sort_values("offer_created_at")
    cut = int(len(g) * 0.8)
    parts_tr.append(g.iloc[:cut])
    parts_te.append(g.iloc[cut:])
    spans[inst] = {"train_until": str(g.iloc[cut - 1]["offer_created_at"].date()), "test_from": str(g.iloc[cut]["offer_created_at"].date()),
                   "n_train": cut, "n_test": int(len(g) - cut)}
tr_t, te_t = pd.concat(parts_tr), pd.concat(parts_te)
time_s = score(Designer.train(tr_t), te_t)
ref_rows = []  # random splits of the same rows, same sizes, for a like-for-like reference
for seed in range(5):
    tr, te = train_test_split(dated, test_size=len(te_t), random_state=seed)
    ref_rows.append(score(Designer.train(tr), te))
report["1c_time_split"] = {"dropped_without_offer_date": int(len(full) - len(dated)), "by_installer": spans, "time_split": time_s,
                           "random_split_same_rows_mean_of_5": summarise(ref_rows)}

Path("reports").mkdir(exist_ok=True)
Path("reports/leakage_checks.json").write_text(json.dumps(report, indent=2, default=float))

pct = lambda x: f"{x:6.1%}"
print(f"projects: {report['n_projects']}")
print("\n1a. Customers:", report["customers"])
m = report["same_customer_pairs_with_identical_battery"]
print(f"    pairs of projects from the same customer with an identical battery size: {m['share']:.0%} (n={m['n_pairs']} pairs) vs {m['random_pairs_same_installer_share']:.0%} for random pairs at the same installer")
print(f"    under a random split, {report['1a_customer_grouped']['share_of_test_projects_whose_customer_is_also_in_train_under_random_split']:.1%} of test projects have their customer in train")
print(f"    {'':26}{'whole design':>14}{'PV':>9}{'battery':>9}{'baseline':>10}   (mean over {len(list(SEEDS_GROUP))} seeds)")
for name, s in (("random split", rand_s), ("customer-grouped split", group_s)):
    print(f"    {name:26}{pct(s['whole']['mean']):>14}{pct(s['pv']['mean']):>9}{pct(s['battery']['mean']):>9}{pct(s['baseline_whole']['mean']):>10}")
print(f"    paired difference in whole design (grouped - random): {report['1a_customer_grouped']['paired_difference_whole_design']:+.3f}")
print("\n1b. Shuffled labels (mean over 5 seeds):")
for name, s in (("real labels", summarise(real_rows)), ("shuffled labels", summarise(shuf_rows))):
    print(f"    {name:26}{pct(s['whole']['mean']):>14}{pct(s['pv']['mean']):>9}{pct(s['battery']['mean']):>9}{pct(s['baseline_whole']['mean']):>10}")
print("\n1c. Time split (earliest 80% of each installer's offers train, latest 20% test):")
for inst, v in spans.items():
    print(f"    {inst}: train to {v['train_until']} (n={v['n_train']}), test from {v['test_from']} (n={v['n_test']})")
r = summarise(ref_rows)
print(f"    {'time split':26}{pct(time_s['whole']):>14}{pct(time_s['pv']):>9}{pct(time_s['battery']):>9}{pct(time_s['baseline_whole']):>10}")
print(f"    {'random, same rows':26}{pct(r['whole']['mean']):>14}{pct(r['pv']['mean']):>9}{pct(r['battery']['mean']):>9}{pct(r['baseline_whole']['mean']):>10}")

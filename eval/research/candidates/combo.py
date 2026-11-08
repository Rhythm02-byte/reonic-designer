"""Combined winner (pre-registered 05:15 after the single-idea results, BEFORE running; see research/experiments.md).
Stacks the settings that passed: a sizing config (tolpv / joint), and repeat-customer `copy` on top.
`C_bat_catalog` is a declared post-hoc ablation: the component breakdown showed the tolpv/joint gains come from the
battery (catalog candidates), while PV got worse; it keeps only that part. Confirmed on fresh seeds 20..39."""
from __future__ import annotations

from research.candidates import joint, repeat
from research.lib import TARGETS, predictor, train_designer

KIND = "combo"
SETTINGS = {
    "C_bat_catalog": {"config": {"sizing": {"coverage": ["battery"], "coverageCandidates": "catalog"}}, "joint": False},
    "A_tolpv_catalog": {"config": {"sizing": {"coverage": ["pv", "battery"], "coverageCandidates": "catalog"}}, "joint": False},
    "B_joint": {"config": None, "joint": True},
}


def fit(train, setting, ctx):
    base = joint.fit(train, {"gate": False}, ctx) if setting["joint"] else predictor(train_designer(train, config=setting["config"]))
    fn = repeat.earlier_design(train)

    def predict(test):
        sizes, extra = base(test)
        E = fn(test)
        sizes = sizes.copy()
        for t, c in zip(TARGETS, repeat.COLS[1:]):
            use = (E["rep_flag"] == 1) & E[c].notna()
            sizes.loc[use, t] = E.loc[use, c]
        return sizes, extra
    return predict

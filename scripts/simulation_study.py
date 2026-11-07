"""Four experiments on simulated data. Writes reports/simulation_study.json (kept apart from eval.json).

    python scripts/simulation_study.py

Read the header of src/reonic/simulate.py first: simulated designs follow OUR policy, not the experts'.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from reonic import data, evaluate, simulate
from reonic.engine import Designer
from reonic.schema import TARGETS

REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)
real = data.load("data/projects.csv")
out: dict = {"disclaimer": "Simulated designs follow a policy written by the team, not installer behaviour."}


def score(designer, test: pd.DataFrame) -> dict:
    pred = designer.design_batch(test)
    m = evaluate.metrics(pred, test)
    return {"whole_design": m["whole_design_within_tolerance"],
            **{t: m[t]["within_tolerance"] for t in TARGETS},
            **{f"{t}_include_acc": m[t]["include_accuracy"] for t in TARGETS}}


# A. Recovery: can the pipeline learn a rule we know? (ceiling check)
train = simulate.simulate(real, n=4000, seed=1, hp_share=0.3)
test = simulate.simulate(real, n=1000, seed=2, hp_share=0.3)
designer = Designer.train(train)
out["A_recovery_hp30"] = score(designer, test)

# B. Gaps: same model, inputs blanked at increasing rates
out["B_missing_inputs"] = {f"{int(r*100)}%": score(designer, simulate.mask_inputs(test, r, seed=3))
                           for r in (0.0, 0.25, 0.5, 0.75)}

# C. Heat pumps: does sizing become learnable when the data has examples?
no_hp = Designer.train(simulate.simulate(real, n=4000, seed=1, hp_share=0.0))
hp_test = simulate.simulate(real, n=1000, seed=2, hp_share=0.3)
out["C_heat_pump"] = {
    "trained_hp0": score(no_hp, hp_test)["heat_pump_kw"],
    "trained_hp30": score(designer, hp_test)["heat_pump_kw"],
}

# D. Transfer: train on simulation, test on the real export. Expected to be poor: the gap is the policy.
d_real = evaluate.metrics(designer.design_batch(real), real)
out["D_sim_to_real"] = {"whole_design": d_real["whole_design_within_tolerance"],
                        **{t: d_real[t]["within_tolerance"] for t in TARGETS}}

(REPORTS / "simulation_study.json").write_text(json.dumps(out, indent=2, default=float))
print(json.dumps(out, indent=2, default=float))

"""Train the served policy and save it where the API picks it up.

By default it learns from offers up to the eval cutoff (2025-12-31), the same rows as the holdout service, so a held-out
2026 project loaded into the planner is designed by a model that never saw it. `--all` trains on every offer (production).

    pnpm x:train        (or: python -m engine.policy.train [--all] [--data data/processed] [--out services/engine/models/designer.joblib])
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from engine.demo import HOLDOUT_CUTOFF
from engine.design import DEFAULT_DATA_DIR, DEFAULT_MODEL_PATH
from engine.policy.designer import Designer
from engine.policy.features import training_frame


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=DEFAULT_DATA_DIR, type=Path)
    ap.add_argument("--out", default=DEFAULT_MODEL_PATH, type=Path)
    ap.add_argument("--all", action="store_true", help="train on every offer, including the 2026 holdout (not for the demo)")
    a = ap.parse_args()
    df = training_frame(pd.read_parquet(a.data / "projects.parquet"), pd.read_parquet(a.data / "options.parquet"))
    if not a.all:
        df = df[df["when"] <= HOLDOUT_CUTOFF].reset_index(drop=True)
    t = time.perf_counter()
    d = Designer.train(df)
    d.save(a.out)
    scope = "all offers" if a.all else f"offers <= {HOLDOUT_CUTOFF.date()}"
    print(f"trained on {len(df)} projects, {scope} ({', '.join(d.installers)}) in {time.perf_counter() - t:.1f}s -> {a.out}")


if __name__ == "__main__":
    main()

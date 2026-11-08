"""Train the policy on ALL processed data and save it where the API picks it up.

    pnpm x:train        (or: python -m engine.policy.train [--data data/processed] [--out services/engine/models/designer.joblib])
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from engine.design import DEFAULT_DATA_DIR, DEFAULT_MODEL_PATH
from engine.policy.designer import Designer
from engine.policy.features import training_frame


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=DEFAULT_DATA_DIR, type=Path)
    ap.add_argument("--out", default=DEFAULT_MODEL_PATH, type=Path)
    a = ap.parse_args()
    df = training_frame(pd.read_parquet(a.data / "projects.parquet"), pd.read_parquet(a.data / "options.parquet"))
    t = time.perf_counter()
    d = Designer.train(df)
    d.save(a.out)
    print(f"trained on {len(df)} projects ({', '.join(d.installers)}) in {time.perf_counter() - t:.1f}s -> {a.out}")


if __name__ == "__main__":
    main()

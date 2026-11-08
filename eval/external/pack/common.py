from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/external"
RAW = DATA / "raw"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def quantiles(values) -> dict:
    import numpy as np
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    return {"n": len(a), **{f"p{p}": float(np.quantile(a, p / 100, method="linear")) if len(a) else None
                            for p in (5, 25, 50, 75, 95)}}

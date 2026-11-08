"""Load compact public calibrated profiles, without network or engine mutation."""
from pathlib import Path
import json
import numpy as np

PROFILE_DIR = Path(__file__).resolve().parents[2] / "data/external/profiles"


def normalized(values):
    a = np.asarray(values, dtype=float)
    if a.shape != (8760,) or not np.isfinite(a).all() or (a < 0).any() or a.sum() <= 0:
        raise ValueError("Profile must be 8760 finite nonnegative hourly values with positive energy")
    return a / a.sum()


def load_profiles(annual_kwh=1.0, path=None):
    if not np.isfinite(annual_kwh) or annual_kwh < 0:
        raise ValueError("Annual energy must be finite and nonnegative")
    with np.load(path or PROFILE_DIR / "measured.npz", allow_pickle=False) as archive:
        return {name: normalized(archive[name]) * annual_kwh for name in sorted(archive.files)}


def metadata():
    return json.loads((PROFILE_DIR / "metadata.json").read_text(encoding="utf-8"))

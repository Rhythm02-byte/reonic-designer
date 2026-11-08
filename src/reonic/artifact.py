"""Saved models that cannot go stale.

A trained designer is slow to build (the app and the API both used to train on every start), so we save it. But a saved
model that no longer matches the code or the data would silently serve old designs, which is worse than being slow. So
every saved model carries a signature of what it was built from (the model code and the data files), and is only used
when the signature still matches. Otherwise it is rebuilt.
"""
import hashlib
from pathlib import Path

import joblib

CODE = ("model.py", "engine.py", "rules.py", "data.py", "physics.py", "schema.py", "baseline.py")


def signature(data_path: str | Path) -> str:
    """Hash of the model code plus the names and sizes of the data files (not their contents: they are large)."""
    h = hashlib.sha256()
    here = Path(__file__).parent
    for name in CODE:
        h.update((here / name).read_bytes())
    p = Path(data_path)
    files = sorted(p.rglob("*.csv")) if p.is_dir() else [p]
    for f in files:
        if f.exists():
            h.update(f"{f.relative_to(p) if p.is_dir() else f.name}:{f.stat().st_size}".encode())
    return h.hexdigest()[:16]


def load_if_fresh(path: str | Path, sig: str):
    """The saved object if it exists, loads, and was built from the same code and data; otherwise None."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        saved = joblib.load(path)
    except Exception:  # noqa: BLE001 - an unreadable or incompatible file just means: rebuild
        return None
    return saved["obj"] if isinstance(saved, dict) and saved.get("sig") == sig else None


def save(path: str | Path, obj, sig: str) -> bool:
    """Best effort: a read-only disk must not stop the app from running."""
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"sig": sig, "obj": obj}, path)
        return True
    except OSError:
        return False

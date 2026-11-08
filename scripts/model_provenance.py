"""Aggregate-only fingerprints shared by training, runtime boot and the final evaluation wrapper."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'services/engine/models/designer.joblib'
MANIFEST = ROOT / '.cache/model-provenance.json'

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def fingerprints():
    from engine.policy.designer import load_config
    h = hashlib.sha256()
    for p in sorted((ROOT / 'services/engine/engine').rglob('*.py')):
        h.update(str(p.relative_to(ROOT)).replace('\\', '/').encode())
        h.update(p.read_bytes())
    return {
        'modelSha256': file_hash(MODEL) if MODEL.exists() else None,
        'policySha256': hashlib.sha256(json.dumps(load_config(), sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'sourceSha256': h.hexdigest(),
    }

def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp'); temp.write_text(json.dumps(value, indent=2), encoding='utf-8'); temp.replace(path)

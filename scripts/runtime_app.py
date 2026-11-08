"""Uvicorn entry point recording the exact model loaded into the cached local API Store."""
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_provenance import ROOT, MANIFEST, fingerprints, write_json
from engine.api.main import app, get_store

before = fingerprints()
store = get_store()
after = fingerprints()
try: manifest = json.loads(MANIFEST.read_text('utf-8'))
except (OSError, ValueError): manifest = {}
verified = store.designer is not None and before == after and all(after[k] == manifest.get(k) for k in after) and store.designer.n_train == manifest.get('trainingRows')
write_json(ROOT / '.cache/engine-runtime.json', {
    **after, 'pid': os.getpid(), 'engineVersion': store.engine_version, 'synthetic': store.synthetic,
    'loadedAt': datetime.now(timezone.utc).isoformat(), 'verifiedManifest': verified,
    'trainingCutoff': manifest.get('trainingCutoff') if verified else None,
    'trainingRows': getattr(store.designer, 'n_train', None),
})

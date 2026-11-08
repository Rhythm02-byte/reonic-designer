"""Train the official cutoff policy, then bind aggregate provenance to its exact artifact."""
from __future__ import annotations
import json, runpy, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_provenance import ROOT, MODEL, MANIFEST, fingerprints, write_json
from engine.demo import HOLDOUT_CUTOFF
from engine.policy.designer import Designer

if len(sys.argv) != 1: raise SystemExit('This demo wrapper accepts no --all override.')
before = fingerprints()
sys.argv = ['engine.policy.train']
runpy.run_module('engine.policy.train', run_name='__main__')
after = fingerprints()
if any(before[k] != after[k] for k in ('policySha256', 'sourceSha256')):
    raise SystemExit('Engine/config changed during training. Retry after those edits finish; no provenance was certified.')
d = Designer.load(MODEL)
write_json(MANIFEST, {**after, 'trainingCutoff': HOLDOUT_CUTOFF.date().isoformat(), 'trainingRows': d.n_train,
                      'trainedAt': datetime.now(timezone.utc).isoformat(), 'scope': 'cutoff-only demo training'})
print(json.dumps({'trainingCutoff': HOLDOUT_CUTOFF.date().isoformat(), 'trainingRows': d.n_train, **after}))

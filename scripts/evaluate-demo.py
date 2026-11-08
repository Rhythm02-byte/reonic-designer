"""One final offline evaluation, with immutable aggregate source/config/model fingerprints.

Run only after the team freezes its selected configuration; never use this wrapper for routine checks.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_provenance import ROOT, fingerprints, write_json

before = fingerprints()
subprocess.run([sys.executable, str(ROOT / 'eval/run.py'), '--data', 'dataset', '--offline'], cwd=ROOT, check=True)
after = fingerprints()
if before != after: raise SystemExit('Model/config/source changed during the exam; results were not certified.')
p = ROOT / 'eval/results/latest.json'
result = json.loads(p.read_text('utf-8'))
result['provenance'] = after
write_json(p, result)
write_json(ROOT / '.cache/frozen-evaluation.json', {**after, 'generatedAt': result.get('generatedAt')})
print('Final evaluation bound to the exact model, config and engine source.')

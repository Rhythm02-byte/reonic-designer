"""Aggregate-only Slack run cards; never loads datasets or exposes raw records."""
import hashlib
import html
import json
import math
import time

from .common import state_dir
from .store import Store

METRICS = ('wholeDesign', 'ems', 'pv', 'battery', 'heatPump', 'wallbox', 'latencyP50ms')
LABELS = {'wholeDesign': 'Whole design', 'ems': 'EMS', 'pv': 'PV', 'battery': 'Battery',
          'heatPump': 'Heat pump', 'wallbox': 'Wallbox', 'latencyP50ms': 'Latency p50 (ms)'}


def escape(value):
    return html.escape(str(value), quote=False)


def number(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def clean_record(record):
    clean = {key: record[key] for key in ('id', 'timestamp', 'kind', 'label', 'comparisonKey', 'series')
             if isinstance(record.get(key), str)}
    if not clean.get('id'):
        raise ValueError('run id required')
    clean['git'] = {key: record.get('git', {}).get(key) for key in ('branch', 'commit', 'dirty')}
    clean['durationSec'] = number(record.get('durationSec'))
    clean['testScored'] = record.get('testScored') is True
    for split in ('validation', 'test'):
        block = record.get(split)
        if isinstance(block, dict):
            clean[split] = {'n': number(block.get('n')), 'models': {
                str(model): {metric: number(scores.get(metric)) for metric in METRICS
                             if number(scores.get(metric)) is not None}
                for model, scores in block.get('models', {}).items() if isinstance(scores, dict)}}
    if isinstance(record.get('repeated'), dict):
        clean['repeated'] = {key: {field: number(record['repeated'].get(key, {}).get(field))
                                  for field in ('mean', 'sd', 'n')} for key in ('ours', 'b0', 'gap')}
    return clean


def fmt(value):
    value = number(value)
    return f'{value:.2f}' if value is not None else 'nicht vorhanden'


def displayed(metric, value):
    value = number(value)
    # eval/metrics.py: tolerances are fractions; EMS is already 0..100, latency is ms.
    return value * 100 if value is not None and metric not in ('ems', 'latencyP50ms') else value


def section(text):
    return {'type': 'section', 'text': {'type': 'mrkdwn', 'text': text[:2900]}}


def card(record, history=()):
    r = clean_record(record)
    git = r['git']
    title = escape(r.get('label') or r.get('kind') or 'Evaluation')[:140]
    lines = [f"*{title}* · `{escape(r['id'])}`",
             f"Commit `{escape(git.get('commit') or 'unbekannt')}` · {escape(git.get('branch') or 'local')}"
             + (' · *DIRTY*' if git.get('dirty') else ''),
             f"Dauer: {fmt(r.get('durationSec'))} s · Test ausgewertet: {'ja' if r['testScored'] else 'nein'}"]
    blocks = [section('\n'.join(lines))]
    for split in ('validation', 'test'):
        if split not in r:
            continue
        block = r[split]
        table = [f"*{'Validierung' if split == 'validation' else 'TEST (keine Modellwahl)'}* · n={fmt(block.get('n'))}"]
        for model, scores in block['models'].items():
            table.append('*' + escape(model) + '*: ' + ' · '.join(f'{LABELS[k]} {fmt(displayed(k, scores.get(k)))}' for k in METRICS))
        # Slack sections are limited; split large model tables into readable sections.
        for start in range(0, len(table), 5):
            blocks.append(section('\n'.join(table[start:start + 5])))
    if r.get('repeated'):
        gap = r['repeated']['gap']
        blocks.append(section(f"Wiederholungen: Δ Whole design {fmt(displayed('wholeDesign', gap.get('mean')))} ± {fmt(displayed('wholeDesign', gap.get('sd')))} pp (SD), n={fmt(gap.get('n'))}"))
    chart = None
    # At most two models, drawn from the SAME split in the SAME run.
    block = r.get('validation') or r.get('test') or {}
    models = block.get('models', {})
    baseline = next((n for n in ('default', 'B0', 'b0') if n in models), next(iter(models), None))
    candidate = next((n for n in ('ours', 'composite', 'candidate') if n in models and n != baseline),
                     next((n for n in reversed(models) if n != baseline), None))
    names = [n for n in (baseline, candidate) if n is not None]
    if baseline and candidate:
        delta = displayed('wholeDesign', models[candidate].get('wholeDesign'))
        reference = displayed('wholeDesign', models[baseline].get('wholeDesign'))
        if delta is not None and reference is not None:
            blocks.append(section(f"Δ Whole design {escape(candidate)} gegen {escape(baseline)}: {delta - reference:+.2f} pp (gleicher Run/Split)"))
    metrics = [k for k in METRICS[:-1] if names and all(number(models[n].get(k)) is not None for n in names)]
    if metrics:
        chart = {'type': 'data_visualization', 'title': 'Validierung' if r.get('validation') else 'TEST · nur Bericht',
                 'chart': {'type': 'bar', 'series': [
                     {'name': f'{i + 1} {name}'[:20], 'data': [{'label': LABELS[k], 'value': displayed(k, models[name][k])} for k in metrics]}
                     for i, name in enumerate(names)],
                     'axis_config': {'categories': [LABELS[k] for k in metrics], 'y_label': 'Score (%)'}}}
        blocks.append(chart)
    # A history key must be supplied by eval; old heterogeneous runs are never guessed comparable.
    if r.get('comparisonKey') and r.get('validation'):
        comparable = [clean_record(p) for p in history if p.get('comparisonKey') == r['comparisonKey']
                      and p.get('validation') and p.get('id') != r['id']][-11:] + [r]
        shared = set.intersection(*(set(p['validation']['models']) for p in comparable)) if comparable else set()
        shared = sorted(n for n in shared if all(number(p['validation']['models'][n].get('wholeDesign')) is not None for p in comparable))[:2]
        if len(comparable) > 1 and shared:
            labels = [p['id'][:12] for p in comparable]
            blocks.append({'type': 'data_visualization', 'title': 'Vergleichbare Validierungsläufe', 'chart': {
                'type': 'line', 'series': [{'name': f'{i + 1} {name}'[:20], 'data': [
                    {'label': p['id'][:12], 'value': displayed('wholeDesign', p['validation']['models'][name]['wholeDesign'])} for p in comparable]}
                    for i, name in enumerate(shared)], 'axis_config': {'categories': labels, 'y_label': 'Whole design (%)'}}})
    elif not r.get('comparisonKey'):
        blocks.append(section('Kein Verlauf: verifizierte Daten-/Split-/Metrikkennung fehlt.'))
    fallback = '\n'.join(b['text']['text'] for b in blocks if b['type'] == 'section')
    return {'text': fallback[:39000], 'blocks': blocks[:45], 'unfurl_links': False, 'unfurl_media': False}


def publish(record, api, channel_id, store=None, existing_ts=None):
    """Durable run-id deduplication; ambiguous network failures are not blindly reposted."""
    r = clean_record(record)
    store = store or Store(state_dir() / 'cards.sqlite')
    key = 'run:' + r['id']
    with store.db() as db:
        found = db.execute('SELECT value FROM kv WHERE key=?', (key,)).fetchone()
        if found and existing_ts is None:
            return json.loads(found['value'])
        db.execute('INSERT INTO kv VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                   (key, json.dumps({'status': 'pending', 'record': r})))
    history = store.get('run-history', [])
    payload = card(r, history)
    payload['channel'] = channel_id
    payload['metadata'] = {'event_type': 'thinc_run', 'event_payload': {'id': r['id']}}
    if existing_ts:
        payload['ts'] = existing_ts
    elif r.get('kind') == 'research':
        group = r.get('series') or (r.get('timestamp', '')[:10] + ':' + str(r['git'].get('branch')))
        group_key = 'series:' + hashlib.sha256(group.encode()).hexdigest()[:20]
        parent = store.get(group_key)
        if not parent:
            parent_result = api('chat.postMessage', {'channel': channel_id, 'text': 'Research · ' + escape(group) + '\nEinzelne Auswertungen im Thread; kein automatischer Testsieger.'})
            if not parent_result.get('ok'):
                store.put(key, {'status': 'failed', 'error': parent_result.get('error')})
                return parent_result
            parent = {'ts': parent_result['ts'], 'count': 0}
        payload['thread_ts'] = parent['ts']
    result = api('chat.update' if existing_ts else 'chat.postMessage', payload)
    if not result.get('ok') and result.get('error') in ('invalid_blocks', 'invalid_arguments'):
        payload['blocks'] = [b for b in payload['blocks'] if b['type'] != 'data_visualization']
        result = api('chat.update' if existing_ts else 'chat.postMessage', payload)
    if result.get('ok'):
        saved = {'status': 'published', 'ts': result.get('ts', existing_ts), 'record': r}
        store.put(key, saved)
        store.put('run-history', (history + [r])[-100:])
        if payload.get('thread_ts'):
            parent['count'] += 1
            store.put(group_key, parent)
            api('chat.update', {'channel': channel_id, 'ts': parent['ts'], 'text':
                f"Research · {escape(group)} · {parent['count']} Auswertungen\nLetzter Run: {escape(r['id'])}. Details im Thread; keine Test-Modellwahl."})
        return saved
    saved = {'status': 'uncertain' if result.get('error') in ('URLError', 'TimeoutError') else 'failed',
             'error': result.get('error', 'unknown'), 'record': r}
    store.put(key, saved)
    return saved

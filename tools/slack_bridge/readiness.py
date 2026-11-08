"""Authenticated rollout confirmations backed by a fresh local runtime-hook execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

from .client import Inbox
from .common import request


def evidence(config, commit):
    if not config:
        raise ValueError('Client noch nicht registriert; private Zugangsdaten bei @Kian anfordern.')
    subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'], cwd=config['workdir'], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=config['workdir'], text=True).strip()
    inbox = Inbox(config['agent'])
    if time.time() - float(inbox.status('connected') or 0) > 45:
        raise ValueError('Client nicht verbunden; slack.py client mit der registrierten Konfiguration starten.')
    proof = json.loads(inbox.status('hook_proof') or '{}')
    if (not proof or time.time() - proof.get('at', 0) > 300 or proof.get('revision') != revision
        or not inbox.status('session_id') or proof.get('session') != inbox.status('session_id')):
        raise ValueError('Noch kein aktueller Hook-Nachweis. Projekt-Hooks freigeben und in der registrierten Sitzung ein Tool ausführen.')
    return {'commit': commit, 'revision': revision, 'hook': proof}


def validate(store, agent, data, now=None):
    now = time.time() if now is None else now
    registered = next(a for a in store.agents() if a['id'] == agent)
    proof = data.get('hook', {})
    expected = hashlib.sha256(Path(__file__).with_name('hooks.py').read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    if (registered['online'] < now - 45 or proof.get('runtime') != registered['runtime']
        or proof.get('session') != registered['session'] or registered['session'] in (None, 'pending')
        or proof.get('hash') != expected or now - proof.get('at', 0) > 300 or proof.get('at', now + 1) > now + 5
        or proof.get('revision') != data.get('revision')):
        raise ValueError('Hook-/Client-Nachweis fehlt, ist veraltet oder gehört zu einer anderen Sitzung.')
    import re
    if not re.fullmatch(r'[0-9a-f]{40}', data.get('revision', '')) or not re.fullmatch(r'[0-9a-f]{7,40}', data.get('commit', '')):
        raise ValueError('Git-Commit-Nachweis fehlt.')
    result = {'agent': agent, 'commit': data['commit'], 'revision': data['revision'], 'runtime': proof['runtime'],
              'session': proof['session'], 'hook_at': proof['at'], 'confirmed_at': now}
    store.put('ready:' + agent, result)
    return result

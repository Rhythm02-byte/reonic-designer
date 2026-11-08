"""Local configuration; credentials and state never live in tracked files."""
import hashlib
import json
import os
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[2]


def setting(name, default=None):
    if name in os.environ:
        return os.environ[name]
    try:
        for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
            key, sep, value = line.partition('=')
            if sep and key.strip() == name:
                return value.strip().strip('\"\'')
    except OSError:
        pass
    return default


def state_dir():
    base = Path(setting('SLACK_STATE_DIR', str(Path(os.getenv('LOCALAPPDATA', str(Path.home() / '.local/share'))) / 'thinc-slack')))
    return base / hashlib.sha256(str(ROOT).casefold().encode()).hexdigest()[:12]


def config_path():
    return Path(os.environ.get('SLACK_CLIENT_CONFIG', str(state_dir() / 'client.json')))


def read_config():
    try:
        return json.loads(config_path().read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def private_json(path, value):
    path = Path(path)
    # Refuse credentials anywhere in the checkout (including untracked directories).
    if path.resolve().is_relative_to(ROOT):
        raise ValueError('credential files must be outside the repository')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    path.chmod(0o600)


def request(config, route, data=None):
    url = config['url'].rstrip('/')
    if not url.startswith('https://') and not url.startswith(('http://127.0.0.1:', 'http://localhost:')):
        raise ValueError('HTTPS required outside loopback')
    req = urllib.request.Request(url + route, data=json.dumps(data).encode() if data is not None else None,
        headers={'Authorization': 'Bearer ' + config['token'], 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            detail = json.loads(error.read()).get('error', 'request rejected')
        except (ValueError, AttributeError):
            detail = 'request rejected'
        raise ValueError(f'bridge HTTP {error.code}: {str(detail)[:200]}') from None

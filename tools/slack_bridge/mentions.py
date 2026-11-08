"""Resolve configured GitHub/display aliases to real Slack mentions, never @all."""
import json
import re
from .common import state_dir
from .store import Store

# Public workspace member IDs, not credentials. Available even before client onboarding.
DEFAULT_MENTIONS = {
    'ilyas': 'U0CFULT8AR0', 'iemko23': 'U0CFULT8AR0',
    'rhythm': 'U0CGNUUQXLY', 'rhythm02-byte': 'U0CGNUUQXLY',
    'faras': 'U0CFYA7QRSQ', 'faris': 'U0CFYA7QRSQ', 'faris-el-mokhtari-svg': 'U0CFYA7QRSQ',
    'kian': 'U0CFWEEL76V', 'kian738': 'U0CFWEEL76V', 'karim': 'U0CFWEEL76V',
}


def resolve_mentions(text, mapping=None):
    if mapping is None:
        mapping = dict(DEFAULT_MENTIONS)
        try:
            mapping.update(json.loads((state_dir() / 'mentions.json').read_text(encoding='utf-8')))
        except (OSError, ValueError):
            if (state_dir() / 'bridge.sqlite').exists():
                mapping.update(Store(state_dir() / 'bridge.sqlite').get('mentions', {}))
    return re.sub(r'(?<![<\w])@([\w.-]+)',
                  lambda m: '<@' + mapping[m[1].casefold()] + '>' if m[1].casefold() in mapping else m[0], text)

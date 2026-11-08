"""Optional bridge commands dispatched by the backwards-compatible Slack CLI."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import uuid

from .common import ROOT, config_path, private_json, read_config, request, setting, state_dir
from .store import Store, ROLES

COMMANDS = {'bridge', 'register', 'client', 'inbox', 'ack', 'resolve', 'block', 'doctor', 'task', 'confirm-setup'}


def config_option(parser):
    parser.add_argument('--config', type=Path)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Durable Slack delivery, local inboxes and registered workers')
    commands = parser.add_subparsers(dest='cmd', required=True)
    bridge = commands.add_parser('bridge').add_subparsers(dest='operation', required=True)
    serve = bridge.add_parser('serve')
    serve.add_argument('--port', type=int, default=8765)
    serve.add_argument('--url')
    serve.add_argument('--without-socket', action='store_true', help='local transport pilot only; no Slack push')
    tunnel = bridge.add_parser('tunnel', help='isolated quick tunnel; updates the setup card endpoint automatically')
    tunnel.add_argument('--port', type=int, default=8765)
    endpoint = bridge.add_parser('endpoint')
    endpoint.add_argument('url')
    rollout = bridge.add_parser('rollout')
    rollout.add_argument('--commit', required=True)
    rollout.add_argument('--agent', action='append', required=True)
    config_option(rollout)
    provision = bridge.add_parser('provision')
    provision.add_argument('agent')
    provision.add_argument('--role', choices=ROLES, required=True)
    provision.add_argument('--slack-user', default='')
    provision.add_argument('--url')
    provision.add_argument('--allow-wake', action='store_true')
    provision.add_argument('--output', type=Path)
    migrate = bridge.add_parser('migrate')
    migrate.add_argument('--bind', action='append', default=[], help='legacy display name=provisioned agent id')
    bind = bridge.add_parser('bind-user')
    bind.add_argument('alias')
    bind.add_argument('slack_user', help='Slack member ID, for example U0123456789')
    rebuild = bridge.add_parser('runs-backfill')
    rebuild.add_argument('--limit', type=int, default=100)
    register = commands.add_parser('register')
    register.add_argument('--credentials', type=Path, required=True)
    register.add_argument('--runtime', choices=['codex', 'claude'], required=True)
    register.add_argument('--session', default=None)
    register.add_argument('--workdir', type=Path, default=ROOT)
    register.add_argument('--allow-wake', action='store_true')
    config_option(register)
    for command in ('client', 'inbox', 'doctor'):
        config_option(commands.add_parser(command))
    confirm = commands.add_parser('confirm-setup')
    confirm.add_argument('--commit', required=True)
    confirm.add_argument('--thread')
    config_option(confirm)
    for command in ('ack', 'resolve', 'block'):
        sub = commands.add_parser(command)
        sub.add_argument('id')
        config_option(sub)
    task = commands.add_parser('task')
    task.add_argument('text')
    task.add_argument('--to', action='append', default=[])
    task.add_argument('--path', action='append', default=[])
    task.add_argument('--channel', default='board')
    task.add_argument('--thread')
    task.add_argument('--priority', choices=['normal', 'critical'], default='normal')
    task.add_argument('--wake', action='store_true')
    task.add_argument('--commit', help='require recipients to verify this commit before acknowledgement')
    config_option(task)
    args = parser.parse_args(argv)
    if getattr(args, 'config', None):
        os.environ['SLACK_CLIENT_CONFIG'] = str(args.config.resolve())
    try:
        if args.cmd == 'bridge':
            return bridge_command(args)
        if args.cmd == 'register':
            config = json.loads(args.credentials.read_text(encoding='utf-8'))
            workdir = args.workdir.resolve()
            if not (workdir / 'AGENTS.md').exists():
                raise ValueError('workdir must contain AGENTS.md')
            config.update(runtime=args.runtime, session=args.session or 'pending', bind_on_start=not bool(args.session),
                          workdir=str(workdir), allow_wake=args.allow_wake)
            target = args.config or state_dir() / ('client-' + args.runtime + '.json')
            private_json(target, config)
            if not config_path().exists() or read_config().get('agent') == config['agent']:
                private_json(config_path(), config)
            from .client import Inbox
            with Inbox(config['agent']).connect() as db:
                db.execute("DELETE FROM status WHERE key='session_id'")
            request(config, '/register', {k: config[k] for k in ('runtime', 'session', 'workdir')})
            print('Registered:', config['agent'], 'configuration:', target)
            return 0
        config = read_config()
        if args.cmd == 'confirm-setup':
            from .readiness import evidence
            result = request(config, '/ready', evidence(config, args.commit))
            print('Verified:', result['agent'], 'commit', result['revision'], 'runtime', result['runtime'], 'fresh hook execution')
            return 0
        if args.cmd == 'doctor':
            return doctor(config)
        if not config:
            raise ValueError('client not configured; provision and register first')
        if args.cmd == 'client':
            from .client import run_client
            asyncio.run(run_client(config))
        elif args.cmd == 'inbox':
            print(json.dumps(request(config, '/inbox'), indent=2, ensure_ascii=True))
        elif args.cmd in ('ack', 'resolve', 'block'):
            from .client import Inbox
            state = {'ack': 'acknowledged', 'resolve': 'resolved', 'block': 'blocked'}[args.cmd]
            data = {'id': args.id, 'state': state}
            if state in ('acknowledged', 'resolved'):
                item = next((i for i in request(config, '/inbox') if i['id'] == args.id), None)
                required = item['payload'].get('required_commit') if item else None
                if required:
                    import subprocess
                    subprocess.run(['git', 'merge-base', '--is-ancestor', required, 'HEAD'], cwd=config['workdir'], check=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    data['revision'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=config['workdir'], text=True).strip()
            request(config, '/receipt', data)
            inbox = Inbox(config['agent'])
            try:
                inbox.receipt(args.id, state)
            except ValueError:
                pass
            print(state, args.id)
        elif args.cmd == 'task':
            print(json.dumps(request(config, '/post', {'text': args.text, 'to': args.to, 'paths': args.path,
                'channel': args.channel, 'thread': args.thread, 'priority': args.priority, 'wake': args.wake, 'required_commit': args.commit})))
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        # API exception strings can include request headers; report only safe known validation text.
        message = str(error) if isinstance(error, ValueError) else type(error).__name__
        if args.cmd == 'confirm-setup' and args.thread:
            import slack
            from .mentions import resolve_mentions
            failures = Store(state_dir() / 'cards.sqlite')
            key = 'setup-blocked:' + args.commit + ':' + read_config().get('agent', slack.who(None))
            if not failures.get(key):
                slack.send('board', resolve_mentions('@Kian') + ' Setup noch nicht bestätigt (' + slack.who(None) + '): ' + message,
                           thread_ts=args.thread)
                failures.put(key, True)
        print('slack bridge: ' + message, file=sys.stderr)
        return 1


def bridge_command(args):
    store = Store(state_dir() / 'bridge.sqlite')
    if args.operation == 'serve':
        from .server import serve
        asyncio.run(serve(args.port, args.url, not args.without_socket))
    elif args.operation == 'tunnel':
        import subprocess, shutil, re
        executable = shutil.which('cloudflared')
        if not executable:
            raise ValueError('cloudflared is not installed')
        config = state_dir() / 'tunnel-config.yml'
        config.write_text(f'url: http://127.0.0.1:{args.port}\n', encoding='utf-8')
        process = subprocess.Popen([executable, 'tunnel', '--config', str(config), '--url', f'http://127.0.0.1:{args.port}', '--no-autoupdate'],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            for line in process.stdout:
                match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', line)
                if match:
                    store.put('public-url', match[0])
                print(line.rstrip(), flush=True)
            return process.wait()
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
    elif args.operation == 'endpoint':
        if not args.url.startswith('https://') or any(c.isspace() for c in args.url):
            raise ValueError('public endpoint must be an HTTPS URL')
        store.put('public-url', args.url.rstrip('/'))
        print('Setup card endpoint updated')
    elif args.operation == 'rollout':
        print(json.dumps(request(read_config(), '/rollout', {'commit': args.commit, 'agents': args.agent})))
    elif args.operation == 'provision':
        from .mentions import DEFAULT_MENTIONS
        owner_alias = {'kian': 'kian', 'iemko': 'ilyas', 'rhythm': 'rhythm', 'faris': 'faris'}[args.role]
        slack_user = args.slack_user or DEFAULT_MENTIONS[owner_alias]
        secret = store.provision(args.agent, args.role, slack_user, args.allow_wake)
        path = args.output or state_dir() / ('credentials-' + args.agent + '.json')
        private_json(path, {'agent': args.agent, 'token': secret, 'url': args.url or store.get('public-url', 'http://127.0.0.1:8765')})
        print('Credential file (share privately, never in Slack):', path)
    elif args.operation == 'bind-user':
        import re
        if not re.fullmatch(r'[UW][A-Z0-9]{8,}', args.slack_user):
            raise ValueError('invalid Slack member ID')
        identities = store.get('mentions', {})
        identities[args.alias.casefold().lstrip('@')] = args.slack_user
        store.put('mentions', identities)
        print('Mention mapping updated:', args.alias)
    elif args.operation == 'migrate':
        import slack
        board = slack.fetch(slack.token(), 'board', None, 100, paginate=True)
        registry = slack.fetch(slack.token(), 'claims', None, 100, paginate=True)
        if board is None or registry is None:
            raise ValueError('cannot read legacy claim state')
        bindings = dict(v.split('=', 1) for v in args.bind)
        active = slack.open_claims(board + registry)
        owners = {}
        for scope, label in active.items():
            legacy = __import__('re').match(r"\[([^\]]+)'s agent\]", label)
            if not legacy or legacy[1] not in bindings:
                raise ValueError('explicit --bind required for active owner: ' + label)
            owners[scope] = bindings[legacy[1]]
        # Validate the whole mapping before importing any individual owner.
        if any(target not in {a['id'] for a in store.agents()} for target in owners.values()):
            raise ValueError('provision every bound target before migration')
        for scope, agent in owners.items():
            store.claim(agent, [scope], migration=True)
        for message in registry:
            row = slack.registry_row(message)
            if row and row[0] in bindings:
                store.put('claim-message:' + bindings[row[0]], message['ts'])
        print('Active claims imported:', len(store.claims()))
    elif args.operation == 'runs-backfill':
        backfill(store, args.limit)
    return 0


def backfill(store, limit):
    import slack
    from .runs import publish
    records = {}
    path = ROOT / 'eval/history/runs.jsonl'
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            record = json.loads(line)
            records[record['id']] = record
        except (ValueError, KeyError):
            continue
    messages = slack.fetch(slack.token(), 'runs', None, 100, paginate=True)
    if messages is None:
        raise ValueError('cannot read #runs')
    count = 0
    for message in messages[-limit:]:
        match = __import__('re').match(r'\[eval run\] id=([\w-]+)', message.get('text', ''))
        run_id = match[1] if match else message.get('metadata', {}).get('event_payload', {}).get('id')
        if not run_id:
            from .runs import Store, state_dir
            cards = Store(state_dir() / 'cards.sqlite')
            run_id = next((rid for rid in records if cards.get('run:' + rid, {}).get('ts') == message['ts']), None)
        if run_id in records:
            result = publish(records[run_id], lambda method, params: slack.call(method, slack.token(), params, True),
                             slack.channel_id(slack.token(), 'runs'), existing_ts=message['ts'])
            if result.get('status') != 'published':
                raise ValueError('backfill stopped; inspect cards state')
            count += 1
    print('Existing run messages upgraded in place:', count)


def doctor(config):
    import slack
    from .client import Inbox
    status = {'bot_token': bool(slack.token()), 'app_token': bool(setting('SLACK_APP_TOKEN')),
              'client_configured': bool(config), 'hook_configs': {
                  runtime: (ROOT / folder / filename).exists() for runtime, folder, filename in
                  [('codex', '.codex', 'hooks.json'), ('claude', '.claude', 'settings.json')]}}
    if config:
        try:
            status['bridge'] = request(config, '/health')
            status['registered_deliveries'] = len(request(config, '/inbox'))
        except Exception as error:
            status['bridge_error'] = type(error).__name__
        inbox = Inbox(config['agent'])
        status['local_pending'] = len(inbox.pending())
        status['last_connection'] = inbox.status('connected')
    print(json.dumps(status, indent=2))
    return 0 if config and status.get('bridge', {}).get('socket_mode') else 1

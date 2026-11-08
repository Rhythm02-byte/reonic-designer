"""Single Socket Mode receiver and authenticated team transport (optional dependencies)."""
import asyncio
import json
import logging
import time
import uuid

from .common import setting, state_dir
from .store import Store, ROLES

log = logging.getLogger(__name__)


class Bridge:
    def __init__(self, store, slack):
        self.store, self.slack = store, slack
        self.socket_online = False
        self.channels = {}
        self.refreshing = set()
        self.connections = {}

    def schedule_refresh(self, event_id):
        if event_id in self.refreshing:
            return
        self.refreshing.add(event_id)
        async def refresh():
            try:
                await asyncio.sleep(0.2)
                await self.refresh_task(event_id)
            except Exception as error:
                log.warning('Task mirror update failed (%s)', type(error).__name__)
            finally:
                self.refreshing.discard(event_id)
        asyncio.create_task(refresh())

    async def channel(self, name):
        if name not in self.channels:
            cursor = ''
            while True:
                result = await self.api('conversations.list', types='public_channel', exclude_archived=True, limit=200, cursor=cursor)
                self.channels.update({c['name']: c['id'] for c in result['channels']})
                cursor = result.get('response_metadata', {}).get('next_cursor', '')
                if not cursor:
                    break
        if name not in self.channels:
            raise ValueError('channel unavailable')
        return self.channels[name]

    async def api(self, method, **params):
        result = await self.slack.api_call(method, json=params)
        if not result.get('ok'):
            raise ValueError('Slack operation failed: ' + str(result.get('error')))
        return result

    def ingest(self, body):
        event = body.get('event', {})
        if event.get('subtype') == 'message_changed':
            event = dict(event.get('message', {}), channel=event.get('channel'))
        if not event.get('text') or not event.get('channel'):
            return False
        metadata = event.get('metadata', {})
        if metadata.get('event_type') in ('thinc_status', 'thinc_run', 'thinc_rollout'):
            return False
        task_id = metadata.get('event_payload', {}).get('task')
        if metadata.get('event_type') == 'thinc_task':
            return False  # authenticated post endpoint already queued it
        payload = {'text': event['text'][:16000], 'channel': event['channel'],
                   'thread': event.get('thread_ts') or event.get('ts'), 'created': time.time(),
                   'from': event.get('user') or event.get('bot_id'), 'priority': 'normal', 'wake': False}
        # Plain file mentions route by responsibility without accepting arbitrary commands.
        import re
        payload['paths'] = re.findall(r'(?<![\w/])(?:apps/web|services/engine|packages/contracts|docs|eval|data/external)(?:/[\w./-]+)?', event['text'])
        recipients = self.store.route(payload)
        return self.store.ingest(body.get('event_id') or str(uuid.uuid4()), payload, recipients)

    def task_card(self, event_id, payload):
        statuses = []
        recipients = []
        for agent in self.store.agents():
            for item in self.store.inbox(agent['id']):
                if item['id'] == event_id:
                    statuses.append(f"{agent['id']}: {item['state']}")
                    recipients.append(agent['id'])
        known = {a['id'] for a in self.store.agents()}
        statuses.extend(target + ': wartet auf Registrierung' for target in payload.get('to', []) if target not in known)
        text = '[' + payload.get('from', 'Team') + '] ' + payload['text'][:2200] + '\n' + (' · '.join(statuses) or 'Kein registrierter Empfänger')
        blocks = [{'type': 'section', 'text': {'type': 'mrkdwn', 'text': text[:2900]}}]
        for recipient in recipients:
            agent = next(a for a in self.store.agents() if a['id'] == recipient)
            actions = [('acknowledged', 'Übernommen'), ('blocked', 'Blockiert'), ('resolved', 'Erledigt')]
            if agent['allow_wake'] and time.time() - payload.get('created', 0) <= 600:
                actions.append(('wake', 'Einmal aktivieren'))
            blocks.append({'type': 'actions', 'elements': [
                {'type': 'button', 'text': {'type': 'plain_text', 'text': (label + ' · ' + recipient)[:75]},
                 'action_id': 'thinc_' + action, 'value': json.dumps({'event': event_id, 'agent': recipient})}
                for action, label in actions]})
        return {'text': text, 'blocks': blocks,
            'metadata': {'event_type': 'thinc_status', 'event_payload': {'task': event_id}}}

    async def refresh_task(self, event_id):
        payload = self.store.get('task:' + event_id)
        if payload:
            await self.api('chat.update', channel=payload['channel'], ts=payload.get('message_ts', payload['thread']), **self.task_card(event_id, payload))
            states = [item['state'] for agent in self.store.agents() for item in self.store.inbox(agent['id']) if item['id'] == event_id]
            emoji = ('white_check_mark' if states and all(s == 'resolved' for s in states) else
                     'octagonal_sign' if 'blocked' in states else 'eyes' if 'acknowledged' in states else None)
            previous = self.store.get('reaction:' + event_id)
            if emoji != previous:
                ts = payload.get('message_ts', payload['thread'])
                if previous:
                    await self.api('reactions.remove', channel=payload['channel'], timestamp=ts, name=previous)
                if emoji:
                    await self.api('reactions.add', channel=payload['channel'], timestamp=ts, name=emoji)
                self.store.put('reaction:' + event_id, emoji)

    async def post(self, agent_id, data):
        agents = {a['id']: a for a in self.store.agents()}
        targets = data.get('to') or []
        import re
        if not isinstance(targets, list) or len(targets) > 10 or any(not isinstance(t, str) or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,80}', t) for t in targets):
            raise ValueError('targets must be valid agent IDs (max 10)')
        actor = agents[agent_id]
        if data.get('wake') and actor['worker_until'] > time.time():
            raise ValueError('awakened workers cannot wake other agents')
        text = str(data.get('text', '')).strip()
        if not text or len(text) > 16000:
            raise ValueError('text required (max 16000 characters)')
        channel = data.get('channel', 'board')
        if channel not in ('board', 'engine', 'web', 'eval', 'pitch'):
            raise ValueError('invalid task channel')
        cid = await self.channel(channel)
        event_id = uuid.uuid4().hex
        from .mentions import resolve_mentions
        text = resolve_mentions(text)
        mentions = ' '.join(f"<@{agents[t]['slack_user']}>" if t in agents and agents[t]['slack_user'] else resolve_mentions('@' + t) for t in targets)
        payload = {'text': (mentions + '\n' + text).strip(), 'to': targets, 'paths': data.get('paths', []),
                   'from': agent_id, 'channel': cid, 'thread': data.get('thread'), 'created': time.time(),
                   'priority': data.get('priority', 'normal'), 'wake': bool(data.get('wake')),
                   'wake_hops': 1 if actor['worker_until'] > time.time() else 0}
        if data.get('required_commit'):
            import re
            if not re.fullmatch(r'[0-9a-f]{7,40}', data['required_commit']):
                raise ValueError('required_commit must be a Git commit hash')
            payload['required_commit'] = data['required_commit']
            payload['text'] += '\nVersion ' + data['required_commit'] + ': erst lokal übernehmen, dann slack.py ack <ID>.'
        if payload['wake'] and payload['priority'] != 'critical':
            raise ValueError('wake requires critical priority')
        recipients = self.store.route(payload)
        card = self.task_card(event_id, payload)
        # Task identity survives Slack retries. Bot-origin messages are not globally ignored.
        card['metadata'] = {'event_type': 'thinc_task', 'event_payload': {'task': event_id}}
        if payload['thread']:
            card['thread_ts'] = payload['thread']
        result = await self.api('chat.postMessage', channel=cid, **card)
        payload['thread'] = payload['thread'] or result.get('ts')
        payload['message_ts'] = result.get('ts')
        self.store.put('task:' + event_id, payload)
        self.store.ingest(event_id, payload, recipients)
        await self.refresh_task(event_id)
        return {'id': event_id, 'recipients': sorted(recipients)}

    async def action(self, body):
        action = body['actions'][0]
        value = json.loads(action['value'])
        event_id, target = value['event'], value['agent']
        who = body.get('user', {}).get('id')
        agents = [a for a in self.store.agents() if a['slack_user'] == who]
        if not agents or not any(i['id'] == event_id for i in self.store.inbox(target)):
            return
        if action['action_id'] == 'thinc_wake':
            payload = self.store.get('task:' + event_id)
            if not payload or time.time() - payload['created'] > 600:
                return
            # A human button is an explicit critical request, never an automatic mention wake.
            payload.update(wake=True, priority='critical')
            payload['wake_to'] = sorted(set(payload.get('wake_to', [])) | {target})
            self.store.put('task:' + event_id, payload)
            with self.store.db() as db:
                db.execute('UPDATE events SET payload=? WHERE id=?', (json.dumps(payload), event_id))
        else:
            payload = self.store.get('task:' + event_id, {})
            if payload.get('required_commit') and action['action_id'] in ('thinc_acknowledged', 'thinc_resolved'):
                return  # commit acknowledgement must come from the local CLI verification
            for agent in agents:
                if agent['id'] != target:
                    continue
                try:
                    self.store.receipt(agent['id'], event_id, action['action_id'][6:])
                except ValueError:
                    continue
        await self.refresh_task(event_id)

    async def mirror_claims(self, agent_id):
        claims = [c['area'] for c in self.store.claims() if c['agent'] == agent_id]
        cid = await self.channel('claims')
        key = 'claim-message:' + agent_id
        ts = self.store.get(key)
        params = {'channel': cid, 'text': f"CLAIMS [{agent_id}'s agent]" + ''.join('\n- ' + p for p in claims),
                  'metadata': {'event_type': 'thinc_status', 'event_payload': {}}}
        if ts:
            params['ts'] = ts
        result = await self.api('chat.update' if ts else 'chat.postMessage', **params)
        self.store.put(key, result['ts'])

    async def overview(self, url=None):
        cid = await self.channel('board')
        agents = self.store.agents()
        pending = sum(i['state'] != 'resolved' and i['payload'].get('action_required', True)
                      for a in agents for i in self.store.inbox(a['id']))
        text = '*Team-Koordination*\nBridge: ' + ('Slack verbunden' if self.socket_online else 'Slack nicht verbunden')
        text += f' · {pending} offene Zustellungen\n'
        text += '\n'.join(f"{a['id']} · {a['runtime'] or 'nicht registriert'} · " +
                          ('Client online' if time.time() - a['online'] < 45 else 'Client offline') +
                          (' · Wake freigegeben' if a['allow_wake'] else ' · Wake aus') for a in agents) or 'Noch keine Agents registriert.'
        if url:
            self.store.put('public-url', url)
        url = self.store.get('public-url')
        if url:
            text += '\nTeam-Endpunkt: ' + url + '\nZugangsdaten separat beziehen; keine Tokens in Slack.'
        if text == self.store.get('overview-text'):
            return
        params = {'channel': cid, 'text': text[:39000], 'metadata': {'event_type': 'thinc_status', 'event_payload': {}}}
        ts = self.store.get('overview-ts')
        if ts:
            params['ts'] = ts
        result = await self.api('chat.update' if ts else 'chat.postMessage', **params)
        self.store.put('overview-ts', result['ts'])
        self.store.put('overview-text', text)
        if not self.store.get('overview-pinned'):
            try:
                await self.api('pins.add', channel=cid, timestamp=result['ts'])
                self.store.put('overview-pinned', True)
            except Exception:
                log.warning('Overview could not be pinned; check pins:write')

    async def rollout(self, actor, data):
        if next(a for a in self.store.agents() if a['id'] == actor)['role'] != 'kian':
            raise ValueError('Only the coordinator can start a team rollout')
        import re
        commit = data.get('commit', '')
        targets = data.get('agents', [])
        if not re.fullmatch(r'[0-9a-f]{7,40}', commit) or not targets or len(targets) > 12:
            raise ValueError('commit and expected agent IDs required')
        if any(not re.fullmatch(r'[a-zA-Z0-9_.-]{1,80}', a) for a in targets):
            raise ValueError('invalid expected agent ID')
        from .mentions import resolve_mentions
        text = resolve_mentions('@Ilyas @Rhythm @Faras @Kian') + '\n'
        text += f'*Einmaliger Team-Pull + überprüfbare Bestätigung: `{commit}` auf `next`*\n'
        text += '1. Im sauberen Checkout `git pull --ff-only origin next`.\n'
        text += '2. tools/README.md: Client registrieren/starten, Projekt-Hooks einmal freigeben, in der Agent-Sitzung ein Tool ausführen.\n'
        text += f'3. `python tools/slack.py confirm-setup --commit {commit} --thread THREAD_TS` ausführen. '
        text += 'Die Bestätigung prüft Git-Version, verbundenen Client und einen frischen Hook-Lauf dieser Sitzung. '
        text += 'Ein normales „gelesen“ zählt nicht.\n'
        text += 'Falls etwas fehlt: im selben Thread mit Grund @Kian taggen. Fehlende Nachweise eskalieren nach fünf Minuten einmalig an @Kian.'
        text = resolve_mentions(text)
        cid = await self.channel('board')
        response = await self.api('chat.postMessage', channel=cid, text=text,
            metadata={'event_type': 'thinc_rollout', 'event_payload': {'commit': commit}})
        ts = response['ts']
        text = text.replace('THREAD_TS', ts)
        rollout = {'commit': commit, 'agents': targets, 'created': time.time(),
                   'deadline': time.time() + 300, 'channel': cid, 'ts': ts, 'text': text, 'escalated': False}
        self.store.put('rollout', rollout)
        payload = {'text': text, 'to': targets, 'from': actor, 'channel': cid, 'thread': ts,
                   'created': time.time(), 'wake': False, 'required_commit': commit}
        self.store.ingest('rollout:' + ts, payload, targets)
        await self.refresh_rollout()
        return {'thread': ts, 'commit': commit, 'expected': targets}

    async def refresh_rollout(self):
        rollout = self.store.get('rollout')
        if not rollout:
            return
        missing, lines = [], []
        for target in rollout['agents']:
            proof = self.store.get('ready:' + target, {})
            confirmed = proof.get('commit') == rollout['commit'] and proof.get('confirmed_at', 0) >= rollout['created']
            lines.append(('✅ ' if confirmed else '⏳ ') + target +
                         (f" · {proof['runtime']} · Commit + Hook bestätigt" if confirmed else ' · Nachweis fehlt'))
            if not confirmed:
                missing.append(target)
        text = rollout['text'] + '\n\n*Bestätigungen*\n' + '\n'.join(lines)
        if text != self.store.get('rollout-text'):
            await self.api('chat.update', channel=rollout['channel'], ts=rollout['ts'], text=text,
                metadata={'event_type': 'thinc_status', 'event_payload': {}})
            self.store.put('rollout-text', text)
        if (missing and time.time() >= rollout['deadline'] and not rollout['escalated']
            and self.store.once('rollout-escalation:' + rollout['ts'])):
            # Mark before sending: never blindly repeat an ambiguous escalation.
            rollout['escalated'] = True
            self.store.put('rollout', rollout)
            from .mentions import resolve_mentions
            await self.api('chat.postMessage', channel=rollout['channel'], thread_ts=rollout['ts'],
                text=resolve_mentions('@Kian') + ' Noch keine überprüfbare Pull-/Hook-Bestätigung von: ' + ', '.join(missing) +
                     '. Bitte Einrichtung/Hook-Freigabe klären; bloßes Lesen reicht nicht.',
                metadata={'event_type': 'thinc_escalation', 'event_payload': {}})


def create_app(store, bridge):
    from aiohttp import web

    @web.middleware
    async def auth(request, handler):
        if request.path == '/health':
            return await handler(request)
        credential = request.headers.get('Authorization', '')
        agent = store.authenticate(credential[7:]) if credential.startswith('Bearer ') else None
        if not agent:
            raise web.HTTPUnauthorized()
        request['agent'] = agent
        try:
            return await handler(request)
        except ValueError as error:
            return web.json_response({'error': str(error)}, status=409)
        except (KeyError, TypeError):
            return web.json_response({'error': 'invalid request fields'}, status=400)

    async def health(request):
        return web.json_response({'ok': True, 'socket_mode': bridge.socket_online})

    async def register(request):
        data = await request.json()
        store.register(request['agent'], data['runtime'], data['session'], data['workdir'])
        for item in store.inbox(request['agent']):
            bridge.schedule_refresh(item['id'])
        return web.json_response({'ok': True})

    async def inbox(request):
        return web.json_response(store.inbox(request['agent']))

    async def identities(request):
        return web.json_response(store.get('mentions', {}))

    async def ready(request):
        from .readiness import validate
        result = validate(store, request['agent'], await request.json())
        rollout = store.get('rollout')
        if rollout and result['commit'] == rollout['commit']:
            try:
                store.receipt(request['agent'], 'rollout:' + rollout['ts'], 'resolved')
            except ValueError:
                pass
        await bridge.refresh_rollout()
        return web.json_response(result)

    async def rollout(request):
        return web.json_response(await bridge.rollout(request['agent'], await request.json()))

    async def claims(request):
        if request.method == 'GET':
            return web.json_response(store.claims())
        data = await request.json()
        result = store.claim(request['agent'], data['paths'], data.get('release', False))
        await bridge.mirror_claims(request['agent'])
        return web.json_response(result)

    async def receipt(request):
        data = await request.json()
        payload = store.get('task:' + data['id'], {})
        if payload.get('required_commit') and data['state'] in ('acknowledged', 'resolved'):
            if not __import__('re').fullmatch(r'[0-9a-f]{40}', data.get('revision', '')):
                raise ValueError('local commit verification required; use slack.py ack/resolve')
            store.put('revision:' + request['agent'] + ':' + data['id'], data['revision'])
        store.receipt(request['agent'], data['id'], data['state'])
        bridge.schedule_refresh(data['id'])
        return web.json_response({'ok': True})

    async def post(request):
        return web.json_response(await bridge.post(request['agent'], await request.json()))

    async def finish(request):
        data = await request.json()
        agent = request['agent']
        current = next(a for a in store.agents() if a['id'] == agent)
        if current['worker'] != data['id']:
            raise ValueError('worker reservation does not match')
        if data.get('result'):
            payload = store.get('task:' + data['id'])
            if payload:
                text = str(data['result'])[:3500]
                result = await bridge.api('chat.postMessage', channel=payload['channel'], thread_ts=payload['thread'],
                    text=agent + ': ' + text, metadata={'event_type': 'thinc_status', 'event_payload': {}})
                report = {'text': text, 'channel': payload['channel'], 'thread': payload['thread'], 'from': agent,
                          'created': time.time(), 'wake': False, 'wake_hops': 1, 'action_required': False}
                store.ingest('result:' + data['id'], report, store.route(report) - {agent})
        store.finish_worker(agent, data['id'])
        return web.json_response({'ok': True})

    async def websocket(request):
        ws = web.WebSocketResponse(heartbeat=15, max_msg_size=128000)
        await ws.prepare(request)
        agent = request['agent']
        if agent in bridge.connections:
            await bridge.connections[agent].close(code=1000, message=b'replaced by a new connection')
        bridge.connections[agent] = ws
        sent = set()
        states_sent = {}
        wakes_sent = set()
        try:
            while not ws.closed:
                store.heartbeat(agent)
                for item in store.inbox(agent):
                    if item['id'] not in sent and item['state'] in ('queued', 'delivered'):
                        await ws.send_json({'type': 'event', **item})
                        sent.add(item['id'])
                    if states_sent.get(item['id']) != item['state']:
                        await ws.send_json({'type': 'state', 'id': item['id'], 'state': item['state']})
                        states_sent[item['id']] = item['state']
                    if item['payload'].get('wake') and item['id'] not in wakes_sent and store.reserve_wake(agent, item['id']):
                        await ws.send_json({'type': 'wake', **item})
                        wakes_sent.add(item['id'])
                try:
                    msg = await asyncio.wait_for(ws.receive(), timeout=0.5)
                    if msg.type == web.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get('type') == 'receipt':
                            store.receipt(agent, data['id'], data['state'])
                    elif msg.type in (web.WSMsgType.CLOSE, web.WSMsgType.CLOSED, web.WSMsgType.ERROR):
                        break
                except asyncio.TimeoutError:
                    pass
        finally:
            await ws.close()
            if bridge.connections.get(agent) is ws:
                bridge.connections.pop(agent, None)
        return ws

    app = web.Application(middlewares=[auth], client_max_size=128000)
    app.add_routes([web.get('/health', health), web.post('/register', register), web.get('/inbox', inbox), web.get('/identities', identities),
                    web.post('/ready', ready), web.post('/rollout', rollout),
                    web.get('/claims', claims), web.post('/claims', claims), web.post('/receipt', receipt),
                    web.post('/post', post), web.post('/worker-finished', finish), web.get('/ws', websocket)])
    return app


async def serve(port=8765, url=None, socket_mode=True):
    from aiohttp import web
    from slack_bolt.async_app import AsyncApp
    from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

    bot = setting('SLACK_BOT_TOKEN')
    if not bot:
        raise ValueError('SLACK_BOT_TOKEN missing')
    # process_before_response makes durable ingest finish before the Socket Mode acknowledgement.
    bolt = AsyncApp(token=bot, process_before_response=True, ignoring_self_events_enabled=False)
    store = Store(state_dir() / 'bridge.sqlite')
    bridge = Bridge(store, bolt.client)

    @bolt.event('message')
    async def message(body):
        bridge.ingest(body)

    @bolt.action(__import__('re').compile('^thinc_'))
    async def action(ack, body):
        await ack()
        await bridge.action(body)

    handler = None
    if socket_mode:
        token = setting('SLACK_APP_TOKEN')
        if not token:
            raise ValueError('SLACK_APP_TOKEN missing; enable Socket Mode and add the app token locally')
        handler = AsyncSocketModeHandler(bolt, token)
        await handler.connect_async()
        bridge.socket_online = True
    runner = web.AppRunner(create_app(store, bridge), access_log=None)
    await runner.setup()
    await web.TCPSite(runner, '127.0.0.1', port).start()
    print(f'Bridge listening on 127.0.0.1:{port}; Socket Mode={bridge.socket_online}', flush=True)
    try:
        while True:
            try:
                if handler:
                    bridge.socket_online = await handler.client.is_connected()
                await bridge.overview(url)
                await bridge.refresh_rollout()
            except Exception as error:
                log.warning('Overview update failed (%s)', type(error).__name__)
            await asyncio.sleep(30)
    finally:
        if handler:
            await handler.close_async()
        await runner.cleanup()

"""One outbound connection per registered session; hooks only touch this local inbox."""
import asyncio
import json
from pathlib import Path
import sqlite3
import subprocess
import time
from contextlib import contextmanager

from .common import request, state_dir


class Inbox:
    def __init__(self, agent, path=None):
        self.path = str(path or state_dir() / ('inbox-' + agent + '.sqlite'))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS inbox (id TEXT PRIMARY KEY,payload TEXT,state TEXT,updated REAL)')
            db.execute('CREATE TABLE IF NOT EXISTS outbox (id TEXT PRIMARY KEY,state TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS status (key TEXT PRIMARY KEY,value TEXT)')

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=1)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def add(self, item):
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO inbox VALUES(?,?,?,?)',
                       (item['id'], json.dumps(item['payload']), 'delivered', time.time()))
            db.execute('INSERT OR IGNORE INTO outbox VALUES(?,?)', (item['id'], 'delivered'))

    def receipt(self, event_id, state):
        with self.connect() as db:
            if not db.execute('SELECT 1 FROM inbox WHERE id=?', (event_id,)).fetchone():
                raise ValueError('event not in local inbox')
            db.execute('UPDATE inbox SET state=?,updated=? WHERE id=?', (state, time.time(), event_id))
            db.execute('INSERT INTO outbox VALUES(?,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state', (event_id, state))

    def pending(self):
        with self.connect() as db:
            return [{'id': r[0], 'payload': json.loads(r[1]), 'state': r[2]} for r in db.execute(
                "SELECT id,payload,state FROM inbox WHERE state='delivered' ORDER BY updated")]

    def remote_state(self, event_id, state):
        from .store import STATES
        if state not in STATES:
            return
        with self.connect() as db:
            row = db.execute('SELECT state FROM inbox WHERE id=?', (event_id,)).fetchone()
            if row and (STATES.index(state) > STATES.index(row[0]) or (row[0] == 'blocked' and state == 'acknowledged')):
                db.execute('UPDATE inbox SET state=?,updated=? WHERE id=?', (state, time.time(), event_id))

    def status(self, key, value=None):
        with self.connect() as db:
            if value is not None:
                db.execute('INSERT INTO status VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, str(value)))
            row = db.execute('SELECT value FROM status WHERE key=?', (key,)).fetchone()
        return row[0] if row else None

    def reserve_worker(self, event_id):
        with self.connect() as db:
            return bool(db.execute('INSERT OR IGNORE INTO status VALUES(?,?)', ('worker:' + event_id, 'started')).rowcount)

    def bind(self, session):
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO status VALUES(?,?)', ('session_id', session))
            return db.execute('SELECT value FROM status WHERE key=?', ('session_id',)).fetchone()[0] == session


async def run_client(config, stop=None):
    from aiohttp import ClientSession, ClientTimeout, WSMsgType
    inbox = Inbox(config['agent'])
    workers = set()
    backoff = 1
    # Validate HTTPS/loopback and credentials before opening a persistent connection.
    url = config['url'].rstrip('/') + '/ws'
    async with ClientSession(timeout=ClientTimeout(total=None, connect=10),
                             headers={'Authorization': 'Bearer ' + config['token']}) as session:
        try:
            while not stop or not stop.is_set():
                try:
                    await asyncio.to_thread(request, config, '/register', {
                        'runtime': config['runtime'], 'session': config['session'], 'workdir': config['workdir']})
                    from .common import private_json
                    private_json(state_dir() / 'mentions.json', await asyncio.to_thread(request, config, '/identities'))
                    async with session.ws_connect(url, heartbeat=15, max_msg_size=128000) as ws:
                        backoff = 1
                        last_ready_check = 0
                        while not ws.closed and (not stop or not stop.is_set()):
                            inbox.status('connected', time.time())
                            bound = inbox.status('session_id')
                            if bound and bound != config['session']:
                                await asyncio.to_thread(request, config, '/register', {
                                    'runtime': config['runtime'], 'session': bound, 'workdir': config['workdir']})
                                config['session'] = bound
                            if time.time() - last_ready_check >= 30:
                                last_ready_check = time.time()
                                try:
                                    rollout = await asyncio.to_thread(request, config, '/rollout')
                                    commit = rollout.get('commit')
                                    if rollout.get('expected') and commit and inbox.status('ready_commit') != commit:
                                        from .readiness import evidence
                                        proof = await asyncio.to_thread(evidence, config, commit)
                                        await asyncio.to_thread(request, config, '/ready', proof)
                                        inbox.status('ready_commit', commit)
                                except (ValueError, OSError, KeyError, subprocess.SubprocessError):
                                    pass  # stay pending until the real hook runs and the client is ready
                            # Explicit receipts are durable until the server confirms them.
                            with inbox.connect() as db:
                                receipts = list(db.execute('SELECT id,state FROM outbox'))
                            for event_id, state in receipts:
                                await asyncio.to_thread(request, config, '/receipt', {'id': event_id, 'state': state})
                                with inbox.connect() as db:
                                    db.execute('DELETE FROM outbox WHERE id=? AND state=?', (event_id, state))
                            try:
                                msg = await asyncio.wait_for(ws.receive(), timeout=0.5)
                            except asyncio.TimeoutError:
                                continue
                            if msg.type != WSMsgType.TEXT:
                                if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR):
                                    break
                                continue
                            item = json.loads(msg.data)
                            if item['type'] == 'event':
                                inbox.add(item)
                            elif item['type'] == 'state':
                                inbox.remote_state(item['id'], item['state'])
                            elif item['type'] == 'wake':
                                from .workers import run_worker
                                if not inbox.reserve_worker(item['id']):
                                    continue
                                task = asyncio.create_task(run_worker(config, item))
                                workers.add(task)
                                task.add_done_callback(workers.discard)
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    # Never log exception strings containing a request or credential.
                    inbox.status('last_error', type(error).__name__)
                    await asyncio.sleep(backoff)
                    backoff = min(30, backoff * 2)
        finally:
            for task in workers:
                task.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

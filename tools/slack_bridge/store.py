"""Transactional coordination and durable delivery. No Slack/network dependencies."""
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager

ROLES = {'kian': ['packages/contracts', 'docs', 'AGENTS.md', 'PLAN.md', 'CLAUDE.md', 'tools', '.codex', '.claude'],
         'rhythm': ['services/engine'], 'faris': ['apps/web'],
         'iemko': ['eval', 'data/external', 'apps/web/e2e']}
STATES = ['queued', 'delivered', 'context', 'acknowledged', 'blocked', 'resolved']


def area(value):
    value = value.replace('\\', '/').rstrip('/')
    if not value or value.startswith('/') or ':' in value or '..' in value.split('/') or any(c.isspace() for c in value):
        raise ValueError('invalid repository-relative scope')
    return '/'.join(p for p in value.split('/') if p and p != '.').casefold()


def overlaps(a, b):
    a, b = area(a), area(b)
    return a == b or a.startswith(b + '/') or b.startswith(a + '/')


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS agents (
                  id TEXT PRIMARY KEY, role TEXT NOT NULL, secret TEXT NOT NULL, slack_user TEXT,
                  runtime TEXT, session TEXT, workdir TEXT, allow_wake INTEGER NOT NULL DEFAULT 0,
                  online REAL NOT NULL DEFAULT 0, last_wake REAL NOT NULL DEFAULT 0,
                  worker TEXT, worker_until REAL NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, payload TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS deliveries (
                  agent TEXT NOT NULL, event TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'queued',
                  updated REAL NOT NULL, PRIMARY KEY(agent,event));
                CREATE TABLE IF NOT EXISTS claims (area TEXT PRIMARY KEY, agent TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            ''')

    @contextmanager
    def db(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute('BEGIN IMMEDIATE')
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def provision(self, agent, role, slack_user='', allow_wake=False):
        if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,80}', agent) or role not in ROLES:
            raise ValueError('invalid agent or role')
        secret = secrets.token_urlsafe(32)
        with self.db() as db:
            # Explicit re-provision rotates a lost credential; never resets worker/cooldown state.
            db.execute('INSERT INTO agents(id,role,secret,slack_user,allow_wake) VALUES(?,?,?,?,?) '
                       'ON CONFLICT(id) DO UPDATE SET role=excluded.role,secret=excluded.secret,'
                       'slack_user=excluded.slack_user,allow_wake=excluded.allow_wake',
                       (agent, role, hashlib.sha256(secret.encode()).hexdigest(), slack_user, bool(allow_wake)))
        return secret

    def authenticate(self, secret):
        digest = hashlib.sha256(secret.encode()).hexdigest()
        with self.db() as db:
            for row in db.execute('SELECT id,secret FROM agents'):
                if hmac.compare_digest(row['secret'], digest):
                    return row['id']
        return None

    def agents(self):
        with self.db() as db:
            return [dict(row) for row in db.execute('SELECT id,role,slack_user,runtime,session,workdir,allow_wake,online,worker,worker_until FROM agents')]

    def register(self, agent, runtime, session, workdir):
        if runtime not in ('codex', 'claude') or not session or not workdir:
            raise ValueError('runtime, session and workdir required')
        with self.db() as db:
            db.execute('UPDATE agents SET runtime=?,session=?,workdir=?,online=? WHERE id=?',
                       (runtime, session, workdir, time.time(), agent))
            for row in db.execute('SELECT id,payload FROM events').fetchall():
                if agent in json.loads(row['payload']).get('to', []):
                    db.execute('INSERT OR IGNORE INTO deliveries(agent,event,updated) VALUES(?,?,?)', (agent, row['id'], time.time()))

    def heartbeat(self, agent):
        with self.db() as db:
            db.execute('UPDATE agents SET online=? WHERE id=?', (time.time(), agent))

    def ingest(self, event_id, payload, recipients):
        with self.db() as db:
            inserted = db.execute('INSERT OR IGNORE INTO events VALUES(?,?,?)',
                                  (event_id, json.dumps(payload), time.time())).rowcount
            if inserted:
                for agent in set(recipients):
                    if db.execute('SELECT 1 FROM agents WHERE id=?', (agent,)).fetchone():
                        db.execute('INSERT INTO deliveries(agent,event,updated) VALUES(?,?,?)', (agent, event_id, time.time()))
        return bool(inserted)

    def route(self, payload):
        recipients = set(payload.get('to', []))
        text = payload.get('text', '')
        for row in self.agents():
            if row['slack_user'] and f"<@{row['slack_user']}>" in text:
                recipients.add(row['id'])
            if any(overlaps(scope, root) for scope in payload.get('paths', []) for root in ROLES[row['role']]):
                if row['role'] != 'faris' or not all(area(p).startswith('apps/web/e2e') for p in payload['paths']):
                    recipients.add(row['id'])
        # Thread participants keep receiving replies even without another mention.
        thread = payload.get('thread')
        if thread:
            with self.db() as db:
                for row in db.execute('SELECT DISTINCT d.agent,e.payload FROM deliveries d JOIN events e ON e.id=d.event'):
                    previous = json.loads(row['payload'])
                    if previous.get('channel') == payload.get('channel') and previous.get('thread') == thread:
                        recipients.add(row['agent'])
        return recipients

    def inbox(self, agent, pending_only=False):
        with self.db() as db:
            rows = db.execute('SELECT e.id,e.payload,d.state,e.created FROM deliveries d JOIN events e ON e.id=d.event '
                              'WHERE d.agent=? ORDER BY e.created', (agent,)).fetchall()
        return [dict(id=r['id'], payload=json.loads(r['payload']), state=r['state'], created=r['created'])
                for r in rows if not pending_only or r['state'] in ('queued', 'delivered')]

    def receipt(self, agent, event, state):
        if state not in STATES:
            raise ValueError('invalid delivery state')
        with self.db() as db:
            row = db.execute('SELECT state FROM deliveries WHERE agent=? AND event=?', (agent, event)).fetchone()
            if not row:
                raise ValueError('event not assigned to this agent')
            if STATES.index(state) < STATES.index(row['state']) and not (row['state'] == 'blocked' and state == 'acknowledged'):
                return
            db.execute('UPDATE deliveries SET state=?,updated=? WHERE agent=? AND event=?', (state, time.time(), agent, event))
            if state in ('acknowledged', 'blocked', 'resolved'):
                db.execute("UPDATE kv SET value=? WHERE key=?", (json.dumps('started'), f'wake:{agent}:{event}'))

    def claim(self, agent, paths, release=False, migration=False):
        paths = sorted(set(area(p) for p in paths))
        with self.db() as db:
            row = db.execute('SELECT role FROM agents WHERE id=?', (agent,)).fetchone()
            if not row:
                raise ValueError('unknown agent')
            for path in paths:
                if not migration and (not any(path == area(root) or path.startswith(area(root) + '/') for root in ROLES[row['role']])
                    or (row['role'] == 'faris' and overlaps(path, 'apps/web/e2e'))):
                    raise ValueError('scope outside assigned ownership')
                for held in db.execute('SELECT area,agent FROM claims'):
                    if held['agent'] != agent and (overlaps(path, held['area']) if not release else path == held['area']):
                        raise ValueError(f"claim conflict: {held['area']} ({held['agent']})")
            for path in paths:
                if release:
                    db.execute('DELETE FROM claims WHERE area=? AND agent=?', (path, agent))
                else:
                    db.execute('INSERT OR IGNORE INTO claims VALUES(?,?)', (path, agent))
        return self.claims()

    def claims(self):
        with self.db() as db:
            return [dict(row) for row in db.execute('SELECT area,agent FROM claims ORDER BY area')]

    def reserve_wake(self, agent, event, now=None):
        now = time.time() if now is None else now
        with self.db() as db:
            row = db.execute('SELECT * FROM agents WHERE id=?', (agent,)).fetchone()
            delivery = db.execute('SELECT e.payload,d.state FROM events e JOIN deliveries d ON d.event=e.id '
                                  'WHERE e.id=? AND d.agent=?', (event, agent)).fetchone()
            if not row or not delivery:
                return False
            payload = json.loads(delivery['payload'])
            if payload.get('wake_to') and agent not in payload['wake_to']:
                return False
            key = f'wake:{agent}:{event}'
            reservation = db.execute('SELECT value FROM kv WHERE key=?', (key,)).fetchone()
            if (reservation and json.loads(reservation['value']) == 'reserved' and row['worker'] == event
                and row['allow_wake'] and row['online'] >= now - 45 and now - payload.get('created', 0) <= 600
                and row['worker_until'] > now and delivery['state'] not in ('acknowledged', 'blocked', 'resolved')):
                return True  # reconnect may resend an unacknowledged reservation; local client deduplicates
            if (not row['allow_wake'] or not row['runtime'] or row['session'] == 'pending' or row['online'] < now - 45
                or row['last_wake'] > now - 1800 or row['worker_until'] > now
                or delivery['state'] in ('acknowledged', 'resolved') or not payload.get('wake')
                or payload.get('priority') != 'critical' or payload.get('wake_hops', 0) != 0
                or now - payload.get('created', 0) > 600 or payload.get('created', now + 1) > now):
                return False
            # Durable replay protection even after worker completion and cooldown.
            if db.execute('SELECT 1 FROM kv WHERE key=?', (key,)).fetchone():
                return False
            db.execute('INSERT INTO kv VALUES(?,?)', (key, json.dumps('reserved')))
            db.execute('UPDATE agents SET last_wake=?,worker=?,worker_until=? WHERE id=?', (now, event, now + 600, agent))
        return True

    def finish_worker(self, agent, event):
        with self.db() as db:
            db.execute('UPDATE agents SET worker=NULL,worker_until=0 WHERE id=? AND worker=?', (agent, event))

    def get(self, key, default=None):
        with self.db() as db:
            row = db.execute('SELECT value FROM kv WHERE key=?', (key,)).fetchone()
        return json.loads(row['value']) if row else default

    def put(self, key, value):
        with self.db() as db:
            db.execute('INSERT INTO kv VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, json.dumps(value)))

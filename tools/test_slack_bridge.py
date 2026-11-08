"""Offline bridge tests, including real loopback WebSocket delivery."""
import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch, AsyncMock

from slack_bridge.store import Store
from slack_bridge.runs import card, publish, clean_record
from slack_bridge.mentions import resolve_mentions
from slack_bridge.client import Inbox
from slack_bridge.hooks import hook
from slack_bridge.server import Bridge


class TemporaryStore(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / 'bridge.sqlite')
        self.token = self.store.provision('kian', 'kian', 'U12345678', True)
        self.store.provision('other', 'kian')
        self.store.register('kian', 'codex', 'session', '/repo')

    def event(self, event_id='e1', **overrides):
        payload = {'created': time.time(), 'text': 'please review', 'priority': 'critical', 'wake': True, 'wake_hops': 0}
        payload.update(overrides)
        self.store.ingest(event_id, payload, ['kian'])
        return payload

    def test_credentials_are_hashed_and_scoped(self):
        self.assertEqual(self.store.authenticate(self.token), 'kian')
        self.assertIsNone(self.store.authenticate('incorrect'))
        self.assertNotIn(self.token, Path(self.store.path).read_bytes().decode('latin1'))

    def test_two_concurrent_overlapping_claims_have_one_winner(self):
        def acquire(agent, scope):
            try:
                self.store.claim(agent, [scope])
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda args: acquire(*args), [('kian', 'tools'), ('other', 'tools/slack.py')]))
        self.assertEqual(sum(results), 1)

    def test_ownership_and_foreign_release_are_rejected(self):
        self.store.claim('kian', ['tools'])
        with self.assertRaises(ValueError):
            self.store.claim('other', ['tools'], release=True)
        with self.assertRaises(ValueError):
            self.store.claim('kian', ['services/engine'])
        self.assertEqual(len(self.store.claims()), 1)

    def test_durable_dedup_and_separate_receipt_states(self):
        self.event()
        self.assertFalse(self.store.ingest('e1', {'text': 'duplicate'}, ['kian']))
        reopened = Store(self.store.path)
        reopened.receipt('kian', 'e1', 'delivered')
        self.assertEqual(reopened.inbox('kian')[0]['state'], 'delivered')
        reopened.receipt('kian', 'e1', 'context')
        reopened.receipt('kian', 'e1', 'acknowledged')
        reopened.receipt('kian', 'e1', 'delivered')
        self.assertEqual(reopened.inbox('kian')[0]['state'], 'acknowledged')
        with self.assertRaises(ValueError):
            reopened.receipt('other', 'e1', 'resolved')

    def test_thread_replies_route_without_repeated_mentions(self):
        self.store.ingest('root', {'text': 'hello', 'channel': 'C1', 'thread': '123'}, ['kian'])
        self.assertEqual(self.store.route({'text': 'follow-up', 'channel': 'C1', 'thread': '123'}), {'kian'})
        self.assertEqual(self.store.route({'text': 'unrelated', 'channel': 'C2', 'thread': '123'}), set())

    def test_explicit_recipient_does_not_fan_out_to_same_human_and_replies_reach_sender(self):
        self.store.provision('sibling', 'kian', 'U12345678')
        self.assertEqual(self.store.route({'text': '<@U12345678>', 'to': ['kian']}), {'kian'})
        self.store.ingest('root', {'text': 'request', 'channel': 'C1', 'thread': '321', 'from': 'other'}, ['kian'])
        self.assertEqual(self.store.route({'text': 'reply', 'channel': 'C1', 'thread': '321'}), {'kian', 'other'})

    def test_wake_is_bounded_and_replay_protected(self):
        self.event()
        self.assertTrue(self.store.reserve_wake('kian', 'e1'))
        self.store.receipt('kian', 'e1', 'acknowledged')
        self.assertFalse(self.store.reserve_wake('kian', 'e1'))
        self.store.finish_worker('kian', 'e1')
        self.event('e2')
        self.assertFalse(self.store.reserve_wake('kian', 'e2'))
        self.assertFalse(self.store.reserve_wake('kian', 'e1', now=time.time() + 2000))

    def test_normal_expired_chained_offline_and_nonopted_wakes_rejected(self):
        cases = [{'priority': 'normal'}, {'wake': False}, {'wake_hops': 1}, {'created': time.time() - 601}]
        for i, overrides in enumerate(cases):
            self.event(str(i), **overrides)
            self.assertFalse(self.store.reserve_wake('kian', str(i)))
        self.event('offline')
        with self.store.db() as db:
            db.execute('UPDATE agents SET online=0 WHERE id=?', ('kian',))
        self.assertFalse(self.store.reserve_wake('kian', 'offline'))
        self.store.provision('disabled', 'kian', allow_wake=False)
        self.store.register('disabled', 'claude', 's', '/repo')
        self.store.ingest('no-optin', {'created': time.time(), 'priority': 'critical', 'wake': True}, ['disabled'])
        self.assertFalse(self.store.reserve_wake('disabled', 'no-optin'))

    def test_bot_events_delivered_status_events_ignored(self):
        bridge = Bridge(self.store, None)
        body = {'event_id': 'bot-event', 'event': {'channel': 'C1', 'ts': '123', 'bot_id': 'same-shared-bot',
                'text': 'hello <@U12345678>'}}
        self.assertTrue(bridge.ingest(body))
        self.assertEqual(len(self.store.inbox('kian')), 1)
        body['event_id'] = 'status-event'
        body['event']['metadata'] = {'event_type': 'thinc_status'}
        self.assertFalse(bridge.ingest(body))

    def test_hook_is_local_silent_when_empty_and_does_not_ack(self):
        local = Inbox('kian', Path(self.temp.name) / 'local.sqlite')
        config = {'agent': 'kian', 'runtime': 'codex'}
        with patch('slack_bridge.hooks.Inbox', return_value=local):
            self.assertIsNone(hook('codex', {'hook_event_name': 'PostToolUse'}, config))
            local.add({'id': 'e1', 'payload': {'text': 'read docs', 'from': 'team'}})
            result = hook('codex', {'hook_event_name': 'PostToolUse', 'session_id': 's1'}, config)
            self.assertIn('read docs', result['hookSpecificOutput']['additionalContext'])
            with local.connect() as db:
                self.assertEqual(db.execute('SELECT state FROM inbox').fetchone()[0], 'context')
            self.assertIsNone(hook('codex', {'hook_event_name': 'PostToolUse', 'session_id': 's1'}, config))

    def test_hook_does_not_leak_to_another_session_or_loop_on_stop(self):
        local = Inbox('kian', Path(self.temp.name) / 'local.sqlite')
        local.status('session_id', 's1')
        local.add({'id': 'e1', 'payload': {'text': 'private routing'}})
        with patch('slack_bridge.hooks.Inbox', return_value=local):
            self.assertIsNone(hook('codex', {'session_id': 's2'}, {'agent': 'kian', 'runtime': 'codex'}))
            self.assertIsNone(hook('codex', {'hook_event_name': 'Stop', 'stop_hook_active': True}, {'agent': 'kian', 'runtime': 'codex'}))
        self.assertEqual(len(local.pending()), 1)

    def test_unbound_client_attaches_once_at_session_start(self):
        local = Inbox('kian', Path(self.temp.name) / 'local.sqlite')
        local.add({'id': 'e1', 'payload': {'text': 'new session'}})
        config = {'agent': 'kian', 'runtime': 'claude', 'session': 'pending', 'bind_on_start': True}
        with patch('slack_bridge.hooks.Inbox', return_value=local):
            self.assertIsNone(hook('claude', {'hook_event_name': 'PostToolUse', 'session_id': 'one'}, config))
            self.assertIsNotNone(hook('claude', {'hook_event_name': 'SessionStart', 'session_id': 'one'}, config))
            self.assertIsNone(hook('claude', {'hook_event_name': 'SessionStart', 'session_id': 'two'}, config))

    def test_local_worker_reservation_is_atomic(self):
        local = Inbox('kian', Path(self.temp.name) / 'local.sqlite')
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(local.reserve_worker, ['same-event', 'same-event']))
        self.assertEqual(sum(result), 1)

    def test_remote_resolution_removes_pending_local_work_without_regression(self):
        local = Inbox('kian', Path(self.temp.name) / 'local.sqlite')
        local.add({'id':'done','payload':{'text':'already resolved elsewhere'}})
        local.remote_state('done','resolved')
        local.remote_state('done','delivered')
        self.assertEqual(local.pending(),[])

    def test_once_guard_survives_concurrent_calls_and_restart(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(self.store.once, ['same-escalation','same-escalation']))
        self.assertEqual(sum(result), 1)
        self.assertFalse(Store(self.store.path).once('same-escalation'))

    def test_setup_confirmation_needs_fresh_matching_runtime_hook(self):
        from slack_bridge.readiness import validate
        from slack_bridge import hooks
        data = {'commit': 'a'*7, 'revision': 'a'*40, 'hook': {'runtime': 'codex', 'session': 'session',
            'at': time.time(), 'revision': 'a'*40, 'hash': hashlib.sha256(Path(hooks.__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest()}}
        self.assertEqual(validate(self.store, 'kian', data)['agent'], 'kian')
        data['hook']['session'] = 'wrong-session'
        with self.assertRaises(ValueError):
            validate(self.store, 'kian', data)

    def test_config_files_or_stale_hook_alone_do_not_confirm_setup(self):
        from slack_bridge.readiness import validate
        with self.assertRaises(ValueError):
            validate(self.store, 'kian', {'commit': 'a'*7, 'revision': 'a'*40, 'hook': {}})
        with self.assertRaises(ValueError):
            validate(self.store, 'kian', {'commit': 'a'*7, 'revision': 'a'*40,
                'hook': {'runtime': 'codex', 'session': 'session', 'at': time.time()-600, 'revision':'a'*40, 'hash':'old'}})


class CardTests(unittest.TestCase):
    def record(self, **updates):
        result = {'id': 'run-1', 'kind': 'research', 'timestamp': '2026-11-08T00:00:00Z',
            'git': {'branch': 'next', 'commit': '123abcd', 'dirty': True}, 'testScored': False,
            'validation': {'n': 20, 'models': {'default': {'wholeDesign': .60, 'pv': .80}, 'candidate': {'wholeDesign': .65, 'pv': .85}}},
            'repeated': {'gap': {'mean': .002, 'sd': .004, 'n': 20}}}
        result.update(updates)
        return result

    def test_nested_scores_missing_values_and_no_raw_fields(self):
        record = self.record(raw_rows=[{'customer': 'SECRET'}])
        result = card(record)
        self.assertIn('65.00', result['text'])
        self.assertIn('nicht vorhanden', result['text'])
        self.assertIn('DIRTY', result['text'])
        self.assertNotIn('SECRET', json.dumps(clean_record(record)))
        self.assertIn('0.20 ± 0.40', result['text'])

    def test_only_verified_validation_history_is_connected(self):
        first = self.record(id='old', comparisonKey='split-A')
        second = self.record(comparisonKey='split-B')
        self.assertEqual(sum(b['type'] == 'data_visualization' for b in card(second, [first])['blocks']), 1)
        second['comparisonKey'] = 'split-A'
        self.assertEqual(sum(b['type'] == 'data_visualization' for b in card(second, [first])['blocks']), 2)
        second.pop('validation')
        second['test'] = first['validation']
        self.assertLessEqual(sum(b['type'] == 'data_visualization' for b in card(second, [first])['blocks']), 1)

    def test_chart_failure_falls_back_and_run_id_is_not_reposted(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / 'cards.sqlite')
            calls = []
            def api(method, params):
                calls.append((method, params))
                if any(b['type'] == 'data_visualization' for b in params.get('blocks', [])):
                    return {'ok': False, 'error': 'invalid_blocks'}
                return {'ok': True, 'ts': '123'}
            result = publish(self.record(kind='full'), api, 'C1', store)
            self.assertEqual(result['status'], 'published')
            self.assertEqual(len(calls), 2)
            publish(self.record(kind='full'), api, 'C1', store)
            self.assertEqual(len(calls), 2)

    def test_real_mentions_only_for_explicitly_bound_names(self):
        self.assertEqual(resolve_mentions('Hi @Kian738 @other @all', {'kian738': 'U12345678'}), 'Hi <@U12345678> @other @all')

    def test_team_aliases_work_before_any_client_configuration(self):
        with tempfile.TemporaryDirectory() as tmp, patch('slack_bridge.mentions.state_dir', return_value=Path(tmp)):
            self.assertEqual(resolve_mentions('@Ilyas @Rhythm @Faras @Kian'),
                '<@U0CFULT8AR0> <@U0CGNUUQXLY> <@U0CFYA7QRSQ> <@U0CFWEEL76V>')

    def test_fraction_metrics_are_percentages_but_ems_is_not_rescaled(self):
        record = self.record()
        record['validation']['models']['candidate']['ems'] = 55.77
        result = card(record)
        self.assertIn('EMS 55.77', result['text'])
        chart = next(b for b in result['blocks'] if b['type'] == 'data_visualization')
        self.assertEqual(chart['chart']['series'][1]['data'][0]['value'], 65.0)


try:
    import aiohttp
except ImportError:
    aiohttp = None


@unittest.skipUnless(aiohttp, 'optional aiohttp dependency not installed')
class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from aiohttp.test_utils import TestServer, TestClient
        from slack_bridge.server import create_app
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / 'bridge.sqlite')
        self.token = self.store.provision('target', 'kian')
        self.bridge = Bridge(self.store, None)
        self.bridge.refresh_task = AsyncMock()
        self.client = TestClient(TestServer(create_app(self.store, self.bridge)))
        await self.client.start_server()
        self.headers = {'Authorization': 'Bearer ' + self.token}

    async def asyncTearDown(self):
        await self.client.close()
        self.temp.cleanup()

    async def test_auth_delivery_reconnect_and_explicit_ack_over_real_websocket(self):
        response = await self.client.get('/inbox')
        self.assertEqual(response.status, 401)
        self.store.ingest('event-1', {'text': 'hello'}, ['target'])
        async with self.client.ws_connect('/ws', headers=self.headers) as ws:
            item = await asyncio.wait_for(ws.receive_json(), 2)
            self.assertEqual(item['id'], 'event-1')
        async with self.client.ws_connect('/ws', headers=self.headers) as ws:
            item = await asyncio.wait_for(ws.receive_json(), 2)
            self.assertEqual(item['id'], 'event-1')
            response = await self.client.post('/receipt', headers=self.headers, json={'id': 'event-1', 'state': 'acknowledged'})
            self.assertEqual(response.status, 200)
        self.assertEqual(self.store.inbox('target')[0]['state'], 'acknowledged')
        self.assertEqual(len(self.store.inbox('target')), 1)

    async def test_task_buttons_are_scoped_and_worker_wake_chains_rejected(self):
        self.store.provision('owner', 'kian', 'UOWNER123')
        self.store.provision('target', 'kian', 'UTARGET12')
        payload = {'text': 'please review', 'channel': 'C1', 'thread': '111', 'to': ['target'], 'created': time.time()}
        self.store.ingest('task-one', payload, ['target'])
        self.store.put('task:task-one', payload)
        self.bridge.api = AsyncMock(return_value={'ok': True, 'ts': '111'})
        body = {'user': {'id': 'UOWNER123'}, 'actions': [{'action_id': 'thinc_acknowledged', 'value': json.dumps({'event': 'task-one', 'agent': 'target'})}]}
        await self.bridge.action(body)
        self.assertEqual(self.store.inbox('target')[0]['state'], 'queued')
        body['user']['id'] = 'UTARGET12'
        await self.bridge.action(body)
        self.assertEqual(self.store.inbox('target')[0]['state'], 'acknowledged')
        with self.store.db() as db:
            db.execute('UPDATE agents SET worker_until=? WHERE id=?', (time.time()+100, 'target'))
        with self.assertRaises(ValueError):
            await self.bridge.post('target', {'to': ['owner'], 'text': 'wake next', 'wake': True, 'priority': 'critical'})

    async def test_commit_confirmation_requires_local_revision_evidence(self):
        payload = {'text': 'pull docs', 'channel': 'C1', 'thread': '111', 'required_commit': '123abcd'}
        self.store.ingest('revision-task', payload, ['target'])
        self.store.put('task:revision-task', payload)
        response = await self.client.post('/receipt', headers=self.headers,
            json={'id': 'revision-task', 'state': 'acknowledged'})
        self.assertEqual(response.status, 409)
        self.assertEqual(self.store.inbox('target')[0]['state'], 'queued')

    async def test_missing_rollout_confirmation_tags_kian_once(self):
        self.bridge.api = AsyncMock(return_value={'ok': True, 'ts': '111'})
        self.store.put('rollout', {'commit':'a'*7, 'agents':['missing'], 'created':time.time()-400,
            'deadline':time.time()-1, 'channel':'C1', 'ts':'111', 'text':'Pull required', 'escalated':False})
        await self.bridge.refresh_rollout()
        await self.bridge.refresh_rollout()
        posts=[c for c in self.bridge.api.call_args_list if c.args[0]=='chat.postMessage']
        self.assertEqual(len(posts),1)
        self.assertIn('<@U0CFWEEL76V>',posts[0].kwargs['text'])

    async def test_confirmed_rollout_does_not_escalate(self):
        self.bridge.api = AsyncMock(return_value={'ok': True, 'ts': '111'})
        started=time.time()-10
        self.store.put('rollout', {'commit':'a'*7, 'agents':['target'], 'created':started,
            'deadline':time.time()-1, 'channel':'C1', 'ts':'111', 'text':'Pull required', 'escalated':False})
        self.store.put('ready:target', {'commit':'a'*7,'confirmed_at':time.time(),'runtime':'codex'})
        await self.bridge.refresh_rollout()
        self.assertFalse(any(c.args[0]=='chat.postMessage' for c in self.bridge.api.call_args_list))


if __name__ == '__main__':
    unittest.main()

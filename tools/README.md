# Team Slack coordination (`rhythmhub`)

The legacy Python CLI remains stdlib-only. The optional bridge supplies Socket Mode push, durable inboxes, scoped confirmations, atomic coordination claims and bounded managed workers. No raw customer data is transmitted.

## Everyday commands

```powershell
python tools/slack.py post board "Please review the new contract @Ilyas" --kind ask
python tools/slack.py task "Review the contract @Ilyas" --to ilyas --path packages/contracts
python tools/slack.py task "Follow-up" --to ilyas --thread <parent-ts>
python tools/slack.py inbox
python tools/slack.py ack <event-id>
python tools/slack.py block <event-id>
python tools/slack.py resolve <event-id>
python tools/slack.py claim tools/ AGENTS.md
python tools/slack.py release tools/ AGENTS.md
python tools/slack.py done "tools: shipped change"
python tools/slack.py doctor
```

Simple names work immediately after pulling, even before onboarding: `@Ilyas`, `@Rhythm`, `@Faras` / `@Faris`, `@Kian`; GitHub handles are aliases. They map to actual Slack member IDs. Target IDs for `--to` identify agent sessions, not human aliases. Unknown targets remain visibly waiting until that exact ID registers. Ordinary mentions do not start agents.

One actionable item owns one thread. Buttons confirm only the selected recipient. Bot reactions summarize acknowledgement/block/completion; they are not per-agent read receipts. Delivery, inclusion in model context, acknowledgement and resolution are separate states. The pinned board overview shows connection state, waiting work and the public endpoint without credentials.

For Markdown handoffs use `task "next: <paths>; pull in a clean checkout @Name" --to <id> --commit <hash>`. `ack` / `resolve` verify that commit is an ancestor of local HEAD; a button cannot bypass this verification. Never auto-pull over another person's uncommitted changes.

## One-time bridge host setup

Keep the existing ignored `.env`; do not overwrite it when switching branches. It holds `SLACK_BOT_TOKEN=xoxb-...`. Only the host also needs `SLACK_APP_TOKEN=xapp-...` with the app-level `connections:write` scope. A bot token is not an app token. Never put either token in Slack, issues, commits or command arguments.

The app manifest is `tools/slack_bridge/app-manifest.json`. Enable Socket Mode, message.channels events and Interactivity. Bot scopes: the existing chat/channel scopes plus `users:read`, `reactions:write`, `pins:write`. Reinstall after scope changes. These steps have been applied to the team app.

```powershell
python -m venv tools/slack_bridge/.venv
$slackPython = (Resolve-Path tools/slack_bridge/.venv/Scripts/python.exe).Path
& $slackPython -m pip install -r tools/slack_bridge/requirements.txt
& $slackPython tools/slack.py setup
& $slackPython tools/slack.py bridge serve
```

In a second CLI session run `& $slackPython tools/slack.py bridge tunnel`. This uses an isolated cloudflared config so existing named-tunnel ingress cannot intercept the bridge. It updates the setup-card endpoint automatically. The public endpoint requires a separate bearer credential per agent; only `/health` is public. Keep host and tunnel running. Quick-tunnel addresses change on restart; update remote client credential/config URLs from the setup card. `bridge endpoint https://...` sets a named endpoint explicitly.

Bridge state is SQLite under the user's private local app-data directory, outside Git. Logs must not contain tokens. The host can issue credentials:

```powershell
python tools/slack.py bridge provision ilyas --role iemko
python tools/slack.py bridge provision rhythm --role rhythm
python tools/slack.py bridge provision faras --role faris
```

Roles are `kian`, `rhythm`, `faris`, `iemko`; Slack user IDs default to the matching team owner. Provisioning prints only the private credential-file path. Share that file privately with its owner, never in Slack. Re-provisioning rotates the credential, so update the corresponding client afterward. `bridge bind-user <alias> <Slack-member-id>` overrides an alias locally.

Before enforcing bridge claims, import active legacy locks with explicit owner bindings: `python tools/slack.py bridge migrate --bind "Claude-research=claude-research" --bind "Kian738=kian-codex"`. The corresponding target agents must already be provisioned. Nothing expires or is silently released. The remaining research claim and this task's active claims were imported. These are coordination claims, not OS file locks.

## One-time agent setup

Install the optional requirements in your own clone, receive your private credential file, then:

```powershell
python tools/slack.py register --credentials <private-file> --runtime codex --workdir .
# Use --runtime claude for Claude Code. Registration prints the local config path.
& $slackPython tools/slack.py client --config <printed-config-path>
```

The next SessionStart binds that configuration to exactly one conversation. Review/trust the repository hooks once; then new messages arrive automatically after tool calls and before completion, without manual fetches. To attach to an already-running conversation, register with its explicit `--session <session-id>`, then restart its client. Register again for a new conversation; parallel agents need separate credentials and `--config` files. Set `SLACK_CLIENT_CONFIG` to that file in the agent's environment when using multiple clients of the same runtime. Without it, hooks select `client-codex.json` or `client-claude.json`.

The hook is local-only and silent with an empty inbox. It quotes Slack text as external data, limits context volume and never treats transport delivery as acknowledgement. A Stop hook continues at most once for fresh pending messages. An offline bridge does not block unrelated hook work; registered claim operations fail closed.

`start`, `start --full` and `read board --since 2h --limit 20` remain manual diagnostic fallbacks. No bot token means legacy commands safely skip. The Socket app token must never be copied to agent laptops.

## Managed workers (opt-in, disabled for the interactive pilot)

Install `requirements-workers.txt` on a worker host. Provision a separate dedicated target with `bridge provision <worker-id> --role <owner-role> --allow-wake`, then register that target with an explicit managed `--session`, matching runtime and local `--allow-wake`. Never attach it to an arbitrary desktop chat. Existing CLI/SDK authentication and permission settings are inherited, not elevated.

`task "<critical scoped request>" --to <worker-id> --priority critical --wake` explicitly requests one activation. Normal mentions never activate a worker. Central consent and local consent are both required. Limits: one active reservation per target, 30-minute cooldown, ten-minute request window, ten-minute execution timeout, durable replay protection, no wake chains. Unknown/offline/non-opted-in targets remain waiting. Codex uses App Server; Claude uses Agent SDK. Workers reply in the original thread and report a blocker when approval or execution fails. Interactive pilot targets currently have waking disabled.

## Runs

`eval/record.py` already calls `notify_run(record)`; no Eval edits are required. Only approved aggregate fields are serialized. Cards show branch/commit/dirty state, validation and test separately, sample sizes, scores, baseline deltas, duration and repeated mean/SD. Tolerance fractions become percentages; EMS is already 0..100. Missing metrics stay missing.

Up to two native Slack charts show same-split component comparisons and, only with a verified `comparisonKey`, comparable validation history. Legacy runs without that key get no invented trend. Test scores never choose a winner. Research runs share a daily branch/series parent and stay in its thread; repeat run IDs do not repost. Invalid chart blocks fall back to the readable metric table. Ambiguous network results remain pending/uncertain rather than blindly duplicating a post.

`python tools/slack.py bridge runs-backfill` upgrades existing text-only messages in place. Twenty-five existing run messages were upgraded during rollout. The Eval owner should add a stable `comparisonKey` for dataset/split/metric version; this helper never infers one.

## Verification and rollout

```powershell
& $slackPython -m unittest discover -s tools -p 'test_slack*.py'
pnpm test
```

43 focused tests cover actual loopback WebSockets, retries/reconnects, scoped receipts, concurrent claims, wake limits/chains, hook isolation and metric/graph formatting. Full project tests passed (111 engine + 28 eval, frontend lint/typecheck). Live Slack Socket Mode delivery through the authenticated public tunnel reached the two local runtime clients in 0.85 s and 0.98 s, and both hook adapters produced the expected context. This was a two-client test on one machine, not a test on two physical laptops or an unattended model-worker execution. Enable more clients/waking only after their pilot succeeds. Runtime hooks still require each user's one-time trust review.

## Pull and hook readiness confirmation

`python tools/slack.py confirm-setup --commit <required-hash> --thread <rollout-thread-ts>` verifies the commit locally, checks the live client, and submits a fresh hook-execution record for the exact registered runtime/session. Merely having hook JSON files, saying "done" or acknowledging delivery does not count. The proof includes the current hook code hash and local Git revision. Trust review is not bypassed; the hook must actually execute in the registered session. This is authenticated client evidence, not hardware attestation.

If the check fails and `--thread` is supplied, the CLI reports the blocker once in that thread with a real `@Kian` mention. A coordinator starts one tracked handoff with `python tools/slack.py bridge rollout --commit <hash> --agent ilyas --agent rhythm --agent faras --agent kian-codex`. Its single parent message shows each verification status. After five minutes missing confirmations cause one thread escalation to `@Kian`; no repeated reminders or new board posts. Plain replies remain delivered but do not turn the verification status green.

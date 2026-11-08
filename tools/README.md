# tools/slack.py — Slack board setup (≈3 min)

1. Create a free workspace at slack.com/get-started#/createnew (skip if you have one).
2. api.slack.com/apps → Create New App → **From a manifest** → pick the workspace → paste `tools/slack-manifest.yaml` → Create.
3. Install App → Install to Workspace → copy the **Bot User OAuth Token** (`xoxb-…`).
4. `cp .env.example .env` and set `SLACK_BOT_TOKEN=xoxb-…` (`.env` is gitignored; never commit or paste it in chat).
5. `python tools/slack.py setup` creates `#board #engine #web #eval #pitch #runs` and the bot joins them.
6. Invite teammates in Slack; each teammate puts the same token in their own `.env` (share privately, not in git).
7. Test: `python tools/slack.py post board "hello"`.
8. Read: `python tools/slack.py read board --since 2h --limit 20`.
9. No token → the script prints a note and exits 0, so it is safe in scripts.
10. From Python: `from tools.slack import notify_run; notify_run({"wholeDesign": 71.2})` posts to `#runs`.

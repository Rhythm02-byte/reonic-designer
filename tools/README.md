# tools/slack.py — Slack board (workspace `rhythmhub`)

1. Ask Kian for the bot token (`xoxb-…`). Never commit it or paste it in chat.
2. `cp .env.example .env` and set `SLACK_BOT_TOKEN=xoxb-…` (`.env` is gitignored).
3. Join the Slack workspace; the channels `#board #engine #web #eval #pitch #runs #changelog` are already there (Browse channels if not in your sidebar).
4. Task start: `python tools/slack.py start`. Post: `post board "<text>" --kind done|blocked|ask|decision|contract`.
5. Locks: `claim <folder>` / `release <folder>`. Finish: `done "<change>"`. Raw read: `read board --since 2h`.
6. Changelog: post one line per shipped change to `#changelog`; only Kian's agent edits `docs/BACKLOG.md` from it (no write races).
7. No token → the script prints a note and exits 0, so it is safe in scripts.
8. From Python: `from tools.slack import notify_run; notify_run({"wholeDesign": 71.2})` posts to `#runs`.
9. `python tools/slack.py setup` is idempotent: creates missing channels and joins the bot.
10. Needs only Python 3.10+. Posts show as "<Name>'s agent" with a colour icon (set your name via `SLACK_AGENT` or git user.name).

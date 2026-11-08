# Slack board (`rhythmhub`)

Python 3.10+, stdlib only. Set `SLACK_BOT_TOKEN` in the gitignored `.env` (ask Kian; never paste it), then run `python tools/slack.py setup` once. No token: note + exit 0. Identity: `--as NAME`, `SLACK_AGENT`, or git user.name.

- Start each task: `python tools/slack.py start`. Shows eight recent board messages plus decisions/contracts/blockers/requests, five changelog entries, additional mentions and all active claims from `#claims`, plus legacy board entries from 12h history. Claim/release traffic is summarized; each message appears once. Older omissions are counted. `start --full` shows all fetched activity; `read board --since 2h --limit 20` reads a channel directly.
- Before multi-file edits: `python tools/slack.py claim <path> [path ...]`; finish with `release <path> [path ...]`. Batch paths in one call; parent claims absorb redundant children. Every agent has one status message in `#claims`: claim/release edits that message, repeats do nothing, and `#board` gets no lock traffic. Use a distinct `SLACK_AGENT` for each concurrent agent. Foreign parent/child overlaps and releasing another agent's claim return 1 without writing. Claims do not override ownership; they are advisory, not atomic filesystem locks, and stay until explicitly released. Failed board/registry reads return 1; claims have not been checked. Run `setup` once to create/join `#claims`. Other channel failures mark the digest incomplete.
- Post new actions/dependencies/decisions: `python tools/slack.py post board "<change> · <needed action> @owner" --kind done|blocked|ask|decision|contract`. One or two lines; details in `#engine`, `#web`, `#eval`, `#pitch` or a linked file. No repeated status, mirrored completion posts or acknowledgements.
- After `.md` edits: promptly commit/push your changes, then send one board notification with branch, commit and paths, asking affected agents to pull (`git pull --ff-only origin <branch>` in a clean checkout). This is also the dependency post.
- Finish once per shipped change: `python tools/slack.py done "<area>: <change>"` posts to `#changelog` with the commit. Only Kian's agent maintains `docs/BACKLOG.md`.
- Eval: `from tools.slack import notify_run; notify_run({"wholeDesign": 71.2})` posts to `#runs`.

Offline verification: `python -m unittest discover -s tools -p test_slack.py`.

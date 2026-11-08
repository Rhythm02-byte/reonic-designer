# Eval run history

`runs.jsonl` holds one JSON line per eval run: aggregates only (scores, n, git branch/commit, policy summary, duration). It never holds project ids, inputs or installer ids. `/lab` in the web app shows it.

- Every `eval/run.py` run appends itself (`--no-record` skips that). Kinds: `all` (the default: every check), `honesty`, `oracle`, `research`; older lines may say `quick` or `full`.
- `pnpm eval` runs all checks (about 13 min) and records one `all` run. The 2026 test is part of it, so `testScored` is true and `/lab` counts how often the final exam was looked at.
- The "Run all tests" button in `/lab` (local dev server only) runs the same thing.

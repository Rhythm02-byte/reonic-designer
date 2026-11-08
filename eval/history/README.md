# Eval run history

`runs.jsonl` holds one JSON line per eval run: aggregates only (scores, n, git branch/commit, policy summary, duration). It never holds project ids, inputs or installer ids. `/lab` in the web app shows it.

- Every `eval/run.py` run appends itself (`--no-record` skips that). Kinds: `quick`, `full`, `honesty`, `oracle`, `research`.
- `npm run eval:quick` gives the validation window plus 5 repeated splits in about 25 s. Add `-- --test` to also score the 2026 test; `testScored` marks that, and `/lab` counts it.
- `npm run eval:record` re-records `eval/results/latest.json` by hand.
- The "Run fast test" button in `/lab` (local dev server only) runs `--quick`.

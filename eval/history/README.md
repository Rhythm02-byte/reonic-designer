# Evaluation history

Run `npm run eval`, then `npm run eval:record` from the repository root.
For the first point, `npm run lab:seed` records the current `eval/results/latest.json` without rerunning evaluation. Both commands append a real record; neither invents historical points. Commit `runs.jsonl` alongside the corresponding branch changes. Recording is explicit because the evaluator and existing eval script belong to another owner.

Open `/lab`. The page reads this aggregate-only file on the server, without engine calls. Missing history shows an empty state; malformed lines are counted and skipped with a warning. Keep this file in production deployments to retain history. The loader walks upward from the web working directory, including on Windows.

Scores are EMS points (0–100), tolerance rates are fractions (0–1), and latency is milliseconds. `durationSec` is total evaluation duration, never inferred from prediction latency. Missing values remain null. The timestamp is report generation time. Git branch/commit/dirty describe recording time; record promptly after evaluation. Outside a Git checkout these are `local`, null and false.

The current policy file is snapshotted separately from `selection.config`, the config actually selected in the report. If engine changes occurred since evaluation, these can differ. Only allowlisted aggregate score fields are extracted; no project rows, installer identifiers, inputs or per-project predictions are retained. LOIO splits with installer identifiers in their names are omitted.

Engine field requests: `durationSec`, `engineVersion`, selected-model `latencyP50ms` and `latencyP95ms`, and optional `honesty.shuffledLabel` (`ems`, `passed`), `honesty.repeatedSplit` (`mean`, `sd`, `n`) and `honesty.fuzz` (`passed`, `total`). No missing evidence is invented. Frontend integration request: root-level `g l` / planner `?lab=1` hooks, outside this task's ownership.

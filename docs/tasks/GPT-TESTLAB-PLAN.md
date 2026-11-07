# Test Lab implementation plan

1. Read the evaluation schema and design rules; keep all changes within the task's explicit ownership list, plus its requested recorder test.
2. Build a standard-library Python recorder that allowlists aggregate metrics, captures Git provenance and policy config, and appends one JSONL record. Seed only from the real latest report. Unknown duration/version remain null.
3. Read history in the `/lab` server component by walking ancestors from the working directory. Build a client view with a branch timeline, accessible data tables, run details, latest comparison, optional honesty/oracle evidence, and two-run deltas.
4. Use plain SVG and scoped CSS with the paper/ink design tokens. No new dependencies.
5. Run the synthetic recorder tests, seed history, lint and build the web app. Inspect the rendered page if a browser is available.

## Scope constraints and integration requests

- Global `g l` and planner `?lab=1` entry points require a root layout/planner change outside the authorized paths. Request those hooks from the frontend owner; `/lab` itself remains unlinked.
- The task explicitly requests `eval/test_record.py`, treated as an exception to the create/edit list.
- Do not change `eval/run.py` or the existing `eval` script. `eval:record` is a separate post-evaluation command; `lab:seed` records the current report.
- No Git repository is present in this checkout, so Git metadata falls back to `local` / null. Board coordination is unavailable here.
- The current report has no duration, engine version or honesty block. Show missing values honestly; never substitute inference latency for evaluation duration.
- Snapshot the current policy file as requested, and separately retain the report's chosen config: concurrent engine work can make those differ.

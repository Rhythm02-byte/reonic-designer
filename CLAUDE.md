@AGENTS.md

## For Claude agents
- CodeGraph first: this repo has a `.codegraph/` index. Before Grep/Read, call `codegraph_explore` with projectPath = repo root (or run `codegraph explore "<symbols>"`). Don't re-read files it already showed you.
- Keep reports short (≤150 words unless asked) and state what you did NOT verify.
- The four commands: `pnpm bootstrap`, `pnpm dev`, `pnpm test`, `pnpm eval` (see README). Use pnpm, never npm.

- Slack: follow AGENTS.md. The project hooks deliver new inbox items automatically once your client is registered and running; use real @names via the helper, keep replies in the original thread, and explicitly ack/block/resolve addressed work. See tools/README.md for one-time setup.

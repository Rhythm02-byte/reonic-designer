@AGENTS.md

## For Claude agents
- CodeGraph first: this repo has a `.codegraph/` index. Before Grep/Read, call `codegraph_explore` with projectPath = repo root (or run `codegraph explore "<symbols>"`). Don't re-read files it already showed you.
- Keep reports short (≤150 words unless asked) and state what you did NOT verify.
- The four commands: `pnpm bootstrap`, `pnpm dev`, `pnpm test`, `pnpm eval` (see README). Use pnpm, never npm.

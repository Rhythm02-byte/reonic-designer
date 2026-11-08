# Docs index (read in this order)

| File | What | Keep current? |
|---|---|---|
| [../README.md](../README.md) | For evaluators and new teammates: what, results, how it works, the four commands | yes |
| [../AGENTS.md](../AGENTS.md) | Owners, hard rules, Slack board, CodeGraph (Claude agents also get `../CLAUDE.md`) | yes |
| [BACKLOG.md](BACKLOG.md) | Every task with status: **the** to-do list | yes |
| [PITCH.md](PITCH.md) | All pitch numbers for OUR engine, with what they were measured on | yes |
| [DESIGN.md](DESIGN.md) / [PRODUCT.md](PRODUCT.md) | Faris's design system (source of truth) + our additions; users and principles | yes |
| [demo-script.md](demo-script.md), [business-case.md](business-case.md), [submission-checklist.md](submission-checklist.md), [pitch/](pitch/) | Rhythm's demo script, business case, checklist and 7-slide deck draft. **Numbers in these come from Rhythm's earlier engine (random/out-of-fold splits); reconcile with PITCH.md before presenting** | until pitch |
| [rhythm-work-log.md](rhythm-work-log.md), [specs/](specs/), [figures/](figures/) | Rhythm's work log, feature specs, deviation chart | reference |
| [tasks/](tasks/) | Self-contained prompts for other agents (Codex: CODEX-ORCHESTRATOR, GPT-EXTERNAL-DATA) | per task |
| [../PLAN.md](../PLAN.md) | Full plan + research synthesis (long; reference only) | rarely |
| `../research/` | Evidence: data findings, workflow, battery/sim, source check, model selection, experiments protocol, external reports | append only |

Rule: new docs go into `tasks/` (prompts) or `research/` (evidence). Anything else updates BACKLOG or PITCH instead of adding a file.

# Backlog (everything asked for, with status)

Status: ✅ done · 🟡 in progress · ⬜ open · ✂️ cut (with reason). Owners per AGENTS.md. Update when you finish something.

## Research & understanding
| Item | Status | Where |
|---|---|---|
| Read the challenge, roadmap | ✅ | PLAN.md |
| Dataset structure, traps, hidden signals, correlations | ✅ | PLAN §2, research/data-correlations.md |
| Reonic product + docs analysis (no public code found) | ✅ | PLAN §5.1 |
| Competitors (Aurora, OpenSolar, autarc, Zolar, Otovo…) | ✅ (deeper UX teardown = external R1) | PLAN §5.2, research/external |
| Installer daily workflow, pains | ✅ | research/installer-workflow.md |
| Battery sizing state of the art, EV, tariffs, aging | ✅ | research/battery-and-simulations.md |
| Stakeholder wants/needs/fears | ✅ | PLAN §4 |
| Source fact-check (no hallucinated studies) | ✅ | research/source-check.md |
| External model tasks R1–R9 + orchestrator prompt | ✅ prompts, R1–R6 results in / ⬜ reconcile into PLAN/PITCH | research/external/PROMPTS.md |
| Teammate findings preserved | ✅ | research/rhythm-findings.md |

## Engine
| Item | Status |
|---|---|
| ETL with unit fixes, column swap, roof type, trusted existing PV/storage | ✅ |
| Baselines B0/B0c/B1 | ✅ |
| Learned chain M1 (ported from Rhythm) + kNN + rules R01–R05 | ✅ |
| Engine default = validation-selected composite model | ✅ |
| Validation-based model selection (no test peeking) | ✅ research/model-selection.md |
| Hourly simulator S1–S5 (PV, load, battery, EV, HP, 20y €) | ✅ |
| Simulator metrics + "why this size" curves + R06 physics flag in /design | ✅ |
| /meta, /simulate, /validate, /eval/summary, /holdout | ✅ |
| **Ask-next (value of information)** + oracle experiment in eval | ✅ (EV planned-year question open) |
| BOM generator (installer line-item templates, Reonic CSV export) | ⬜ |
| Simulator upgrades U1 load variety, U2 forecast dispatch / negative prices | ⬜ |
| Conformal calibration of size ranges | ✅ |
| Simulator features inside M1 | ✅ |
| Claude Haiku: explanation phrasing + ⌘K intent → JSON patch (grounded, fallback) | ⬜ |
| Homeowner Q&A assistant with tools (stretch) | ⬜ |
| Product library with market price ranges (seeded from history + config/market.json) | ⬜ (data in config, UI open) |

## Frontend (Next.js, Faris's base, Reonic-style DESIGN.md)
| Item | Status |
|---|---|
| Port planner + offer + 3D house onto our engine | ✅ live end-to-end |
| Lock pins, diff bar + undo, range hints, provenance hints, flags | ✅ |
| Offer page: variants within planner limits, battery curve, QR share | ✅ (verify 'Your choice' card updates) |
| Reality check card (expert vs ours, held-out) | ✅ |
| `/eval` page | ✂️ replaced by hidden `/lab` (docs/tasks/GPT-TESTLAB.md, Codex); delete `/eval` + EvalReport once `/lab` lands |
| Mobile layout, ≥44 px targets, haptics (web-haptics) | 🟡 / ⬜ |
| House types (gable/hip/flat/shed) | ✂️ for now: one Blender house; roof type shown in text. Revisit if time |
| Product library UI | ⬜ |

## Testing & quality
| Item | Status |
|---|---|
| Unit tests (ETL, rules, policy, simulator) | ✅ 103 passing (port agent adding more) |
| Eval harness: temporal, random, leave-one-installer-out, sensitivity, robustness | ✅ |
| Validation split for selection | ✅ |
| API smoke + latency tests | 🟡 |
| E2E (Playwright: intake → design → change → share link on mobile) | ⬜ (iemko) |
| External UX review / bug hunt / chat red-team (R7–R9) | ⬜ after app runs |

## Delivery
| Item | Status |
|---|---|
| Pitch notes | 🟡 docs/PITCH.md |
| Deck | ⬜ |
| README (setup, approach, limitations) | 🟡 |
| Deployment for QR demo (Vercel + engine host or tunnel) | ⬜ |
| Fallback demo recording | ⬜ |
| Ask Reonic the §17 questions (signed option, build-year meaning, hours per design) | ⬜ |
| Agent board (pinned issue + tools/board) | ⬜ |
| Delete `_incoming/` after port is verified | ⬜ |
| Polish: reason text rounding (16.5 vs 16.7 kWp), duplicate Share button on mobile, UI for alternatives + typical day | ⬜ |

## Cleanup (after the port agent finishes; nobody edits designer.py meanwhile)
| Item | Status |
|---|---|
| Port Rhythm's coverage sizing + full battery catalogue + honesty checks behind the validation gate | 🟡 agent running |
| Collapse policy modes: keep `composite` as the only served mode; `learned`/`hybrid`/H1 stay only as eval candidates | ⬜ |
| Delete stale `docs/HANDOFF-CODEX.md`, `_incoming/`, `/eval` (after `/lab`) | ⬜ |
| Check unused schemas (`SharePolicy`, `BomLine` until BOM exists) | ⬜ |
| Make thinc a git repo → push as branch `next` to the team repo → rename to `main` once the team agrees | ⬜ your OK |

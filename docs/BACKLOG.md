# Backlog (everything asked for, with status)

Status: ✅ done · 🟡 in progress · ⬜ open · ✂️ cut (reason). Owner in brackets. Freeze **Sun 11:00**, submission **15:00**. Update when you finish something.

## A. Before freeze: demo-critical (in this order)
| Item | Status |
|---|---|
| Faris's frontend = source of truth in `apps/web` (sidebar, drafts, grouped inputs, system cards, whole-option offers) wired to our engine via an adapter `lib/api.ts`; our extras mounted with `// ours:` lines [Claude session] | ✅ |
| Faris pushes his unpushed work → re-copy his files (his components stay verbatim, so this takes minutes) [Faris] | ⬜ |
| Pitch mode `/pitch` (iemko) ported onto Faris's planner; logo 3× → menu: Pitch mode · Pitch offline (`?demo=1`) · Lab results. iemko: re-check slide numbers vs `docs/PITCH.md` (latency p95 slide) [iemko] | ✅ |
| Parts list visible in planner (+ offer): modules ×N, inverter, battery, wallbox, heat pump, service lines | ✅ |
| QR code for the homeowner link | ✅ |
| Make `next` the team's main: Faris + iemko pushed, team agrees, rename on GitHub (needs repo admin: Rhythm) [Kian] | ⬜ |
| Deploy: Cloudflare quick tunnel to `pnpm dev` (one URL, no account) **or** Vercel + hosted engine; decide by 09:00. Through the tunnel, `/engine/holdout` and `/lab/run` answer 403 (`apps/web/proxy.ts`), so real projects stay on the presenter's laptop [Kian] | ⬜ |
| Deck: Rhythm's 7-slide draft (`docs/pitch/`) with numbers from `docs/PITCH.md` (his use his older engine) [Kian/Rhythm] | ⬜ |
| Fallback screen recording of the demo [iemko] | ⬜ |

## B. Before freeze: if time (each needs a demo reason)
| Item | Status |
|---|---|
| Haiku: bill photo → annual kWh (strict JSON); the measured +9.8 pts lever. Separate `/plan` [Claude] | ⬜ |
| Haiku: grounded co-pilot (intent "EV next year" → input patch; homeowner Q&A with tool calls to our endpoints), template fallback without key [Claude] | ⬜ |
| Metric research phase under `research/experiments.md` protocol (bundle classification, catalogue-as-classes, TabPFN, recency, …) [Claude agents] | ⬜ |
| Codex night shift: external data pack + blind-spot sweep (`docs/tasks/CODEX-ORCHESTRATOR.md`) [Codex] | ⬜ hand to Codex |
| Slack board live: paste the `thinc-board` bot token into `.env` [Kian] | 🟡 |
| Reconcile ChatGPT research R1–R6 + `COMPATIBILITY.md` (verified pairings vs implemented, keep UNVERIFIED) into PLAN/PITCH [Kian] | ⬜ |
| Mobile haptics (web-haptics; Faris's UI dropped it) [web] | ⬜ |
| Ask Reonic mentors on site: signed option, build-year meaning, hours per design (PLAN §17) [Kian] | ⬜ |
| E2E smoke (Playwright: intake → design → set size → share → offer on mobile) [iemko] | ⬜ |
| From Rhythm's main (good work, other layout): model artifact freshness signature (warn when code changed since training) and a Docker compose for `next` [Rhythm] | ⬜ |
| Real roof view: Google Maps 3D / Photorealistic 3D Tiles at the address as the primary map where panels are placed; the Blender house stays as the fallback when no coverage or no key [Faris] | ⬜ |

## C. Known bugs / polish (re-check after the Faris integration)
| Item | Status |
|---|---|
| Reason text rounding (16.5 vs 16.7 kWp) | ⬜ recheck |
| Duplicate Share button on mobile | ⬜ recheck (may be gone with Faris's UI) |
| Offer page counted panels as kWp ÷ 450 W (23) while the planner said 22 (463 Wp modules): the link now carries the module watts | ✅ |
| A locked part showed "Experts pick 20 kWh" (its own value as the range): no range while locked | ✅ |
| Offer "Your choice" card updates when the homeowner changes an option | ⬜ recheck |
| Typical-day chart + alternatives (engine returns them; no UI in Faris's design yet) | ⬜ |
| Engine `/design` p50 ~0.35–0.5 s under load (was 92 ms before battery coverage sizing; per-row pandas features ~60 ms) | ⬜ optimise if time |

## D. Done (highlights)
- **Research:** data structure, unit traps, correlations, installer workflow, battery and simulation state of the art, competitors, source fact-check, ChatGPT R1–R6 reports in `research/external/`.
- **Engine:**
  - ETL with unit fixes
  - baselines
  - learned chain + kNN + rules R01–R07
  - validation-selected composite (+ battery coverage sizing)
  - conformal ranges
  - hourly simulator
  - Ask next
  - API
  - parts list (modules, inverter, storage, wallbox, heat pump, services)
- **Quality:**
  - 111 engine tests
  - honesty checks (shuffled labels, 20 splits, 2,000-home fuzz, which fixed 194 rule bugs)
  - `pnpm eval` = all checks, recorded per branch
  - `/lab` with one button and a presenter menu
- **Repo:**
  - `next` pushed
  - pnpm, with four commands (`bootstrap`, `dev`, `test`, `eval`)
  - cross-platform scripts
  - README for evaluators
  - CLAUDE.md → AGENTS.md
  - Slack script
  - Rhythm's deck, demo script, business case, work log and specs in `docs/`
  - unused `lightgbm` dropped

## E. Cut (and why)
- House types gable/hip/flat/shed: one Blender house; roof type shown in text.
- Simulator upgrades U1 (load variety), U2 (forecast dispatch / negative prices): no demo impact before freeze.
- Product library UI: price data stays in `services/engine/config/market.json`.
- Haiku choosing sizes / scoring Haiku on the private dataset: breaks hard rule 3 (LLM never sizes), and would send project data to a third-party API.

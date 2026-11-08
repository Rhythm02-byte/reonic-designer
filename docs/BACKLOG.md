# Backlog

Status: ✅ done · 🟡 in progress · ⬜ open · ✂️ cut (reason). Submission **Sun 8 Nov, 15:00**. Only Kian's agent edits this file.

## Open (today, before 15:00)
| Item | Status |
|---|---|
| Jury top 5: pinned Evidence project, slide 6 hint, Evidence headline wording, stale numbers in PITCH/slides, contradicting "similar homes" cards (`research/jury/final-review.md`) | 🟡 |
| Playwright E2E smoke of the demo path (`pnpm x:e2e`) | 🟡 |
| Real Google 3D mesh as the main house view, with our panels placed on its roof (local only) | 🟡 |
| Installer 2a8ba8e2 gets no PV at exactly 4,500 kWh (`demand_is_default`): decision A, louder flag, numbers unchanged [Rhythm] | ⬜ |
| Parts list mixes brands (inverter and battery from different makers); R06 battery flag fires even when the larger battery improves NPV [Rhythm] | ⬜ |
| Phone test of the homeowner link (QR) and a fallback screen recording [Kian/iemko] | ⬜ |
| Haiku where it earns points (not for bills): planned separately with `/plan` [Kian] | ⬜ |

## Done (highlights)
- **Engine:** ETL with unit fixes; baselines B0/B1; learned chain + kNN + rules R01–R07; battery sized from the installer's catalogue (research winner); conformal ranges; hourly simulator; Ask next; parts list; input plausibility warnings; QA fixes (negative roof cap → 422, metrics without new PV, kWp = modules × Wp, locked PV in installer modules, R03 after rounding); `/design` ~130 ms warm.
- **Evaluation:** 2026 test (n = 325) recorded in `eval/results/latest.json`; 4 quarterly folds + 20 splits; shuffled-label control; oracle upper bounds; selective prediction; research tournament with pre-registered adoption rule (`research/experiments.md`).
- **Web:** Faris's planner (sidebar, drafts, undo, grouped inputs, system cards); one Share control with QR; homeowner `/offer`; `/pitch` deck with live planner and offline mode; `/lab`; `/new-customer`; custom dropdown, checkbox and radio; initials avatars; tunnel guard (`apps/web/proxy.ts`); real-house mesh import.
- **Repo:** `next` is the team's main; pnpm with `bootstrap`, `dev`, `test`, `eval`; README for evaluators; AGENTS.md with bad habits.

## Cut (and why)
- Haiku reading the electricity bill: data is collected before the planner, not from the homeowner.
- Haiku choosing sizes in the served engine: AGENTS rule 3 (LLM never sizes).
- Slack coordination: the team stopped using it.
- House types gable/hip/flat/shed: the real mesh replaces them; the stylised house stays as the fallback.
- Simulator upgrades (load variety, forecast dispatch, per-location weather): no demo impact today; the simulator uses one PVGIS site, which understates Bavarian savings but does not change sizing.

# Demo script (under 5 minutes, run from `/pitch`)

The deck *is* the app: `/pitch` shows the slides and, on slides 5 and 6, the real planner and homeowner page in place. Speaker notes per slide: press **N** in `/pitch`, with a timer. Timings add up to 220 s, leaving time for questions.

## Before you start (T-30 min)
- [ ] `pnpm dev` is running (engine :8000 + web :3000), and `pnpm x:train` was run after the last engine change. The served model learns from offers ≤ 2025-12-31, so the 2026 projects in Evidence are unseen.
- [ ] Open `http://localhost:3000/pitch` in full screen (**F**). Or tap the logo three times → *Pitch mode*.
- [ ] Offline fallback: logo ×3 → *Pitch mode, offline* (`/pitch?demo=1`): labelled toy numbers, no engine.
- [ ] Phone: if the homeowner link should open on the jury's phones, run a tunnel (`cloudflared tunnel --url http://localhost:3000`) and test the QR once. Real projects and the test runner stay local through the tunnel (`apps/web/proxy.ts`).
- [ ] The fallback screen recording is on the laptop (not in the repo).
- [ ] Clear old planner drafts: open the planner once and reload, so it starts from "Familie Berger".

## The run (→ / PageDown / presenter remote steps through everything)
| Slide | Time | What happens / what to say |
|---|---|---|
| 1 Hook | 10 s | "A family waits 8.2 days for an offer." (median, installer 1; elapsed time, not effort) |
| 2 Problem | 20 s | Near-identical homes get 5.4–12.6 kWp from experts: roof and budget aren't in the data. "Just predict it" can't work. |
| 3 Turn | 15 s | "So we built a designer that knows what it doesn't know, and asks." |
| 4 How | 15 s | Home facts → learned installer habits + hourly simulation → design with ranges → the next question. No LLM sizes anything. |
| 5 Live planner | 90 s | New request → Ask next → answer 5,200 kWh (diff bar) → EV next year (wallbox) → planner forces 20 kWh battery (warnings) → Evidence: a 2026 project the model never saw. If the engine fails: press **D** (offline demo data). |
| 6 Homeowner link | 20 s | Share → QR → the plain homeowner view; switch one option. |
| 7 Proof | 20 s | 2026 test: **solar +17 pts** vs the installer's own habit; whole design 22.2 vs 20.6% (**on par, within noise**); roof question worth up to +11 pts (upper bound). |
| 8 Value | 20 s | Planner, installer, homeowner. Hours saved: ask Reonic. |
| 9 Close | 10 s | "Great planners don't guess. They ask." · Rhythm and his dancers |

## If something breaks
- Engine down → the planner says "Running on synthetic data". Switch to `/pitch?demo=1` (D key) and say so.
- Slow first design → wait for "Updating design…"; never click twice.
- Page frozen → reload the browser (the slide number is in the URL: `#5.3` = slide 5, step 3).

## Honest answers to have ready
See `docs/PITCH.md` §10 and `research/jury/questions.md`. In short:
- "Whole design ties the installer's habit; PV is where we win."
- "The 2026 test was never used to choose; every look at it is counted in `/lab`."
- "With a stricter ±1-module PV tolerance, the habit wins: we report that too."

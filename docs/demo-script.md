# Demo script (under 5 minutes, run from `/pitch`)

The deck *is* the app: `/pitch` shows the slides and, on slides 5 and 6, the real planner and homeowner page in place. Speaker notes per slide: press **N** in `/pitch`, with a timer. Timings add up to 280 s and leave 20 s spare.

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
| 1 Cover | 10 s | One sentence: designs like your best planner, and says what it doesn't know. |
| 2 Problem | 20 s | 8.2 days median from request to offer at installer 1: **elapsed time, not effort**. |
| 3 Data | 20 s | We rebuilt every size from parts lists; near-identical homes get 5.4–12.6 kWp, because roof and budget are missing. |
| 4 How | 20 s | Learned policy + similar homes → hourly simulation → rules and catalogue → design with ranges, reasons, flags, next question. No LLM sizes anything. |
| 5 Live planner | 90 s | **Step 1:** new request; consumption and roof unknown → "Ask the customer next". **Step 2:** answer 5,200 kWh → the diff bar says what moved. **Step 3:** EV next year → wallbox appears. **Step 4:** the planner forces a 20 kWh battery → R05/R06 warnings explain why that rarely pays. **Step 5:** Evidence → load a 2026 project → compare with the expert (the model never saw it). |
| 6 Homeowner link | 20 s | Plain words, only the options the planner allowed; switch one option. |
| 7 Proof | 25 s | 2026 projects: **PV +17 pts** vs the installer's own habit; **whole design a tie** (20.9 vs 20.6%). Say "tie". |
| 8 Win / tie | 15 s | PV depends on the home (model wins); battery follows the package (habit; the economic optimum is the second opinion). |
| 9 Ask next | 25 s | Answering the roof question: up to +12 pts (**upper bound**); real consumption instead of the placeholder: +9.8 pts. |
| 10 Value | 20 s | First draft in under a second; flags before the offer goes out; the homeowner link. Hours saved: ask Reonic. |
| 11 Limits | 15 s | Two installers; heat pumps are physics-led; parts list preliminary; next: roof and budget at intake. |

## If something breaks
- Engine down → the planner says "Running on synthetic data". Switch to `/pitch?demo=1` (D key) and say so.
- Slow first design → wait for "Updating design…"; never click twice.
- Page frozen → reload the browser (the slide number is in the URL: `#5.3` = slide 5, step 3).

## Honest answers to have ready
See `docs/PITCH.md` §10 and `research/jury/questions.md`. In short:
- "Whole design ties the installer's habit; PV is where we win."
- "The 2026 test was never used to choose; every look at it is counted in `/lab`."
- "With a stricter ±1-module PV tolerance, the habit wins: we report that too."

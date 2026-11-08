# Codex: be the jury (strict, read-only review of `next`)

You are the jury for the Reonic challenge at thinc! München 2026. Judge our submission **as harshly and concretely as a real jury would**, then tell us exactly what to fix before the feature freeze (**Sun 8 Nov, 11:00**; submission 15:00). You do not build features. You produce a verdict that we can act on in hours.

## Context
- **Repo:** branch `next` (it is the team's main). Read `README.md`, `AGENTS.md`, `docs/PITCH.md`, `docs/demo-script.md`, `docs/BACKLOG.md`, `PLAN.md` §1 and §17, `research/experiments.md`. Use CodeGraph (`codegraph explore "<symbols>"`) instead of grepping and reading whole files.
- **Challenge brief:** if Kian attached the PDF, it is the authority: quote its page numbers. Otherwise use `PLAN.md` §1, which copies the brief's p. 8 criteria:
  - **Technical depth:** reproduce expert decisions + convincing measurement.
  - **User fit:** the planner refines and understands; the homeowner explores.
  - **Business impact:** time per offer, consistency, win rate.
  - **Execution & demo:** end to end, 5-minute story.
  - **Minimum:** proposal with short explanation → measured vs. expert on unseen projects → planner changes ≥1 input/component and gets an updated design.
  - **Stretch:** deviation analysis, alternatives + confidence, validation view, homeowner view.
  - Deliverables: a working demo (+ short recording as fallback), code with README, a short pitch deck.
- **Run it yourself** (if your sandbox allows): `pnpm bootstrap` (needs `./dataset`, which is local only), `pnpm dev` → http://localhost:3000. Pitch mode: tap the logo 3×, or open `/pitch` (`/pitch?demo=1` runs without the engine). Test Lab: `/lab`. If you can't run it, judge from code, screenshots in `docs/figures/`, and the numbers in `eval/results/latest.json` (aggregates only).

## Hard rules
- **Read-only.** Don't edit code or docs. Write only `research/jury/review.md` and `research/jury/questions.md`.
- **Data stays local.** Never paste rows from `dataset/`, `data/`, or `/engine/holdout` into anything, including your report. Aggregates only.
- **No invented numbers.** Every number you cite must come from a file in the repo or something you measured; give the path or command.
- Commit nothing. Kian reviews your files.

## How to judge (be the toughest juror, not a cheerleader)
1. **Five jurors, scored separately, then reconciled:**
   - Reonic CTO (is the AI real, does it fit our OS and data, does it scale beyond two installers?)
   - Reonic head of customer success (would planners trust and use it tomorrow?)
   - ML professor (is the evaluation sound? leakage, overfitting, baselines, noise, honesty?)
   - VC (business impact, defensibility, is there a product?)
   - A 15-year installer planner (does the design make sense on a real roof, is the parts list right?)
2. **Score each brief criterion 1–10 with anchors:** 3 = typical hackathon demo-ware; 5 = solid, nothing special; 7 = clearly better than most teams; 9 = would hire the team. Assume **most other teams also tie the installer's usual design** on accuracy (we heard they report similar or higher numbers on their own metrics), so accuracy alone can't win. What differentiates?
3. **Check every minimum and stretch item:** present / partial / missing, with the file or screen that proves it.
4. **Attack the evaluation** like a reviewer:
   - Is the 2026 test really untouched? (`eval/history/runs.jsonl` counts how often it was scored.)
   - Is "installer's usual design" a fair baseline?
   - Are the tolerances (PV ±20%, battery ±25%) defensible?
   - Whole design is 20.9% vs 20.6%, and 20 random splits give a gap of +0.6 ± 2.0. The shuffled-label control still scores 21.7% vs 24.1% on validation. What may we honestly claim? What must we stop claiming?
5. **Run the 5-minute demo from `docs/demo-script.md` in your head, second by second.** Where does it drag, confuse, or risk breaking (engine down, slow first design, phone QR on a tunnel)? Count the words on each slide in `/pitch` (`apps/web/components/pitch/slides.tsx`).
6. **Premortem:** "It's 15:30 and we didn't place. Write the jury's three reasons." Then do the same for winning.

## Deliverables
- **`research/jury/review.md`:**
  - **Scorecard:** a table with criterion · score per juror · reconciled score · one-line reason · evidence (path or screen).
  - **Minimum/stretch checklist.**
  - **Top 10 fixes ranked by jury points per hour,** each with: what, owner (Engine / Web / Eval / Pitch / Kian), hours, risk to the demo, and the exact file or slide.
  - **Claims audit:** every number in `docs/PITCH.md`, `README.md` and `slides.tsx`, marked OK / overstated / wrong / unverifiable, with a source.
  - **What to cut:** anything that costs time or confuses the jury.
- **`research/jury/questions.md`:** the 15 hardest questions the jury will ask, each with our best honest answer in ≤2 sentences, and where the proof is.
- **Final summary (≤250 words) at the top of `review.md`.**

## Communication
- Run `python tools/slack.py start` first (token in `.env`). When done: `SLACK_AGENT=Codex-Jury python tools/slack.py post board "Jury review ready: research/jury/review.md · top fix: <one line> @Kian738" --kind done`. Post only that, plus blockers.
- If you can run parallel agents, give each juror its own agent, then reconcile in one pass.

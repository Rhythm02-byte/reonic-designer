# Submission checklist (due Sunday 8 Nov, 15:00)

Reonic asks for three things (brief, p. 8): a working demo (with a short recording as fallback), the code with a README, and a short pitch deck.

## Code and README
- [ ] PRs merged into `main`, and `main` passes `pytest -q` from a fresh clone
- [ ] `python scripts/preflight.py` passes (tests, no data in git, README, deck and demo-script numbers match the reports and the app). Re-run the reports first if results changed: `python -m reonic eval`, `python scripts/repeated_splits.py`, `python scripts/unseen_installer.py`
- [ ] README has setup, approach, results and known limitations (done, re-read it once)
- [ ] No Reonic data in the repo or its history: `git log --all --name-only | grep -E "\.csv|\.joblib|data/raw"` prints nothing
- [ ] Decide how Reonic gets the code: a link they can open (make the repo public, or add them as collaborators). **Owner: repo owner.** The repo is private today.
- [ ] If the repo is public: check that the aggregate figures in `docs/` (deviation chart, tables) are acceptable to share. They contain no project rows.

## Demo
- [ ] Rehearse `docs/demo-script.md` twice with a timer, under 5 minutes
- [ ] Record the fallback demo and keep the file outside the repo (or upload where the brief asks)
- [ ] Re-measure the example numbers if the code changed since the script was written

## Deck
A 7-slide draft is in `docs/pitch/home-energy-designer.pptx` (problem, solution, results, where we disagree, value, limits and next steps), with speaker notes. Its numbers are typed in, not linked: if any result changes, update slides 4, 6 and 7 and the notes.
- [ ] Team reviews the draft and adds names and any branding
- [ ] Problem, solution, how we evaluated, value for installers and homeowners (the four parts the brief names)
- [ ] Only real-data numbers; every business-case number labelled as an assumption
- [ ] Include "where we disagree with the experts" and the limitations slide

## People
- [ ] Every teammate has read the challenge PDF
- [ ] Ask Reonic (stand or event chat) the three questions that change numbers: which offer was signed, module wattage at `2a8ba8e2`, is 4,500 kWh a default. Record answers in `.claude/skills/reonic-data/SKILL.md`, then re-run `python -m reonic eval` and `python scripts/sensitivity.py`
- [ ] Ask what time one design takes today (business case input)

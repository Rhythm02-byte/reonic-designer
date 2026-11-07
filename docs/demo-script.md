# Demo script (5 minutes)

Follows the four-step demo Reonic describes (brief, p. 7): a home is described, a complete system appears, the design is refined, it is checked against reality. Numbers below were measured with the app on the real data; if they differ on your screen, the data or code has changed, so re-measure before recording.

## Before you start

- [ ] Real export in `data/raw/` (two installer folders). Never show or share the raw files.
- [ ] `python -m reonic eval` has been run, so the Evaluation tab has numbers.
- [ ] `streamlit run app.py`, browser at full width, sidebar open.
- [ ] Have `docs/figures/deviation_chart.png` and `docs/business-case.md` open in other tabs.
- [ ] If the web frontend has been merged (`web/`), the steps are the same; only the buttons differ.

## The story

**0:00 The problem (30 s).** Planners spend hours designing each home before an offer can go out. We propose a first design a planner can review, explain and change. The planner keeps the final say.

**0:30 Step 1 and 2: a home, and a complete design (1 min).** Sidebar, "Start from an example", choose **Typical home: we match the expert** (5,000 kWh a year, no EV).
- Design tab: PV 8.9 kWp, battery 9.2 kWh, no heat pump, no wallbox.
- Read one or two lines of "Why": what share of similar past homes got a battery, and the median size. Point at "rough assumptions" on the savings line.
- Say: this home was never used to train the model.

**1:30 Step 3: refine (1 min).**
- Tick **Electric car**, set 12,000 km. PV goes to 9.4 kWp, battery 9 kWh, and a wallbox of 11 kW appears with "rule: has an EV".
- Tick **Override PV**, leave it at 0. The battery disappears (rule R02: no PV, no battery) and the page warns that this is unusual for similar homes. Untick the override.
- Say: the planner can override any component and the rest re-plans around it.

**2:30 Step 4: check against reality (1 min).**
- Compare tab, same typical home: expert PV 9.45 vs ours 8.9, battery 10 vs 9.2, all four components agree.
- Switch to **Home with an EV and a wallbox**: expert PV 13.5 vs ours 10.8, battery 9 vs 9.2, wallbox 11 vs 11, all agree.
- Evaluation tab, said plainly: PV size matches the installer for **45.8%** of unseen homes against **36.1%** for a "typical design" that ignores the home. On the whole design the model (13.5%) is not better than the typical design (15.0%). Our measurable edge is PV size. Do not quote the 3.8% rule-of-thumb figure on its own: it is an easy reference.

**3:30 Where we are wrong, and why (1 min).** Honest part, do not skip.
- Choose **Home that already has PV** (6.7 kWp already): the installer added only a 5 kWh battery; we also propose 9.4 kWp of new PV. Only 18 homes in the data already have PV, too few to learn from.
- Choose **Where we disagree: expert chose a heat pump**: we never propose one; only 13 of 1,593 designs include a heat pump.
- Show the deviation chart: for near-identical homes the installers' own PV size varies from 5.4 to 12.6 kWp, so some disagreement is theirs, not ours.

**4:30 Value and close (30 s).** Business case: about **€4,000 to €28,000 per planner per year** of design time (conservative to base), all assumptions, the biggest unknown being hours per design today. Next: Reonic's answers on which offer was signed and what the 4,500 kWh values are, then roof area and budget as inputs.

## If something goes wrong

- App will not start: `pytest -q` first; check `data/raw/` is present. The app falls back to synthetic data with a visible warning, so never record in that mode.
- Numbers differ from this script: re-run the examples and update this file before recording.
- Out of time: cut the heat pump example and keep the PV one.

## Do not say

- That the tool replaces the planner, or that it raises win rates (we have no data on either).
- That the savings or payback figures are exact. They are labelled rough assumptions.

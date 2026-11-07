# Business case: what faster first designs are worth to an installer

**Read this first.** No number on this page is a Reonic figure. Every input is an assumption, shown as a range, and the largest unknown (how long a design takes today) is open question 7 for Reonic. When Reonic answers, change the inputs in `src/reonic/business.py`; the formulas stay the same. Run `python -m reonic.business` to reproduce the tables.

## What we claim, and what we do not

- **We claim:** a first design that the planner reviews and adjusts takes less time than designing from scratch, and the time saved is worth money and frees capacity for work on site.
- **We do not claim:** that the tool replaces the planner, that it raises win rates, or what it should cost. We have no data on any of those.
- **Why review time is real:** our design agrees with the installer's on every component for only about 14% of homes (random split; 9.8-18.5% on an installer the model has not seen). PV and battery sizes land within tolerance for 46% and 39% of homes. So the planner still checks and edits most designs; the tool provides a starting point.
- **What is solid:** the include decisions. On held-out homes the model correctly includes PV for 93% of homes that have it and a battery for 86% (precision 98% and 94%). That is the part a planner no longer has to start from nothing on.

## The model

Value per planner per year = designs per year × (hours per design today − hours per design with the tool) × planner cost per hour.

| | Conservative | Base | Optimistic |
|---|---|---|---|
| Designs per planner per week (assumption) | 8 | 12 | 15 |
| Hours per design today (assumption) | 1 | 1.5 | 2 |
| Minutes per design with the tool (assumption) | 45 | 30 | 20 |
| Planner cost, €/hour (assumption) | 45 | 50 | 55 |
| Planners per installer (assumption) | 2 | 3 | 4 |
| Designs per planner per year | 368 | 552 | 690 |
| Share of the year spent designing today | 20% | 45% | 75% |
| Hours saved per planner per year | 92 | 552 | 1,150 |
| Share of design time saved | 25% | 67% | 83% |
| **Value per planner per year (€)** | **4,140** | **27,600** | **63,250** |
| Value per installer per year (€) | 8,280 | 82,800 | 253,000 |
| Site days freed per installer per year | 23 | 207 | 575 |

### Where the assumptions come from

| Input | Basis | Confidence |
|---|---|---|
| Designs per week | Reonic's brief: planners "create several offers per day". The number is ours. | Low |
| Hours per design today | Reonic's brief: planners "spend hours on every single design". The number is ours. | Low. The largest driver of the result |
| Minutes with the tool | Our own judgement, set conservatively because most designs need edits | Low |
| Planner cost | Typical loaded cost in Germany; not sourced | Low |
| Planners per installer | Reonic's brief: "mid-sized installation company". The number is ours. | Low |
| Working weeks, hours | 46 weeks × 40 hours | Medium |

A third-party site claims quote time fell from 2 hours to 8 minutes. We did not use it: it is not from Reonic and we could not verify it.

### Which inputs matter most

Value per planner per year with one input moved away from the base case (€27,600):

| Input moved | Result |
|---|---|
| Hours per design today, 1.0 to 2.0 | 13,800 to 41,400 |
| Minutes with the tool, 45 to 20 | 20,700 to 32,200 |
| Designs per planner per week, 8 to 15 | 18,400 to 34,500 |
| Planner cost, 45 to 55 €/hour | 24,840 to 30,360 |

The time per design today moves the result most, and it is the one number Reonic can give us.

## How to use these numbers

- **Headline:** quote the conservative and base cases together, about **€4,000 to €28,000 per planner per year**, and say they are assumptions. Do not lead with the optimistic case: it has a planner designing 75% of the year and saving 83% of that time.
- **Capacity framing:** the same hours, spent on site, are 23 to 207 days per installer per year in the conservative and base cases. This is the argument Reonic's brief makes (more time installing).
- **Per-planner value is a ceiling for price:** an installer will pay less than the value it gets. We have not estimated a price.

## Not modelled

- **Win rate and revenue.** Reonic's brief says faster offers win more often. We have no conversion data, so we do not put a number on it. If Reonic provides offer-to-signed rates and margin per project, add a revenue line: extra signed projects = offers per year × (new win rate − old win rate).
- **Design quality.** The validation view flags unusual choices, but we have not measured whether it improves outcomes.
- **Tool cost, onboarding, and the time to correct a wrong design.** The review-time assumption is meant to cover correction, but it is a guess.

## Open until Reonic answers

1. How long does one design take today?
2. How many offers does a planner create per week?
3. What share of offers are signed, and what is the margin per project?

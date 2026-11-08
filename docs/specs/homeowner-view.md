# Spec: homeowner view, trying variants of an offer

**Status:** not started · **Workstream:** Product & UI · **Stretch goal** (Reonic PDF p. 4 and p. 7)

## Problem

A homeowner who has received an offer wants to understand it and try variants, such as a bigger battery or no heat pump, before signing. They need plain language, not data sheets. They must not be oversold or pushed into the wrong system.

## Behaviour

A separate tab on the same engine:
- The homeowner can switch a component on or off and resize it, but only within the limits the installer offered. Their home's data stays fixed.
- Each change shows, in plain words: the change in cost, the change in yearly savings, and how much of their own solar power they use themselves.
- No technical jargon. Units are shown with a plain explanation.

## Data and code

- Same `Designer` engine as the planner view. No separate model.
- Limits come from the planner's offer, not from the homeowner.
- Plain-language wording may be drafted by an LLM, but every number comes from the engine's output and must be checked against it (see the optional LLM item in PLAN.md). Without an API key the template text is used.

## Done when

- A homeowner can switch and resize at least the battery and the wallbox, and see the effect within one click.
- Choices outside the offered limits are not possible.
- The text has no jargon terms on a checklist of forbidden words (for example kWp, SCOP, self-consumption ratio) unless explained in the same line.
- Shows "rough assumptions" wherever a saving or payback is displayed.

## Out of scope

Signing, payments, and anything that changes the planner's offer.

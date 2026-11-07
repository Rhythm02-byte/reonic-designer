# Product

Product name: **Rhythm** (Home Energy Designer). Styled after reonic.com, but with its own logo.

## Register

product

## Users

- **Planner (installer staff).** Sits at an office laptop during the day, often with a customer on the phone or in a
  video call. Knows PV, batteries, heat pumps and wallboxes. Wants a first design that is close to what an experienced
  colleague would propose, plus a reason to trust it, in seconds rather than an hour of spreadsheet work.
- **Homeowner.** Opens the offer link on a phone at home, in the evening, without the planner next to them. Not an
  expert. Wants to understand what is on offer, what it costs, what it saves, and what happens if they drop or change a
  part. Must never be able to pick something the planner did not allow.

## Product Purpose

Home Energy Designer proposes the PV, battery, heat pump and wallbox sizes for a home the way an expert planner would,
learned from real Reonic projects. Every design is checked against projects the model never saw, and the page says how
often it gets the whole design right compared with a rule of thumb. The planner shares the design as a link; the
homeowner sees it in plain words and can switch between the options the planner allowed. Built for the Reonic challenge
at thinc! München 2026; judged on whether the AI is real, honest about its limits, and useful to both sides.

## Brand Personality

Reonic: calm, competent, warm. A tool from a company that sells software to installers, not a consumer app.
Warm off-white paper, near-black ink, quiet zinc text, pill buttons with an arrow, cards with a hairline border and no
shadow. One wow per view: Reonic's orange to pink gradient, used on the proof (the reality check) and on one headline
word. Everything else stays quiet so the numbers carry the page.

## Anti-references

- A generic SaaS dashboard: KPI tiles in a row, a sidebar, charts for the sake of charts.
- The hero-metric template: one giant number, a tiny label, a gradient behind it.
- Purple or blue-violet gradients, glassmorphism, glowing borders, dark mode "because it looks techy".
- Energy-category reflexes: green leaves, sun icons everywhere, teal and lime.
- A 1:1 copy of reonic.com: no customer logos, testimonials, stock photos or cookie banner.

## Design Principles

1. **Proof before polish.** The held-out check is the product's claim; it gets the one loud moment. Never show a
   number without saying what it was measured on.
2. **Honest about uncertainty.** Rough assumptions, synthetic data and "unknown" inputs are said out loud, next to the
   number they affect, in plain words.
3. **The house is the summary.** The 3D house shows the current design at a glance; text and numbers explain it,
   they do not repeat it.
4. **Two readers, two densities.** The planner gets dense inputs and the evidence table; the homeowner gets one idea per
   card and words before units.
5. **Nothing the planner did not allow.** The homeowner view only offers the options in the link and always shows the
   way back to the recommendation.

## Accessibility & Inclusion

- WCAG 2.2 AA: 4.5:1 for body text, 3:1 for large text and UI parts, including text on the gradient (ink, never white).
- Every option group is a native radio group with a legend; keyboard and screen readers get real controls.
- Status is never colour alone: match/off badges carry the word, the active offer variant has an outline and a label.
- `prefers-reduced-motion` stops the house animation and transitions; `forced-colors` drops the gradient text to plain
  text.
- The 3D house has a text description (`role="img"` + `aria-label`) and a text fallback without WebGL.
- Plain English for homeowners: units are explained the first time (kWp, kWh, kW).

---
# gstack: design-md-format=spec
name: Home Energy Designer
description: Reonic's calm product paper, ink and hairlines, with one warm orange to pink gradient reserved for the proof.
colors:
  surface: "#FDFDFB"
  surface-sunken: "#F7F5EF"
  surface-raised: "#FBFAF7"
  card: "#FFFFFF"
  text: "#1B1D20"
  text-body: "oklch(0.37 0.013 285.805)"
  text-muted: "oklch(0.552 0.016 285.938)"
  text-quiet: "oklch(0.442 0.017 285.786)"
  border: "oklch(0.92 0.004 286.32)"
  primary: "#1B1D20"
  on-primary: "#FDFDFB"
  accent: "#2563EB"
  gradient-start: "#F59A0F"
  gradient-mid: "#F2784A"
  gradient-end: "#EF6AA8"
  gradient-text-start: "#E06D00"
  gradient-text-end: "#E0458A"
  band: "#292025"
  band-end: "#4B4247"
  success: "#34D399"
  warning: "#FBBF24"
  warning-text: "#92400E"
  error: "#9F1239"
  error-surface: "#FFF1F2"
typography:
  display:
    fontFamily: Geist
    fontWeight: 600
    fontSize: 2.25rem
    letterSpacing: -0.025em
  heading:
    fontFamily: Geist
    fontWeight: 600
    fontSize: 1.125rem
  body:
    fontFamily: Geist
    fontSize: 0.875rem
    lineHeight: 1.5
  label:
    fontFamily: Geist
    fontWeight: 500
    fontSize: 0.75rem
  number:
    fontFamily: Geist
    fontWeight: 600
    fontFeature: tnum
rounded:
  sm: 8px
  md: 12px
  lg: 16px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.full}"
  button-secondary:
    backgroundColor: "{colors.card}"
    textColor: "{colors.text}"
    borderColor: "{colors.border}"
    rounded: "{rounded.full}"
  input:
    backgroundColor: "{colors.card}"
    borderColor: "{colors.border}"
    rounded: "{rounded.sm}"
  card:
    backgroundColor: "{colors.card}"
    borderColor: "{colors.border}"
    rounded: "{rounded.lg}"
  icon:
    textColor: "{colors.accent}"
  footer:
    backgroundColor: "{colors.surface-sunken}"
    textColor: "{colors.text-quiet}"
---

# Home Energy Designer

## Overview

**Creative North Star:** Reonic's own product voice, warm paper and ink with hairline cards, so the tool feels like
part of the installer's Reonic software; the one orange to pink moment marks the proof that the AI works.
**Product context:** Planner tool (`/`) and homeowner offer page (`/offer#…`) for the Reonic challenge, thinc! München
2026. Users and principles live in PRODUCT.md.
**Mode per surface:** Planner: Operate (dense inputs, live design, evidence). Offer: Read (one idea per card, plain
words, a few choices).
**Reference sites:** https://reonic.com/de-de/ (tokens measured from the live page, 2026-11-07).
**Key characteristics:**
- Off-white paper, near-black ink, zinc body text; no pure black or white.
- Cards with a 1px zinc-200 border and no shadow; pill buttons with an arrow.
- Small blue line icons label inputs and stats; blue filled check circles mark what is included.
- One gradient card (the reality check) and one gradient headline word per view; nothing else is loud.
- The 3D house is the largest element on both views.

## Colors

**Strategy:** Restrained. Tinted neutrals carry 90% of the surface; blue-600 (`accent`) marks icons, focus and
selection; the gradient appears on the reality card and, on the offer, one headline word and the aubergine band once at the
end of the offer.
**Light or dark:** Light. A planner works at an office laptop in daylight next to a customer call; a homeowner reads
the offer on a phone in a lit living room. Both match reonic.com, which is light.

- Text on the gradient is always `text` (ink): 7.6:1 on orange, 5.9:1 on pink. White and `text-body` fail (3.8:1).
- Gradient text uses the darker `gradient-text-*` stops (3.2:1 and 3.8:1 on paper), so it is allowed only at 24px and
  up (WCAG large text). Under `forced-colors` it falls back to plain text.
- `text-muted` passes on `surface` (4.75:1) but not on `surface-sunken` (4.43:1); text on sand uses `text-quiet`.
- On the dark panel (`text` background) secondary text is zinc-400 (6.6:1); on the band it is zinc-300 (6.5:1).
- Match/off badges use `success` / `warning` fills with ink text and always carry the word.

## Typography

Geist Sans only, loaded through `next/font` (`--font-geist-sans`), the face reonic.com uses. Noto Serif is dropped:
reonic.com uses it only for testimonial quotes, which this product does not have. Scale: display 36px (30px on mobile),
section heading 18px, card title 16px/500, body 14px, label 12px. Numbers use tabular figures. Body copy is capped at
about 65ch.

## Layout

Planner: full-width up to 1500px; a 320px input column and a fluid design column from `lg` (1024px); a single column
below. Offer: up to 1024px (`max-w-5xl`); a fluid column and a sticky 380px cost column from `lg`. Gutters are 16px on
mobile and 24px from `sm`. Inside cards the padding is 16px; gaps between cards 24px; dense input rows 12px.

## Elevation & Depth

Flat. Depth comes from surface steps (sand behind the house, white cards on paper, ink panel inside the gradient card)
and 1px borders. The only shadows are on the 3D labels floating over the canvas and on the selected segment of a
segmented control.

## Shapes

Cards 16px, inner panels 12px (16px card minus a 4px visual gap), inputs 8px, buttons, chips and segmented controls
full pills. Icons are 16px line icons at 1.75 stroke; check circles are filled 16px or 20px discs.

## Components

- **Sidebar (planner, from xl):** sand column, 248px, right hairline: Rhythm logo, a customer search field, Mine/Team
  segmented control, customer list (active item white with a ring), "Signed in as" select at the bottom. Below xl a
  customer select sits in the header instead.
- **Header:** solid `surface`, bottom border, no blur. Rhythm logo (ink rounded square with three rising paper bars,
  "Rhythm" wordmark in Geist 600), a hairline divider,
  "Home Energy Designer", a neutral persona chip; on the planner the share CTA sits right.
- **Button primary:** ink pill, paper text, 14px/500, trailing arrow-up-right; hover ink at 85%; focus-visible 2px
  blue outline with 2px offset; disabled 40% opacity.
- **Button secondary:** white pill with a zinc-200 ring; hover `surface-raised`.
- **Input / select:** white, zinc-200 ring, 8px; focus 2px blue ring; placeholder "Unknown" in zinc-400.
- **Segmented control:** native radios in a sand pill track; checked segment white with a small shadow; focus ring
  blue.
- **Card:** white, 1px border, 16px, no shadow.
- **Reality card (the wow):** gradient background, ink text, eyebrow + headline, a 12px ink inner panel with
  model vs. rule-of-thumb bars and the held-out project table with match/off badges.
- **Check list:** blue filled check circle + text for "Why this design" and included offer parts; a muted minus circle
  for parts that are not included.
- **Band:** aubergine (`band` to `band-end`) with a grain overlay, paper text, closes the offer page.
- **Footer:** `surface-sunken`, 12px `text-quiet` data note.
- **States:** skeletons (sand pulse) while loading, rose alert for errors, 60% opacity while a variant recalculates.

## Do's and Don'ts

- Do keep the gradient to the reality card and one headline word per view.
- Do put ink, never white, on the gradient.
- Do pair every number with what it was measured on or which assumptions it rests on.
- Do use blue only for icons, focus and selection.
- Don't add shadows to cards, blur to the header, or a second gradient element.
- Don't copy reonic.com marketing furniture: customer logos, testimonials, photos, cookie banner.
- Don't build KPI tile rows or a giant hero number; the reality numbers live in bars with labels.
- Don't use em dashes in UI copy.

## Motion

- **Approach:** minimal-functional.
- **Easing:** enter(ease-out) exit(ease-out) move(ease-in-out); colour transitions use the Tailwind default.
- **Duration:** micro(150ms) short(200ms) for hover and selection; skeleton pulse only while loading.
- **The one authored moment:** house parts pop in one after another (25ms apart) when the design changes; stopped
  under `prefers-reduced-motion`.

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-11-07 | Initial design system created | Created by /design-consultation from tokens measured on reonic.com/de-de and the approved plan (2 views, calm product + 1 wow; logo later replaced by Rhythm) |
| 2026-11-07 | Gradient text allowed once per view | User-approved exception to impeccable's ban; darkened stops, large text only, forced-colors fallback |
| 2026-11-07 | Ink text on the gradient card | reonic.com uses white text there, which fails AA (2.2:1 on orange) |
| 2026-11-07 | Own logo "Rhythm" instead of the Reonic logo | User request: a similar mark (rounded ink square) with its own name and glyph; no Reonic artwork in the product |
| 2026-11-07 | Planner becomes a workspace with a customer sidebar | Operating software for several planners and customers; the planner h1 is the customer name, so its gradient word is gone |
| 2026-11-07 | Noto Serif removed | Only reonic.com's testimonials use it; the gradient sans word replaces the italic serif |

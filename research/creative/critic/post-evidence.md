# Post-evidence critic decision

**2026-11-08, Europe/Berlin. Verdict: promote I13 to final priority 1, subject to the narrow scope below.** This is an explicit **measured-evidence override** of the original subjective tournament, not a retroactive Elo improvement. Preserve `tournament.json`, all original ratings/matches, and the raw idea pool unchanged. The parent is the final judge; this is the critic's recommendation.

## Why the promotion is warranted

The [DEV stress handoff](../ceiling/STRESS.md) supplies concrete failures that were unavailable when I13 ranked eighth. One negative PV capacity among 676 policy returns is a direct bounded-output defect. Strict module arithmetic fails for 39 of 70 designs in 24 preselected full responses, consistent with display precision loss. A separate availability follow-up finds eight absent fields among 347 required metric fields and an empty-candidate exception caught by the metrics attachment path. These issues can invalidate the draft or its explanation during the demo; improving a pitch while leaving them undisclosed is the wrong ordering.

Keep the severity distinctions: **120 missed relevant-review checks are not 120 physical violations**; 58 other review cases are blocked by the policy-only adapter, and the full-response subset has four misses among 16 review cases. The arithmetic finding is evidence of representation inconsistency, not 39 physically impossible installations. The 15 passing toy trajectories and 676 passing replay comparisons are useful scoped evidence, not proof of full-year API conservation or release readiness. The canonical DEV run lacks a start SHA, so its model consistency is mtime-only; the later metric follow-up has start/end SHA. No controlled before/after claim is justified.

## Counterargument and restriction

A rushed broad engine rewrite could break the working demo, and most review misses need agreed semantics rather than more generic warnings. A blanket warning on every request would game review sensitivity and harm ordinary flows; false-review coverage is incomplete. Therefore promote **small owner repairs and honest acceptance checks**, not a new model, readiness classifier, full schema redesign, or a promise to eliminate every blocked check before freeze. If the owner cannot make and verify the bounded fixes, the fallback is a disclosed limitation and a narrowed demo scope, never a passing release claim.

## Narrow mini-spec for Engine and Eval owners

**What:** repair numeric/domain handling, module arithmetic consistency, and the empty simulation-candidate path. Audit review warnings separately under predeclared relevant semantics.

**How and acceptance:**

1. Freeze model/config hashes and preserve all failing DEV receipts. Engine rejects negative roof/domain inputs through a controlled API response, or returns an explicitly reviewed bounded draft where that behavior is already agreed; no accepted draft may contain negative capacity. Test the exact synthetic failure plus valid neighboring values. A schema/API contract change follows the existing owner/announcement process.
2. Preserve the module identity at its stated units and precision in every proposal and alternative. Re-run the fixed 24-response/70-design subset and independent arithmetic assertion, including planner locks; do not weaken the tolerance to make rounding pass.
3. Handle empty/nonfinite autarky candidate sets without an uncontrolled exception. For supported cases, produce the eligible required metrics; otherwise surface the explicitly degraded/undefined state through agreed existing semantics. Never fabricate zero savings/energy or treat caught simulation failure as a successful simulation. Re-run the missing-metric fixtures with availability denominators, not only bounds on values that happened to be returned.
4. For review, agree exact case/code mappings and full-endpoint eligibility before repair. Recheck the four missing full-response warnings and representative ordinary controls. Preserve policy-adapter blockers as blockers; no blanket-warning workaround or post-hoc relabeling of difficult cases.
5. Eval reruns targeted owner tests and the unchanged DEV suite offline with start/end hashes. If all scoped critical checks pass, run a newly frozen evaluator-controlled seed/profile split after fixes. Preserve the original failure report and describe the old suite as development-used. Retain independent toy/replay checks and every remaining coverage blocker.

**Measurement:** pass/fail/blocked per eligible check and response/design/field denominators; no synthetic expert labels, no 2026 selection, no changed sizing objective. No model retraining or tuning to these failures is part of this mini-spec.

**Demo moment:** a deliberately invalid roof input receives controlled handling; a valid proposal and its alternatives have exact module arithmetic and real available simulation metrics. Demonstrate the useful behavior without claiming broader certification.

**Hours and risk:** original I13's two-hour estimate covered the harness/ledger, not these newly evidenced repairs. Reserve **2–4 owner-hours for the bounded engine patches plus 1–2 Eval hours** for reruns/review; these are planning estimates, not measured effort, and full-endpoint warning semantics may exceed them. Under a frozen model, the numeric/precision patches have moderate regression risk; metrics fallback and review changes have higher uncertainty. Owner-confirmed small patches and targeted checks are the cut line. Do not expand into a simulator or contract rewrite to satisfy the deadline.

## Final ranking recommendation

Final action priorities become **I13, I23, I02, I17, I03**, followed by I20. Label the first row “post-evidence override; original rank 8 / Elo 1652.2.” Shift original ranks 1–7 down one position and retain every original Elo. The unchanged tournament remains a faithful record of the pre-evidence judgments; this addendum explains why a new observed defect outranks them.

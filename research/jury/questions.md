# Fifteen hard jury questions

Answers below are limited to two sentences each. Proof references are separate. Authority is the supplied `Reonic_Hackathon_Challenge_final.pdf`, especially pp. 3–8; model numbers use `eval/results/latest.json → served.test`, not the exploratory top-level headline.

1. **Your whole-system accuracy is effectively the median. Why should we choose you?**

   “We match all components within our declared tolerances on 68 of 325 later projects, versus 67 for the installer-specific median bundle, so we claim a tie. Our differentiation is helping the planner expose missing information, refine the draft, inspect flags, and explain approved options.”

   Proof: `eval/results/latest.json → served.test`; `apps/web/components/AskNext.tsx`; `Planner.tsx`; `Offer.tsx`.

2. **Was the 2026 test really untouched and scored once?**

   “No: the history contains at least three test-scored runs, and earlier baseline results had also been seen. Selection is documented as using validation, but repeated access means we should describe this as a temporal holdout rather than a once-only untouched final exam.”

   Proof: `eval/history/runs.jsonl:5–7`; `research/model-selection.md` opening caveat; `eval/run.py` recording controls.

3. **Did the model behind your live comparison train on that project?**

   “The holdout service fits a model through the cutoff, but the ordinary training command uses all processed projects. We must identify a cutoff-pinned artifact before calling the ordinary planner's revised prediction unseen; otherwise the edit demonstrates workflow only.”

   Proof: `services/engine/engine/demo.py:181–184`; `policy/train.py:23–26`; `apps/web/components/Planner.tsx:160–163`; `lib/api.ts:278–281`.

4. **Your shuffled-label model still scores well. Is the AI learning anything?**

   “PV matching falls from 52.2% to 40.3% on validation when training labels are shuffled, supporting an input-dependent PV signal. Whole-design matching remains 21.7% versus 24.1% real and 17.7% for B0, so retained rules and marginals explain much of that score and the control does not prove absence of leakage.”

   Proof: `eval/results/latest.json → honesty.shuffledLabels`; `eval/honesty.py:74–89`.

5. **Is +0.6 ±2.0 evidence you outperform the baseline?**

   “No: that is the paired whole-design gap across overlapping pre-2026 random splits, with ± reporting split standard deviation rather than a confidence interval. We report a tie and distinguish it from the observed temporal-sample PV advantage.”

   Proof: `latest.json → honesty.repeatedSplits`; `served.test.models`.

6. **Who decided a 20% PV error is acceptable?**

   “We chose PV ±20% and battery/heat-pump ±25% for expert-agreement scoring; wallbox scoring checks inclusion. Those are not installer-approved engineering tolerances or certification that the proposed system fits a roof.”

   Proof: `eval/metrics.py:85–109`; PDF pp. 3,6 distinguishes plausibility from simple imitation.

7. **What exactly is your ‘installer's usual design’ baseline?**

   “It is a historical installer-specific median bundle with simple inclusion habits, not an expert designing the new home. It is a useful strong frequency benchmark, and it does not measure time saved against a real planner.”

   Proof: `services/engine/engine/baseline.py:100–102`; `eval/results/latest.json → served.test.models.B0`.

8. **Is the roof-question uplift circular?**

   “Yes, it deliberately uses the expert's own module count as a cap, so the 20.9% to 32.9% whole-design result is an oracle upper bound. It motivates collecting roof capacity but does not predict the benefit of a homeowner answering that question.”

   Proof: `latest.json → oracle.fields.roof`; `eval/oracle.py`; slide `asknext` footnote.

9. **Does +9.8 points prove your question-ranking feature saves work?**

   “It shows that restoring recorded demand after replacing every demand with the 4,500 kWh default improves whole-design matching in this intervention. We have not measured whether the ranking elicits better answers or reduces planner effort in real qualification calls.”

   Proof: `latest.json → oracle.fields.demand`; `engine/ask_next.py`; `PLAN.md §17` default-value question.

10. **Can I order the suggested equipment and install it?**

    “The BOM is a preliminary candidate selection based on individual product sizes and historical service lines. It does not establish inverter/battery compatibility, string and MPPT limits, mounting geometry, heat-loss adequacy, or a site-approved installation.”

    Proof: `services/engine/engine/design.py:124–154`; `apps/web/components/PartsList.tsx`; `research/external/COMPATIBILITY.md` is research, not implemented certification.

11. **What is actually AI here, and why not just prompt an LLM?**

    “The sizing policy uses trained gradient-boosted presence, size, and quantile models combined with deterministic rules and simulation. The sizing path works without an LLM, which is consistent with the brief's explicit acceptance of statistical/ML models and optional language models.”

    Proof: `policy/chain.py:85–123`; `policy/designer.py:302–310,376–421`; PDF p. 6.

12. **Will this work for an installer we have never seen?**

    “We have evidence from two installers and some leave-one-installer-out experiments, not a validated rollout of the current served policy to new customers. A new installer needs product mapping, unit/schema checks, and a measured validation period before we can promise comparable behavior.”

    Proof: `latest.json → installers, splits.loio_test_*`; `research/model-selection.md`; `PLAN.md §17` unanswered data questions.

13. **Do the ranges mean an 80% chance the design is right?**

    “No: the intervals describe expert size variation, with empirical historical coverage, rather than the probability that every component is correct or suitable. Earlier coverage results also need their model/configuration identified before being attributed to the current served policy.”

    Proof: `research/model-selection.md → p10-p90 interval coverage`; `policy.json → conformal`; `apps/web/components/PartRange.tsx`.

14. **How many hours or euros have you saved, and what happens to win rate?**

    “We have not measured labor saved or conversion uplift, and API response time is not time to an approved offer. The euro figures in the business case are explicitly assumed scenarios; the next pilot should measure reviewed-offer task time, corrections, and homeowner follow-up.”

    Proof: `docs/business-case.md`; `docs/PITCH.md §7`; PDF pp. 5,8.

15. **What happens if the engine or the phone link fails during your demo?**

    “A labelled offline pitch mode exists, but pending requests currently lack a timeout and the homeowner BOM depends on the engine. We should rehearse a local recording fallback and a synthetic phone offer on a reachable origin; until that is done, we cannot claim the failure path is verified.”

    Proof: `apps/web/lib/engine.ts:126–155`; `components/pitch/Pitch.tsx:143–181`; `PartsList.tsx:57–76`; `OfferQr.tsx:13`; `docs/BACKLOG.md A`.

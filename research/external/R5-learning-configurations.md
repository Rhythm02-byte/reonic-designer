## Summary (≤150 words)

As of **2026-11-07**, recommend independent component models, catalog-valid candidate generation, deterministic simulation and feasibility checks. Compare pooled median/mode and nearest-neighbor baselines before adding complexity. Predictor-level monotonic constraints do not guarantee monotonic final bundle selection. [Scikit-learn](https://scikit-learn.org/stable/modules/ensemble.html)

The decisive labeling question is whether alternatives are **all acceptable** or **offered choices with one selected design**. Standard partial-label learning assumes one true candidate, not several equally valid systems. [Cour et al.](https://jmlr.org/papers/v12/cour11a.html)

Use temporal validation and two directional installer-transfer tests. Conformal methods can express ambiguity, but ordinary guarantees depend on assumptions and are not automatically joint bundle guarantees. [MAPIE](https://mapie.readthedocs.io/en/stable/content/getting-started/choosing-algorithm/), [Angelopoulos and Bates](https://arxiv.org/abs/2107.07511)

Effort estimates and expected benefits below are proposals, not measured project results.

## Findings

### Method decision table

All effort estimates assume working ETL/simulation and an engineer familiar with the pipeline. They overlap and are not additive.

| Method | Fit | Estimated hours | Expected benefit—hypothesis | Main risk / reference |
|---|---|---:|---|---|
| **Monotone gradient boosting** | Strong first candidate | 3–5 | Nonlinear tabular imitation with selected directional constraints | Constraints apply conditionally; projection/ranking may break them. Multiclass restrictions apply. [Docs](https://scikit-learn.org/stable/modules/ensemble.html) |
| **Ordinal regression** | Good for ordered product steps | 3–5 | Respects ordering | Rank gaps differ from physical kWh/kW gaps. [Paper](https://www.jmlr.org/beta/papers/v18/15-495.html) |
| **Independent multi-output models** | Best first interface | 2–4 | Simple debugging and missing-target handling | Can produce incompatible bundles; enforce feasibility separately. [Docs](https://scikit-learn.org/stable/modules/multiclass.html) |
| **Classifier/regressor chains** | Possible second iteration | 4–7 | Captures output dependencies | Order/error propagation; train-time true labels differ from predicted inference inputs. [Docs](https://scikit-learn.org/stable/modules/generated/sklearn.multioutput.ClassifierChain.html) |
| **Structured/energy-based bundle scoring** | Strong architectural fit | 6–10 | Coherent combinations and tradeoffs | Candidate recall bounds accuracy; flexible scorer overfits. Start linear. [Tutorial](https://media.nips.cc/Conferences/2006/Tutorials/Slides/LeCun.pdf) |
| **Case-based reasoning / kNN** | Valuable baseline | 2–3; learned metric 5–8 | Realistic complete precedent bundles | Scaling/missingness/installer identity can dominate distance. NCA is not automatically suited to mixed outputs. [Docs](https://scikit-learn.org/stable/modules/neighbors) |
| **Hierarchical installer effects** | Conceptually appropriate; defer full Bayesian build | 6–10 | Partial pooling of installer tendencies | Two groups weakly identify between-installer variability; informative prior may be needed. [Gelman](https://statmodeling.stat.columbia.edu/2015/12/08/hierarchical-modeling-when-you-have-only-2-groups-i-still-think-its-a-good-idea-you-just-need-an-informative-prior-on-the-group-level-variation/) |
| **Conformal classification/CQR** | Optional after stable model | 3–5 | Sets/intervals with assessed coverage | Separate calibration data; marginal ≠ joint/subgroup coverage; shift matters. [MAPIE](https://mapie.readthedocs.io/en/stable/content/getting-started/choosing-algorithm/), [overview](https://arxiv.org/abs/2107.07511) |
| **Inverse optimization / conditional logit** | Only with identifiable choices/choice sets | 8–14 | Learns tradeoff weights | Signed designs mix preference, sales, availability and installer style; synthetic alternatives are not known rejected choices. [Inverse optimization](https://open.bu.edu/items/f886116f-6c18-44b9-b3e3-46112715298f), [Train](https://eml.berkeley.edu/books/choice2.html) |
| **Physics-informed features/scoring** | High priority with existing simulator | 3–5 | Adds physical/economic structure | Simulation output is not measured truth; features must be available from intake/candidate. [Theory-guided learning](https://arxiv.org/abs/1612.08544) |
| **Set-valued / partial labels** | Essential semantics; specialist model optional | 2–4 bookkeeping; 8–14 specialist | Avoids penalizing known acceptable alternatives | Standard partial-label assumption differs from multiple valid outputs. [Paper](https://jmlr.org/papers/v12/cour11a.html) |
| **Placeholder detection** | Mandatory quality layer | 2–3 | Prevents defaults becoming false relationships | Frequency spikes alone do not prove errors; combine provenance/constraints/statistics. [HoloClean](https://www.vldb.org/pvldb/vol10/p1190-rekatsinas.pdf) |

### Recommended 20-hour stack

Proposed allocation:

1. **0–3 h:** freeze project/household identifiers, alternative semantics, splits and default flags.
2. **3–5 h:** pooled mode/median, engineering-rule and fixed-distance kNN baselines.
3. **5–9 h:** independent presence classifiers and conditional size regressors; numeric PV module count.
4. **9–13 h:** enumerate nearby valid catalogue combinations, retrieved bundles and feasible no-battery alternatives; reject invalid candidates; simulate and score.
5. **13–16 h:** temporal/installer evaluation and ablations.
6. **16–18 h:** one conformal output only if adequate calibration data and stable pipeline exist.
7. **18–20 h:** deterministic export, fallbacks, versions and traceable explanations.

The allocation is an engineering recommendation based on the methods above, not a demonstrated delivery estimate. Defer learned metrics, full hierarchical inference, chains and inverse utility learning.

### Alternatives and defaults

For genuinely acceptable set \(Y_i\), preserve the set. A proposed training convention gives each project weight one, distributing \(1/m_i\) across its retained alternatives.

For one selected option among known choices \(C_i\), conditional logit is a different formulation:

\[
P(y\mid x,C_i)=
\frac{\exp(w^\top\phi(x,y))}
{\sum_{z\in C_i}\exp(w^\top\phi(x,z))}
\]

Interpretation depends on recorded choice sets and model assumptions. Unchosen does not mean technically invalid. [Train](https://eml.berkeley.edu/books/choice2.html)

For suspected defaults, inspect training-only frequency spikes, provenance and cross-field consistency. Preserve original value plus `suspectedDefault`; compare keep/missing/exclude treatments. Repeated **4,500 kWh** alone is not proof. This is a proposed audit informed by statistical/constraint-based cleaning. [HoloClean](https://www.vldb.org/pvldb/vol10/p1190-rekatsinas.pdf)

### Evaluation protocol

**Splits:** a proposed starting allocation is oldest60% training, next15% validation, next10% conformalization, newest15% final test. Publish actual dates/counts. Keep variants and repeated households together; fit preprocessing/default detection inside training folds. Use expanding-window development checks. [Leakage guidance](https://scikit-learn.org/stable/common_pitfalls), [cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html)

Run **installer A→B** and **B→A** separately. Do not estimate target-installer effects using target labels. Two directions are not a population-wide generalization estimate.

| Dimension | Proposed metrics |
|---|---|
| Component presence | Precision/recall/F1, prevalence, log loss/Brier and reliability plots |
| Size | Physical-unit MAE, step error, over/undersizing; separate presence failures |
| Acceptable sets | Top-one membership; top-three intersection; minimum distance to recorded acceptable set |
| Whole bundle | Match/tolerance accuracy, invalid rate, lock violations, end-to-end monotonicity |
| Candidate generation | Recall of observed acceptable bundles before ranking |
| Economics | Simulator objective gap against best candidate in the **same candidate set** |
| Uncertainty | Coverage and width/set size; descriptive installer/missingness subgroups |

These metrics are proposed, not established project scores. Brier alone is not a calibration diagnosis; unrecorded alternatives may also be valid. [Calibration](https://scikit-learn.org/stable/modules/calibration.html)

### Three invalidating pitfalls

1. **Leakage:** variants crossing splits, preprocessing fit globally, or final BOM/price used as intake features. [Guidance](https://scikit-learn.org/stable/common_pitfalls)
2. **Wrong label semantics:** treating rejected offers as acceptable, or arbitrarily choosing one of several valid systems. [Partial-label paper](https://jmlr.org/papers/v12/cour11a.html)
3. **Conflating imitation, validity and uncertainty:** expert match is not economic optimality; simulated savings are not measured savings; component coverage is not joint coverage under shift. [Theory-guided learning](https://arxiv.org/abs/1612.08544), [conformal overview](https://arxiv.org/abs/2107.07511)

## Implications for our product

- Ship independent models plus feasible bundle selection first.
- Preserve accepted/offered/signed distinctions.
- Evaluate catalogue mapping and ranking as part of the model.
- Keep pooled fallback behavior for unseen installers.
- Expose uncertain/default inputs.
- Label simulation results and uncertainty scope.
- Avoid unsupported numeric improvement or confidence claims.

## Open questions / uncertainty

- Class balance, effective project count, repeated households and alternative semantics are U.
- No numeric expected model gain is defensible without evaluation.
- Availability of explicit default metadata is U.
- Effort assumes functioning ETL and offline simulation.
- Historical and current catalogue availability may differ.
- Installed library versions were not inspected; no untested API implementation is prescribed.

## Sources (numbered list: title — publisher — date — URL)

All accessed **2026-11-07**.

1. Ensemble methods — scikit-learn — current undated docs — [URL](https://scikit-learn.org/stable/modules/ensemble.html).
2. Learning from Partial Labels — Cour, Sapp and Taskar, JMLR — 2011 — [URL](https://jmlr.org/papers/v12/cour11a.html).
3. Choosing algorithms — MAPIE — current undated docs — [URL](https://mapie.readthedocs.io/en/stable/content/getting-started/choosing-algorithm/).
4. Consistency of Ordinal Regression — Pedregosa, Bach and Gramfort, JMLR — 2017 — [URL](https://www.jmlr.org/beta/papers/v18/15-495.html).
5. Multi-output / chains — scikit-learn — current undated docs — [Multi-output](https://scikit-learn.org/stable/modules/multiclass.html), [chains](https://scikit-learn.org/stable/modules/generated/sklearn.multioutput.ClassifierChain.html).
6. Energy-Based Learning — LeCun, NeurIPS tutorial — 2006 — [URL](https://media.nips.cc/Conferences/2006/Tutorials/Slides/LeCun.pdf).
7. Nearest Neighbors / NCA — scikit-learn — current undated docs — [URL](https://scikit-learn.org/stable/modules/neighbors).
8. Hierarchical models with two groups — Andrew Gelman — 2015-12-08 — [URL](https://statmodeling.stat.columbia.edu/2015/12/08/hierarchical-modeling-when-you-have-only-2-groups-i-still-think-its-a-good-idea-you-just-need-an-informative-prior-on-the-group-level-variation/).
9. Introduction to Conformal Prediction — Angelopoulos and Bates — 2021, revised — [URL](https://arxiv.org/abs/2107.07511).
10. Data-Driven Estimation Using Inverse Optimization — Bertsimas, Gupta and Paschalidis — 2015 — [URL](https://open.bu.edu/items/f886116f-6c18-44b9-b3e3-46112715298f).
11. Discrete Choice Methods with Simulation — Kenneth Train — 2009 — [URL](https://eml.berkeley.edu/books/choice2.html).
12. Theory-guided Data Science — Karpatne et al. — 2016/2017 — [URL](https://arxiv.org/abs/1612.08544).
13. HoloClean — Rekatsinas et al., PVLDB — 2017 — [URL](https://www.vldb.org/pvldb/vol10/p1190-rekatsinas.pdf).
14. Pitfalls / validation / calibration — scikit-learn — current undated docs — [Pitfalls](https://scikit-learn.org/stable/common_pitfalls), [validation](https://scikit-learn.org/stable/modules/cross_validation.html), [calibration](https://scikit-learn.org/stable/modules/calibration.html).

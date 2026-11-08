"""Replay a subjective, auditable 30-idea pairwise tournament. No model/data access.

Run from any directory: python research/creative/critic/rank.py
The scalar rubric makes decisions transparent; Elo is a display of those judgments,
not independent evidence of quality. Replaying orders quantifies only order effects.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
POOL = HERE.parent / "generator" / "ideas.json"
WEIGHTS = {"jury_impact": .35, "evidence": .30, "time": .20, "safety": .15}

# id: jury, evidence available before freeze, hours, demo risk (0 best / 5 worst),
# critic objection, explicit judge disposition after the generator's reply.
REVIEW = {
 "I01": (4, 3.5, .5, 1, "No empirically justified install-ready threshold; new UI outside scope.", "AMEND: pitch-only survey checklist, existing warnings; no new gate or UI."),
 "I02": (5, 5, .5, .5, "Masking/oracle gains are not a prospective customer-question trial; expert roof cap is target leakage if presented as observed roof.", "KEEP: rehearse existing Ask next; state oracle qualifier beside proof, use synthetic interactive home."),
 "I03": (4.8, 4.5, 1.5, 1, "Value 4500 alone cannot prove a default; current design warning ignores entered provenance although Ask next respects it.", "KEEP: paired provenance cases, aggregate findings and owner request; no engine edit by Codex."),
 "I04": (4.8, 4, 1.5, 1.5, "Simulator choice is assumption-sensitive; a zero can follow exception; optimum only among tested candidates.", "AMEND: frozen successful-simulation receipt and scenario comparator; no universal economic optimum."),
 "I05": (4.8, 4, 2, 1, "No source establishes which option was signed; any-option scoring rewards option count.", "KEEP: label audit and mentor question before fitting; keep primary score unchanged."),
 "I06": (4.5, 4, 2, 1, "Coarse neighbors do not prove an information-theoretic ceiling; exact collisions give only an empirical finite-sample bound.", "KEEP: expose exact/collapsed feature definition and singleton counts; never claim a 25% universal ceiling."),
 "I07": (4, 2.5, 6, 3, "Already registered experiment; no measured gain and full fold research can exceed freeze budget.", "DEFER: top-K bundle ranking on pre-2026 folds only; no new model adoption now."),
 "I08": (3.8, 2.5, 5, 2.5, "Already registered experiment; catalogue classes do not guarantee joint-objective gain.", "DEFER: tolerance-mass objective on registered settings and pre-2026 folds."),
 "I09": (4.2, 4.5, 1, .5, "Test-based example selection could become flattering cherry-picking; paired uncertainty matters.", "KEEP: fixed validation aggregate win/loss/error intersections; do not select models from 2026."),
 "I10": (4, 2.5, 3, 2, "Uncited bounds create fake certainty; scenario range is not a confidence interval.", "DEFER unless cited frozen bounds exist: deterministic tariff/profile scenarios only."),
 "I11": (4, 3, 1.5, 1.5, "Rooftop proxy is not verified residential status; observed market practice is not correct sizing; linkage must use official IDs.", "CONDITIONAL: show only real extracted cohort counts/years and separately report unlinked storage."),
 "I12": (4, 3, 2, 1.5, "Few measured homes are not population uncertainty; hourly aggregation still loses intrahour dynamics.", "CONDITIONAL: paired fixed-design profile sensitivity, named datasets and coverage; no new calibration claim without data."),
 "I13": (4.8, 4.5, 2, 1, "Existing fuzz already covers basic cases; a checker reusing optimizer rules is not independent; missing conservation trace blocks coverage.", "KEEP: frozen reject/review expectations, independent identities and explicit eligible denominators; report blocked checks."),
 "I14": (4.3, 3, 3, 1.5, "Validation threshold cannot promise calibration for new installers or shifted data.", "DEFER deployment: make validation-only selective-risk curve; pooled transfer remains unverified."),
 "I15": (3.7, 2, 4, 2, "Answer weights and user-time costs unmeasured; policy sensitivity is not accuracy uplift.", "RESEARCH: log question sensitivity and propose timed planner study; no minutes or accuracy claim."),
 "I16": (4.2, 4, 1, 1, "Signed offers identify purchases among observed projects, not causal physical need; EV flag absence may be missingness.", "KEEP: language and attribution audit, no causal claim from observational bundles."),
 "I17": (4.5, 4.5, 1, .5, "New receipt UI is scope creep; a hash alone does not prove no network or fresh code.", "KEEP: offline artifact/config/source-hash and replay report with attempted-network coverage; no UI."),
 "I18": (4, 4, 2, 1, "Two installers supply only two transfer directions, not general unseen-installer validation.", "KEEP AUDIT: per-transfer counts/coverage; qualify pooled fallback; no universal generalization claim."),
 "I19": (4.6, 4, 2, 1, "Existing versus total sizes and incremental economics may disagree across layers; require owner-confirmed semantics.", "KEEP: synthetic semantic accounting fixtures and request, not a prefreeze engine rewrite."),
 "I20": (4.2, 4.5, .5, .5, "Very few HP labels cannot justify a learned sizing or standards-compliance claim.", "KEEP: physics-led evidence statement and required site inputs; no compliance guarantee."),
 "I21": (3.5, 3, 2, 1.5, "Shadow price implies an optimization interpretation unsupported by a discrete coupled policy.", "AMEND: one-more-module scenario difference, no monotonicity/general economic guarantee."),
 "I22": (3.8, 2, 4, 2.5, "Existing variants are battery sweeps, not an established whole-system Pareto frontier; new UI is forbidden.", "DEFER: inspect existing approved variants only; no frontier or Pareto optimality claim."),
 "I23": (5, 5, .5, 0, "Whole-design superiority, labor saving and stale latency could invalidate an otherwise honest pitch.", "KEEP FIRST: request precise PV gain/tie/oracle/elapsed-time language and fresh benchmark receipt."),
 "I24": (4.2, 4.5, 1, .5, "Choosing the scoring rule that makes ours win is metric overfitting.", "KEEP: freeze sensitivity definitions first, report all and retain primary metric."),
 "I25": (4, 4, 1, .5, "Other teams' actions/scores are rumors; product marketing does not independently establish comparative performance.", "KEEP: cite vendor features narrowly; differentiate on evidence/workflow, not unsupported novelty."),
 "I26": (3.5, 1.5, 6, 3, "Regret requires independently defined utility; one purchased bundle is not a counterfactual utility label.", "RESEARCH ONLY: elicit planner preferences and freeze utility before a regret experiment."),
 "I27": (4.2, 2.5, 2, 1, "No prospective roof/budget trial can deliver reliable gain before freeze.", "KEEP PLAN: define a small future collection study; no claimed measured gain."),
 "I28": (4, 3.5, .75, 1.5, "Opening with failure can confuse; selected test example may be cherry-picked.", "PROTECT WILDCARD: rehearsed synthetic or fixed validation counterexample; show why assistance still helps."),
 "I29": (3.8, 1.5, 3, 3, "Sales model and information pricing are untested; new gating product exceeds scope.", "PROTECT WILDCARD: pitch-only future information-first experiment, no price/revenue assertion."),
 "I30": (3.7, 1.5, 6, 3.5, "Passport/export lifecycle is a different product with substantial data governance and stale-assumption work.", "PROTECT WILDCARD: future versioned assumptions receipt concept, no implementation before freeze."),
}

GENERATOR_REPLY = {
 "received": "2026-11-08 Europe/Berlin",
 "text": "Generator accepted I02,03,05,06,09,11,12,14,15,16,18,20,24,25,26,27,28,29,30 critiques fully. Amended I01 to a pitch-only site-survey checklist; I04 to a frozen scenario receipt; deferred I07/08; limited I10 to deterministic sourced scenarios; I13 to incremental independent coverage; I17 to report hashes, no UI; I19 to accounting audit; I21 to scenario difference; I22 to existing sweep inspection; I23 top-priority owner request.",
 "source": "Actual collaboration message from /root/creative_generate after two critic messages, retained verbatim in the chat; this is a concise paraphrase.",
}


def assess(candidate):
    ident = candidate["id"]
    jury, evidence, hours, risk, objection, disposition = REVIEW[ident]
    axes = {"jury_impact": jury, "evidence": evidence,
            "time": max(0., 5 * (1-hours/8)), "safety": 5-risk}
    amended = {
        "I01": {"title": "Survey-needed handoff checklist", "owner": "Pitch", "first_step": "Write a pitch-only site-survey checklist using existing missing inputs and warning semantics; no new readiness gate."},
        "I20": {"title": "Heat-pump evidence scope statement", "owner": "Pitch", "first_step": "State sparse HP labels and physics-led sizing in pitch notes; ask planner what site inputs remain necessary."},
        "I21": {"title": "One-more-module scenario difference", "first_step": "Freeze one synthetic home and compare fixed constraints differing by one module; label a scenario difference, not shadow price."},
    }
    return {**candidate, **amended.get(ident, {}), "review_hours": hours, "risk_0_best_5_worst": risk,
            "axes": axes, "weighted_score": sum(WEIGHTS[k]*v for k,v in axes.items()),
            "critic": objection, "judge_decision": disposition,
            "judge_identity": "critic agent /root/creative_critic; parent/Claude final review required"}


def compare(a, b):
    contributions = {k: WEIGHTS[k]*(a["axes"][k]-b["axes"][k]) for k in WEIGHTS}
    delta = sum(contributions.values())
    result = .5 if abs(delta) < .075 else float(delta > 0)
    leading = sorted(contributions, key=lambda k: -abs(contributions[k]))[:2]
    winner = "tie" if result == .5 else (a["id"] if result else b["id"])
    why = "; ".join(f"{k}: {a['id']}={a['axes'][k]:.3f}, {b['id']}={b['axes'][k]:.3f}, weighted difference={contributions[k]:+.3f}" for k in leading)
    return {"a": a["id"], "b": b["id"], "score_a": result,
            "winner": winner, "weighted_difference_a_minus_b": round(delta,6),
            "rationale": why + ". Apply the recorded judge restrictions to both ideas; a win never licenses a cut feature."}


def replay(matches, order):
    elo = {key: 1500. for key in REVIEW}
    for idx in order:
        m = matches[idx]
        a,b = m["a"],m["b"]
        expected = 1 / (1 + 10 ** ((elo[b]-elo[a])/400))
        change = 24 * (m["score_a"]-expected)
        elo[a] += change
        elo[b] -= change
    return elo


def main():
    raw_bytes = POOL.read_bytes()
    pool = json.loads(raw_bytes)
    ideas = [assess(c) for c in pool["canonical_candidates"]]
    assert len(ideas) >= 25 and {x["id"] for x in ideas} == set(REVIEW)
    matches = [compare(a,b) for a,b in itertools.combinations(ideas, 2)]
    assert len(matches) == 435
    replays=[]
    for seed in range(20):
        order=list(range(len(matches)))
        random.Random(seed).shuffle(order)
        replays.append(replay(matches, order))
    for idea in ideas:
        scores=[r[idea["id"]] for r in replays]
        idea.update(elo=round(sum(scores)/len(scores),3),
                    elo_order_min=round(min(scores),3), elo_order_max=round(max(scores),3),
                    wins=sum(m["winner"]==idea["id"] for m in matches),
                    ties=sum(m["winner"]=="tie" and idea["id"] in (m["a"],m["b"]) for m in matches))
    ideas.sort(key=lambda i: (-i["elo"],i["id"]))
    output={"as_of":"2026-11-08", "type":"subjective rubric-derived pairwise tournament",
            "pool_sha256":hashlib.sha256(raw_bytes).hexdigest(),
            "limitations":["One critic is also the explicit judge, not a third independent expert.",
                          "All scores/hours/risks are reviewer estimates, not measurements.",
                          "Elo ranks the rubric's judgments, not independent empirical quality.",
                          "Order ranges quantify replay order only, not uncertainty about idea value.",
                          "Other teams' intentions and scores remain UNVERIFIED."],
            "rubric":{"scale":"jury/evidence/time/safety 0..5, higher better", "weights":WEIGHTS,
                      "time":"max(0, 5*(1-hours/8)); hours are estimated owner implementation/review effort",
                      "safety":"5 minus estimated demo risk on 0..5",
                      "decision":"weighted-score difference <0.075 is a tie; otherwise higher wins",
                      "elo":"1500 initial, K=24, 400 logistic scale, one full round robin, 20 seeded order replays; reported mean",
                      "purpose":"Prioritize before freeze; no quantitative expected model gain is claimed."},
            "generator_reply":GENERATOR_REPLY, "ranked":ideas,
            "protected_wildcards":["I28","I29","I30"], "matches":matches}
    (HERE/"tournament.json").write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    # New appendix copy; the generator's raw pool stays unmodified.
    rating={i["id"]:i["elo"] for i in ideas}
    appendix=[{**r,"elo":rating[r["canonical_id"]],"elo_status":"canonical_idea_tournament_rating_not_raw_idea_test"} for r in pool["raw_pool"]]
    (HERE/"raw-pool-with-elo.json").write_text(json.dumps(appendix,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    for rank,i in enumerate(ideas,1):
        print(f"{rank:2} {i['id']} {i['elo']:.1f} {i['title']}")


if __name__=="__main__":
    main()

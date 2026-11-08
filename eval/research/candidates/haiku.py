"""Haiku picker (step 5 of the plan): Claude Haiku 5.5 chooses ONE of the engine's top-5 packages per home (from the
joint package retrieval, k=25 / top 20). It never invents a size: the answer is an enum of candidate ids (structured
outputs), and tools only return JSON computed locally from the TRAINING rows.

Determinism: Haiku 5.5 rejects non-default sampling parameters (temperature 0 is a 400), so instead thinking is disabled,
effort is low, and every answer is cached by sha256(prompt version + model + home + candidates); reruns are identical.
No API key / any API error -> candidate c1 (the retrieval's own top package). Research only: rule 3 ("LLM never sizes")
still holds for the served engine. Validation folds only (FOLDS_ONLY).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from engine.policy.features import features
from engine.policy.neighbours import Neighbours
from research.candidates.pkg import ranked, vocabulary
from research.lib import TARGETS, apply_rules

KIND = "post-processor"
FOLDS_ONLY = True
SETTINGS = {"top5": {"k": 25, "top": 20, "n": 5}}
MODEL = "claude-haiku-5-5"
PROMPT_VERSION = "v1"
ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / "data" / "processed" / "research_cache" / "haiku" / "answers.jsonl"
PRICE_IN, PRICE_OUT = 0.10 / 1e6, 0.50 / 1e6   # $/token, Haiku 5.5 (prompts <= 100K tokens)
INPUT_KEYS = ("demand_kwh", "price_eur_kwh", "has_ev", "ev_km", "has_existing_pv", "existing_pv_kwp", "has_existing_storage",
              "existing_storage_kwh", "has_existing_wallbox", "heating_type", "heat_demand_kwh", "load_family")

SYSTEM = """You help a solar installer draft an offer. An engine proposes candidate packages for one home; you pick the one
the installer's own expert planner would most likely offer. A pick counts as right when PV is within 20%, battery within
25%, heat pump within 25% of the expert's, and wallbox matches (included or not). You never invent sizes: answer only with
a candidate id. Use the tools (all data comes from this installer's past offers) before answering when the choice is not
obvious. Final answer: JSON with the chosen id."""

TOOLS = [
    {"name": "candidate_details", "strict": True,
     "description": "The candidate packages with: share of the 25 most similar past homes each one would have matched, and how often the installer sold it.",
     "input_schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False}},
    {"name": "similar_homes", "strict": True,
     "description": "The expert designs (kWp, battery kWh, heat pump kW, wallbox) of the k most similar past homes, nearest first, with their inputs.",
     "input_schema": {"type": "object", "properties": {"k": {"type": "integer", "enum": [5, 10, 25]}}, "required": ["k"],
                      "additionalProperties": False}},
    {"name": "installer_ladder", "strict": True,
     "description": "This installer's most frequent packages and its median battery kWh per PV kWp.",
     "input_schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False}},
]

_lock = threading.Lock()


def _clean(v):
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (int, float, np.floating, np.integer)):
        return None if v != v else round(float(v), 2)
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)


def _pkg(p) -> dict:
    return {"pv_kwp": round(float(p[0]), 2), "battery_kwh": round(float(p[1]), 2), "heat_pump_kw": round(float(p[2]), 2),
            "wallbox": bool(p[3] > 0)}


def _load_cache() -> dict:
    out = {}
    if CACHE.exists():
        for line in CACHE.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                out[r["key"]] = r
            except ValueError:
                pass
    return out


def _client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip().strip('"')
    if not os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OFFLINE") == "1":
        return None
    extra = os.environ.get("RESEARCH_PYLIB")  # SDK installed outside the engine venv (research only)
    if extra and extra not in sys.path:
        sys.path.insert(0, extra)
    import anthropic
    return anthropic.Anthropic(max_retries=4)


def ask(client, home: dict, cands: list[dict], tools: dict) -> tuple[str, dict]:
    """One manual tool loop -> (candidate id, usage). Raises on API errors (caller falls back to c1)."""
    ids = [c["id"] for c in cands]
    fmt = {"format": {"type": "json_schema", "schema": {"type": "object", "properties": {"choice": {"type": "string", "enum": ids}},
                                                        "required": ["choice"], "additionalProperties": False}},
           "effort": "low"}
    msgs = [{"role": "user", "content": "Home inputs (unknown = null):\n" + json.dumps(home) +
             "\n\nCandidate packages:\n" + json.dumps(cands) + "\n\nWhich candidate id?"}]
    usage = {"in": 0, "out": 0, "turns": 0}
    for _ in range(5):
        r = client.messages.create(model=MODEL, max_tokens=2000, system=SYSTEM, tools=TOOLS, messages=msgs,
                                   output_config=fmt, thinking={"type": "disabled"})
        usage["in"] += r.usage.input_tokens
        usage["out"] += r.usage.output_tokens
        usage["turns"] += 1
        if r.stop_reason != "tool_use":
            text = next((b.text for b in r.content if b.type == "text"), "")
            choice = json.loads(text)["choice"] if text else ids[0]
            return (choice if choice in ids else ids[0]), usage
        msgs.append({"role": "assistant", "content": r.content})
        results = []
        for b in r.content:
            if b.type == "tool_use":
                fn = tools[b.name]
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(fn(**(b.input or {})))})
        msgs.append({"role": "user", "content": results})
    return ids[0], usage


def fit(train: pd.DataFrame, setting: dict, ctx):
    catalog = ctx.base().catalog
    installers = tuple(sorted(train.installer_id.astype(str).unique()))
    nn = Neighbours().fit(features(train, installers), train[list(TARGETS)].astype(float), setting["k"])
    vocab, vocab_n = vocabulary(train, 10), train.installer_id.astype(str).value_counts()
    tr_rows = train.reset_index(drop=True)

    def predict(test: pd.DataFrame):
        r = ranked(train, test, setting["k"], setting["top"])
        idx = nn.nn.kneighbors(nn._z(features(test, installers)), return_distance=False)
        client, cache = _client(), _load_cache()
        jobs = []
        for i, ((pk, sc), row, nb) in enumerate(zip(r, test.to_dict("records"), idx)):
            inst = str(row["installer_id"])
            Yi = train[list(TARGETS)].astype(float)
            g = Yi[train.installer_id.astype(str) == inst].assign(wallbox_kw=lambda d: np.where(d.wallbox_kw > 0, 11.0, 0.0)).round(1)
            vc = g.value_counts()
            cands = [{"id": f"c{j + 1}", **_pkg(p)} for j, p in enumerate(pk[: setting["n"]])]
            details = [{**c, "similar_homes_matched": round(float(s), 3),
                        "installer_share": round(float(vc.get(tuple(np.round(p, 1)), 0)) / max(len(g), 1), 3)}
                       for c, p, s in zip(cands, pk, sc)]
            near = [{"design": _pkg([tr_rows.at[j, t] if tr_rows.at[j, t] == tr_rows.at[j, t] else -1 for t in TARGETS]),
                     "inputs": {k: _clean(tr_rows.at[j, k]) for k in ("demand_kwh", "has_ev", "heating_type") if k in tr_rows}}
                    for j in nb]
            lad = vocab.get(inst, vocab["all"])
            gi = g[(g.pv_kwp > 0) & (g.battery_kwh > 0)]
            ladder = {"top_packages": [_pkg(p) for p in lad],
                      "median_battery_kwh_per_pv_kwp": round(float((gi.battery_kwh / gi.pv_kwp).median()), 3) if len(gi) else None,
                      "n_offers": int(vocab_n.get(inst, 0))}
            home = {"installer": inst, **{k: _clean(row.get(k)) for k in INPUT_KEYS}}
            tools = {"candidate_details": lambda d=details: d, "similar_homes": lambda k=10, n=near: n[:k],
                     "installer_ladder": lambda l=ladder: l}
            key = hashlib.sha256(json.dumps([PROMPT_VERSION, MODEL, home, details, near, ladder], sort_keys=True).encode()).hexdigest()
            jobs.append((i, key, home, cands, tools))
        todo = [j for j in jobs if j[1] not in cache]
        est = len(todo) * 3 * 2500
        print(f"  haiku: {len(jobs)} homes, {len(todo)} uncached; est. <= {est / 1e6:.1f}M input tokens (~${est * PRICE_IN + len(todo) * 3 * 60 * PRICE_OUT:.2f})"
              + ("" if client else "  [no API key/OFFLINE: candidate c1 for all]"), flush=True)

        def work(job):
            i, key, home, cands, tools = job
            try:
                choice, usage = ask(client, home, cands, tools)
            except Exception as e:  # noqa: BLE001 - any API failure falls back to the retrieval's top package
                return {"key": key, "choice": "c1", "error": type(e).__name__}
            rec = {"key": key, "choice": choice, "usage": usage}
            with _lock:
                CACHE.parent.mkdir(parents=True, exist_ok=True)
                with CACHE.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec) + "\n")
            return rec

        if client and todo:
            with ThreadPoolExecutor(8) as ex:
                for rec in ex.map(work, todo):
                    cache.setdefault(rec["key"], rec)
        errs = sum(1 for _, k, *_ in jobs if cache.get(k, {}).get("error"))
        picks = [int(cache.get(k, {"choice": "c1"})["choice"][1:]) - 1 for _, k, *_ in jobs]
        print(f"  haiku: picked c1 for {sum(p == 0 for p in picks)}/{len(picks)} homes; {errs} API errors", flush=True)
        sizes = pd.DataFrame([pk[min(p, len(pk) - 1)] for p, (pk, _) in zip(picks, r)], columns=list(TARGETS), index=test.index)
        return apply_rules(test, sizes, catalog), None
    return predict

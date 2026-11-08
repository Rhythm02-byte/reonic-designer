"""FastAPI app. Run: uvicorn engine.api.main:app --reload --port 8000

GET  /health         liveness + engine version
GET  /meta           form fields, target catalogs, installers, synthetic flag
POST /design         policy + simulator: proposal, alternatives, metrics, curves, physics, flags (accepts locks)
POST /simulate       homeowner variant switching: simulator only
POST /validate       planner's own system: rule flags, similar-home percentiles, metrics
GET  /eval/summary   compact view of eval/results/latest.json (404 until an eval has run)
GET  /holdout?n=12   real past 2026 homes: expert design vs ours (env DEMO_HOLDOUT=0 -> 403)
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")  # before sklearn loads: see threadpool_limits below
import threading
from contextlib import asynccontextmanager
from functools import lru_cache

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from threadpoolctl import threadpool_limits

# One request designs one home: per-call OpenMP thread start-up in sklearn's boosted trees costs more than it saves
# (cached /design ~450 ms -> under 150 ms). Training (eval/, train.py) runs in other processes and keeps all threads.
threadpool_limits(1)

from engine import demo
from engine.design import ENGINE_VERSION, Store, _module_wp, design, simulate, start_physics_pool, validate
from engine.models.schemas import (
    DesignRequest, DesignResponse, EvalSummary, HoldoutResponse, MetaResponse, Metrics, SimulateRequest, ValidateRequest,
    ValidateResponse,
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Warm the holdout (it trains a designer, ~7 s) in the background so the first /holdout call is instant;
    start the process pool that simulates the "Ask next" answer homes in parallel (ENGINE_PHYS_WORKERS=0 turns it off)."""
    if os.environ.get("ENGINE_WARM", "1") != "0":
        threading.Thread(target=start_physics_pool, daemon=True).start()
    if os.environ.get("DEMO_HOLDOUT", "1") != "0" and os.environ.get("ENGINE_WARM", "1") != "0":
        demo.warm_in_background(get_holdout())
    yield


app = FastAPI(title="thinc! engine", version=ENGINE_VERSION, lifespan=lifespan)
ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000", *filter(None, os.environ.get("ENGINE_CORS_ORIGINS", "").split(","))]
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["*"], allow_headers=["*"])


@lru_cache
def get_store() -> Store:
    return Store()


@lru_cache
def get_holdout() -> demo.HoldoutService | None:
    """Holdout over the processed data of the default store (None when there is none). Overridden in tests."""
    store = get_store()
    pp, op = store.dir / "projects.parquet", store.dir / "options.parquet"
    if not (pp.exists() and op.exists()):
        return None
    from engine.policy.features import training_frame
    D = training_frame(pd.read_parquet(pp), pd.read_parquet(op))
    return demo.HoldoutService(D, wp_for=lambda inst: _module_wp(store, inst), synthetic=store.synthetic)


@app.get("/health")
def health(store: Store = Depends(get_store)) -> dict:
    return {"status": "ok", "engineVersion": store.engine_version}


@app.get("/meta", response_model=MetaResponse, response_model_by_alias=True)
def get_meta(store: Store = Depends(get_store)) -> MetaResponse:
    return demo.meta(store.designer, store.installers, store.synthetic, store.engine_version)


@app.post("/design", response_model=DesignResponse, response_model_by_alias=True)
def post_design(req: DesignRequest, store: Store = Depends(get_store)) -> DesignResponse:
    return design(req, store)


@app.post("/simulate", response_model=Metrics, response_model_by_alias=True)
def post_simulate(req: SimulateRequest) -> Metrics:
    return simulate(req)


@app.post("/validate", response_model=ValidateResponse, response_model_by_alias=True)
def post_validate(req: ValidateRequest, store: Store = Depends(get_store)) -> ValidateResponse:
    return validate(req, store)


@app.get("/eval/summary", response_model=EvalSummary, response_model_by_alias=True)
def get_eval_summary() -> EvalSummary:
    s = demo.eval_summary()
    if s is None:
        raise HTTPException(status_code=404, detail="no eval results yet (run: npm run eval)")
    return s


@app.get("/holdout", response_model=HoldoutResponse, response_model_by_alias=True)
def get_holdout_rows(n: int = Query(12, ge=1, le=50), svc: demo.HoldoutService | None = Depends(get_holdout)) -> HoldoutResponse:
    if os.environ.get("DEMO_HOLDOUT", "1") == "0":
        raise HTTPException(status_code=403, detail="holdout disabled (DEMO_HOLDOUT=0)")
    if svc is None or not svc.has_test():
        raise HTTPException(status_code=404, detail="no held-out homes available")
    return svc.rows(n)

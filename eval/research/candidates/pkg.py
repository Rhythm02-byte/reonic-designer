"""Joint package retrieval (Codex ceiling report, method 1; idea 1 in the 50).

Candidates = the installer's N most frequent complete training packages (PV, battery, heat pump, wallbox; sizes rounded
to 0.1). Score of a package for a home = share of its k nearest TRAINING homes whose expert design the package hits
within tolerance on all four components (the whole-design metric itself). Ties / all-zero -> the more frequent package.
Hard rules R01-R05 + snapping still run on the chosen package. Packages with an unknown size are not servable and dropped.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine.policy.features import features
from engine.policy.neighbours import Neighbours
from research.lib import TARGETS, apply_rules, hits

KIND = "post-processor"
SETTINGS = {"k25_top10": {"k": 25, "top": 10}, "k25_top20": {"k": 25, "top": 20}, "k50_top20": {"k": 50, "top": 20}}


def vocabulary(train: pd.DataFrame, top: int) -> dict[str, np.ndarray]:
    """installer (and "all") -> (top, 4) array of the most frequent fully-sized packages, most frequent first."""
    Y = train[list(TARGETS)].astype(float)
    Y = Y.assign(wallbox_kw=np.where(Y.wallbox_kw > 0, 11.0, 0.0)).round(1)
    ok = Y.notna().all(axis=1)
    out = {}
    for key, g in [("all", Y[ok])] + [(str(i), Y[ok & (train.installer_id.astype(str) == i)]) for i in train.installer_id.astype(str).unique()]:
        if len(g):
            vc = g.value_counts()
            out[key] = np.array([list(t) for t in vc.index[:top]], dtype=float)
    return out


def package_scores(pk: np.ndarray, nb: pd.DataFrame) -> np.ndarray:
    """(n_packages,) share of neighbour designs each package hits on all four components."""
    ok = np.ones((len(pk), len(nb)), dtype=bool)
    for j, t in enumerate(TARGETS):
        ok &= hits(np.repeat(pk[:, j:j + 1], len(nb), axis=1), np.broadcast_to(nb[t].to_numpy(float), (len(pk), len(nb))), t)
    return ok.mean(axis=1)


def ranked(train: pd.DataFrame, test: pd.DataFrame, k: int, top: int, ctx=None):
    """-> list per test row of (packages (n,4), scores (n,)) sorted best first (used by the Haiku picker too)."""
    installers = tuple(sorted(train.installer_id.astype(str).unique()))
    Xtr, Xte = features(train, installers), features(test, installers)
    nn = Neighbours().fit(Xtr, train[list(TARGETS)].astype(float), k)
    vocab = vocabulary(train, top)
    out = []
    for inst, nb in zip(test.installer_id.astype(str), nn.query(Xte)):
        pk = vocab.get(inst, vocab["all"])
        s = package_scores(pk, nb)
        order = np.argsort(-s, kind="stable")  # stable: ties keep frequency order
        out.append((pk[order], s[order]))
    return out


def fit(train: pd.DataFrame, setting: dict, ctx):
    catalog = ctx.base().catalog

    def predict(test: pd.DataFrame):
        r = ranked(train, test, setting["k"], setting["top"])
        sizes = pd.DataFrame([pk[0] for pk, _ in r], columns=list(TARGETS), index=test.index)
        return apply_rules(test, sizes, catalog), None
    return predict

"""Composite mode (per-component sources), conformal widening, physics / installer-prior features. Synthetic data only."""
import json

import numpy as np
import pandas as pd
import pytest

from engine.policy import rules
from engine.policy.designer import Designer, load_config
from engine.policy.features import TARGETS
from engine.policy.physics import PvPrior
from policy_synth import generate

EMPTY = {"mode": "learned", "pvGate": 0.5, "sources": {}, "conformal": {}, "features": {}, "model": {}}


@pytest.fixture(scope="module")
def df():
    return generate(600, seed=3)


@pytest.fixture(scope="module")
def dz(df):
    return Designer.train(df, config=EMPTY, synthetic=True)


def test_every_source_gives_valid_designs(dz, df):
    sample = df.head(25)
    for comp, srcs in (("pv", ("B0", "B0c", "M1")), ("battery", ("B0", "B0c", "H1", "M1", "SIM")),
                       ("heatPump", ("B0", "B0c", "H1", "M1")), ("wallbox", ("B0", "B0c", "H1", "M1"))):
        for s in srcs:
            out = dz.with_config("composite", sources={comp: s}).design_batch(sample)
            assert list(out.columns) == list(TARGETS) and len(out) == 25
            assert (out.fillna(0) >= 0).all().all()
            assert (out.battery_kwh.fillna(0) <= rules.BATTERY_MAX_KWH_PER_KWP * (out.pv_kwp.fillna(0) + sample.existing_pv_kwp.fillna(0)) + 1e-6).all()


def test_all_m1_composite_equals_learned(dz, df):
    a = dz.with_config("learned").design_batch(df.head(40))
    b = dz.with_config("composite", sources={"pv": "M1", "battery": "M1", "heatPump": "M1", "wallbox": "M1"}).design_batch(df.head(40))
    pd.testing.assert_frame_equal(a, b)


def test_b0_pv_is_installer_median_and_ignores_the_home(dz, df):
    c = dz.with_config("composite", sources={"pv": "B0"})
    out = c.design_batch(df[df.installer_id == "synthB"].head(30))
    assert out.pv_kwp.nunique() == 1
    assert abs(out.pv_kwp.iat[0] - df[(df.installer_id == "synthB") & (df.pv_kwp > 0)].pv_kwp.median()) < 0.11


def test_battery_sees_the_final_pv_of_the_chosen_source(dz, df):
    row = df.iloc[[0]].copy()
    row["existing_pv_kwp"], row["has_existing_pv"] = 0.0, False
    no_pv = dz.with_config("composite", 0.5, {"pv": "M1", "battery": "SIM"})
    # lock PV to zero: a simulator battery cannot exist without PV (R02)
    d = no_pv.design_row(row.iloc[0].to_dict(), locked={"pv_kwp": 0.0})
    assert d.values["battery_kwh"] == 0.0


def test_lock_wins_over_any_source(dz, df):
    row = df.iloc[0].to_dict()
    for s in ("B0", "SIM", "M1"):
        d = dz.with_config("composite", 0.5, {"pv": s, "battery": s}).design_row(row, locked={"pv_kwp": 12.0, "battery_kwh": 10.0})
        assert d.values["pv_kwp"] == 12.0 and d.values["battery_kwh"] == 10.0


def test_reasons_cover_every_component_with_sources(dz, df):
    d = dz.with_config("composite", 0.5, {"pv": "B0c", "battery": "SIM", "heatPump": "H1", "wallbox": "B0"}).design_row(df.iloc[1].to_dict())
    comps = {r.component for r in d.reasons}
    assert {"pv", "battery", "heatPump", "wallbox"} <= comps


def test_unknown_source_is_rejected(dz):
    with pytest.raises(ValueError):
        dz.with_config("composite", sources={"pv": "nope"})
    with pytest.raises(ValueError):
        dz.with_config("composite", sources={"roof": "M1"})


def test_conformal_widens_intervals_and_keeps_order(dz, df):
    base = dz.with_config("composite", sources={"pv": "M1"}, conformal={})
    wide = base.with_config(conformal={"pv_kwp": 2.0, "battery_kwh": 1.0})
    _, e0 = base.design_batch_full(df.head(50))
    _, e1 = wide.design_batch_full(df.head(50))
    assert (e1.hi_pv_kwp >= e0.hi_pv_kwp - 1e-9).all() and (e1.lo_pv_kwp <= e0.lo_pv_kwp + 1e-9).all()
    assert (e1.hi_pv_kwp - e1.lo_pv_kwp > e0.hi_pv_kwp - e0.lo_pv_kwp).any()
    assert (e1.lo_pv_kwp <= e1.hi_pv_kwp).all() and (e1.lo_pv_kwp >= 0).all()
    # intervals of a locked component stay degenerate
    d = wide.design_row(df.iloc[0].to_dict(), locked={"pv_kwp": 8.0})
    assert d.intervals["pv_kwp"] == (8.0, 8.0, 8.0)


def test_load_config_reads_composite_blocks(tmp_path):
    p = tmp_path / "p.json"
    p.write_text(json.dumps({"mode": "composite", "pvGate": 0.5, "sources": {"pv": "M1"}, "conformal": {"pv_kwp": 1.5},
                             "features": {"installerPrior": True}, "model": {"maxDepth": 3}}), encoding="utf-8")
    cfg = load_config(p)
    assert cfg["mode"] == "composite" and cfg["sources"] == {"pv": "M1"} and cfg["conformal"] == {"pv_kwp": 1.5}
    assert cfg["features"] == {"installerPrior": True} and cfg["model"] == {"maxDepth": 3}


def test_installer_prior_is_out_of_fold(df):
    oof = PvPrior.oof(df, folds=5)
    full = PvPrior().fit(df).transform(df)
    assert oof.notna().all() and not np.allclose(oof, full)  # row's own target is not in its prior
    assert abs(oof.median() - full.median()) < 3


def test_trained_with_prior_and_regularisation_round_trips(df, tmp_path):
    cfg = {**EMPTY, "features": {"installerPrior": True}, "model": {"maxDepth": 3, "minLeaf": 40}}
    d = Designer.train(df, config=cfg, synthetic=True)
    assert "inst_pv_prior_kwp" in d._X(df.head(3)).columns
    d.save(tmp_path / "d.joblib")
    d2 = Designer.load(tmp_path / "d.joblib", apply_config=False)
    pd.testing.assert_frame_equal(d.design_batch(df.head(20)), d2.design_batch(df.head(20)))
    assert d2.design_row(df.iloc[0].to_dict()).values["pv_kwp"] >= 0


def test_physics_features_added_when_enabled(df):
    d = Designer.train(df.head(80), config={**EMPTY, "features": {"physics": True}}, synthetic=True)
    X = d._X(df.head(2))
    assert {"sim_pv_opt_kwp", "sim_battery_opt_kwh"} <= set(X.columns) and X.sim_pv_opt_kwp.notna().all()

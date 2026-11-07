import numpy as np
import pandas as pd

from reonic import simulate
from reonic.schema import INPUT_FIELDS


def _real():
    rng = np.random.default_rng(0)
    n = 200
    return pd.DataFrame({
        "annual_consumption_kwh": rng.uniform(2000, 8000, n), "electricity_price_eur_kwh": 0.35,
        "energy_price_increase": 0.03, "has_ev": rng.random(n) < 0.3, "ev_km_per_year": 12000.0,
        "has_flexible_tariff": 0.0, "load_profile": "H0", "heating_type": "gas", "heating_demand_kwh": 15000.0,
        "existing_pv_kwp": 0.0, "existing_battery_kwh": 0.0, "has_existing_wallbox": False,
        "household_size": np.nan, "heated_area_m2": np.nan,
    })


def test_wallbox_only_with_ev():
    s = simulate.simulate(_real(), n=500, seed=1)
    assert (s.loc[~s.has_ev.astype(bool), "wallbox_kw"] == 0).all()


def test_heat_pump_only_for_fossil_heating_with_known_demand():
    s = simulate.simulate(_real(), n=500, seed=1, hp_share=0.5)
    hp = s[s.heat_pump_kw > 0]
    assert len(hp) > 0 and hp.heating_type.isin(["gas", "oil"]).all() and (hp.heating_demand_kwh > 0).all()


def test_masking_keeps_targets_and_blanks_inputs():
    s = simulate.simulate(_real(), n=400, seed=2)
    m = simulate.mask_inputs(s, 0.5, seed=3)
    assert m["annual_consumption_kwh"].isna().mean() > 0.3
    pd.testing.assert_series_equal(m["pv_kwp"], s["pv_kwp"])
    assert set(INPUT_FIELDS) <= set(m.columns)

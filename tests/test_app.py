"""The planner app's demo flow, driven headlessly on synthetic data (the real export cannot be in the repo)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")
KEYS = ["consumption", "has_ev", "ev_km", "heating", "heat_demand", "pv_existing"]


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    import os

    os.environ["REONIC_DATA"] = str(tmp_path_factory.mktemp("d") / "synthetic.csv")
    at = AppTest.from_file(APP, default_timeout=300).run()
    yield at
    os.environ.pop("REONIC_DATA", None)


def test_app_renders_and_offers_examples(app):
    assert not app.exception
    options = app.selectbox(key="example").options
    assert options[0] == "Enter your own home" and len(options) >= 3


def test_every_example_loads_without_error_and_is_a_different_home(app):
    seen = []
    for option in app.selectbox(key="example").options[1:]:
        app.selectbox(key="example").select(option).run()
        assert not app.exception, option
        seen.append(tuple(app.session_state[k] for k in KEYS))
    assert len(set(seen)) == len(seen), "two examples loaded the same home"


def test_wallbox_shows_its_rule_not_a_probability(app):
    app.selectbox(key="example").select("Enter your own home").run()
    app.checkbox(key="has_ev").check().run()
    wallbox = [m for m in app.metric if m.label == "Wallbox"][0]
    assert wallbox.delta == "rule: has an EV" and wallbox.value != "none"
    app.checkbox(key="has_ev").uncheck().run()
    wallbox = [m for m in app.metric if m.label == "Wallbox"][0]
    assert wallbox.delta == "rule: no EV" and wallbox.value == "none"


def test_planner_override_flows_downstream(app):
    app.checkbox(key="lock_pv_kwp").check().run()
    metrics = {m.label: m for m in app.metric}
    assert metrics["PV"].delta == "planner override" and metrics["PV"].value == "none"
    assert metrics["Battery"].value == "none"  # R02: no PV, so no battery
    assert not app.exception
    app.checkbox(key="lock_pv_kwp").uncheck().run()

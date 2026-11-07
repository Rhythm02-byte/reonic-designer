"""Ask next (value of information) and the roof cap. SYNTHETIC data only (tests/policy_synth.py)."""
import pytest

from engine.ask_next import MAX_ITEMS, ask_next, capex_eur, changed_components
from engine.design import design, _module_wp
from engine.models.schemas import Building, DesignRequest, HomeInputs, Provenance
from engine.policy import rules
from engine.policy.designer import Designer
from policy_synth import generate

FIELDS = {"demandKwh", "building.roofMaxModules", "ev.has", "heating.heatDemandKwh", "existingPv.kwp", "existingStorage.kwh"}


@pytest.fixture(scope="module")
def designer():
    return Designer.train(generate(1200, seed=1), config={"mode": "hybrid", "pvGate": 0.5}, synthetic=True)


def home(**kw) -> HomeInputs:
    return HomeInputs(installer_id="synthB", demand_kwh=4500, heating={"type": "Gas"}, **kw)


def test_stats_are_stored_and_ask_returns_at_most_three(designer):
    assert "all" in designer.ask_stats and designer.ask_stats["all"]["roofKwp"]
    items = ask_next(home(), designer, 450.0)
    assert 1 <= len(items) <= MAX_ITEMS
    for a in items:
        assert a.field in FIELDS and a.question.endswith("?") and a.why
        assert len(a.answers) >= 2 and a.impact.components and a.impact.price_swing_eur > 0


def test_default_demand_is_asked_and_entered_fields_are_skipped(designer):
    assert "demandKwh" in {a.field for a in ask_next(home(), designer, 450.0)}
    entered = {k: Provenance(source="entered") for k in ("demandKwh", "ev.has", "building.roofMaxModules", "heating.heatDemandKwh")}
    got = {a.field for a in ask_next(home(provenance=entered), designer, 450.0)}
    assert not got & {"demandKwh", "ev.has", "building.roofMaxModules", "heating.heatDemandKwh"}
    # a known roof or a real demand are not asked either
    got = {a.field for a in ask_next(home(building=Building(roof_max_modules=20)), designer, 450.0)}
    assert "building.roofMaxModules" not in got
    assert "demandKwh" not in {a.field for a in ask_next(home().model_copy(update={"demand_kwh": 5200.0}), designer, 450.0)}


def test_locked_component_is_not_counted(designer):
    items = ask_next(home(), designer, 450.0, locks=("pv",))
    assert all("pv" not in a.impact.components for a in items)
    assert "building.roofMaxModules" not in {a.field for a in items}


def test_changed_components_uses_set_and_catalog_steps():
    a = {"pv_kwp": 8.0, "battery_kwh": 7.0, "heat_pump_kw": 0.0, "wallbox_kw": 0.0}
    assert changed_components(a, {**a, "wallbox_kw": 11.0}, 450.0, 2.0, set()) == ["wallbox"]
    assert changed_components(a, {**a, "pv_kwp": 8.45}, 450.0, 2.0, set()) == []
    assert changed_components(a, {**a, "pv_kwp": 9.0}, 450.0, 2.0, set()) == ["pv"]
    assert changed_components(a, {**a, "battery_kwh": 9.0}, 450.0, 2.0, {"battery"}) == []
    assert capex_eur({**a, "wallbox_kw": 11.0}) > capex_eur(a) > 0


def test_roof_caps_pv_modules(designer, processed, tmp_path):
    from engine.design import Store
    path = tmp_path / "d.joblib"
    designer.save(path)
    store = Store(processed, model_path=path)
    big = home().model_copy(update={"demand_kwh": 12000.0})
    free = design(DesignRequest(inputs=big), store)
    assert free.proposal.pv.modules > 12
    capped_in = big.model_copy(update={"building": Building(roof_max_modules=12)})
    capped = design(DesignRequest(inputs=capped_in), store)
    assert capped.proposal.pv.modules <= 12
    assert any(r.code == "R07" for r in capped.reasons)
    assert capped.provenance["building.roofMaxModules"].source == "national_default"  # not marked entered by the caller
    assert capped.proposal.battery is None or capped.proposal.battery.kwh <= 2.0 * capped.proposal.pv.kwp  # R04 still holds downstream


def test_r07_flags_a_locked_pv_over_the_roof():
    ctx = {"heating_type": None, "existing_pv_kwp": 0.0, "roof_max_kwp": 4.5, "roof_max_modules": 10}
    v, applied, flags = rules.apply_one("pv_kwp", 9.0, {}, ctx, {})
    assert v == 4.5 and applied[0].id == "R07"
    v, applied, flags = rules.apply_one("pv_kwp", 9.0, {}, ctx, {}, locked=True)
    assert v == 9.0 and flags[0].id == "R07" and not applied
    assert rules.apply_one("pv_kwp", 9.0, {}, {**ctx, "roof_max_kwp": None}, {})[0] == 9.0

"""Tiny/synthetic fixtures catch source-specific errors, never fit private data."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pack.mastr import eligible, link_colocated, storage_capacity_map, attach_storage_capacity
from pack.build_profiles import complete_hourly
from profiles import load_profiles, normalized
from benchmark import no_network
from pack.public_priors import sample_public_homes


def test_mastr_filters_gross_rooftop_household_operating_year():
    base = {"EinheitBetriebsstatus": "In Betrieb", "EinheitSystemstatus": "Aktiviert", "Land": "Deutschland",
            "Inbetriebnahmedatum": "2024-03-12", "Bruttoleistung": "9.5",
            "Lage": "Bauliche Anlagen (Hausdach, Gebäude und Fassade)", "Nutzungsbereich": "Haushalt"}
    variants = [base, {**base, "Lage": "Freifläche"}, {**base, "Nutzungsbereich": "Industrie"},
                {**base, "Bruttoleistung": "9000"}, {**base, "Inbetriebnahmedatum": "2027-01-01"},
                {**base, "EinheitBetriebsstatus": "In Planung"}]
    assert eligible(pd.DataFrame(variants), "solar").tolist() == [True, False, False, False, False, False]


def test_linker_requires_both_ids_and_rejects_empty_ambiguous_links():
    def frame(rows):
        return pd.DataFrame(rows, columns=["LokationMastrNummer", "AnlagenbetreiberMastrNummer", "value"])
    pv = frame([("L1", "A1", 9), ("", "", 5), ("L2", "A2", 8), ("L2", "A2", 6), ("L3", "A3", 10)])
    battery = frame([("L1", "A1", 8), ("", "", 4), ("L2", "A2", 9), ("L3", "OTHER", 10)])
    result = link_colocated(pv, battery)
    assert len(result) == 1
    assert result.iloc[0].value_pv == 9
    assert result.iloc[0].value_battery == 8


def test_capacity_is_from_installation_and_both_registry_references_must_agree():
    installations = pd.DataFrame([
        ["SPE1", "9.6", "SEE000000000001", "In Betrieb"],
        ["SPE2", "20", "SEE000000000002,SEE000000000003", "In Betrieb"],
        ["SPE3", "15", "SEE000000000004", "In Planung"],
    ], columns=["MastrNummer", "NutzbareSpeicherkapazitaet", "VerknuepfteEinheit", "AnlageBetriebsstatus"])
    mapping = storage_capacity_map(installations)
    units = pd.DataFrame([["SPE1", "SEE000000000001"], ["SPE1", "SEE000000000999"], ["SPE2", "SEE000000000002"]],
                         columns=["SpeMastrNummer", "EinheitMastrNummer"])
    result = attach_storage_capacity(units, mapping)
    assert result.NutzbareSpeicherkapazitaet.tolist() == ["9.6", "", ""]


def test_complete_year_removes_only_leap_day_and_rejects_missing():
    idx = pd.date_range("2016-01-01", "2017-01-01", inclusive="left", freq="h", tz="UTC")
    assert complete_hourly(idx, np.ones(len(idx)), 2016).sum() == 8760
    broken = np.ones(len(idx))
    broken[123] = np.nan
    with pytest.raises(ValueError, match="Incomplete"):
        complete_hourly(idx, broken, 2016)
    with pytest.raises(ValueError, match="Duplicate"):
        complete_hourly(idx.append(idx[:1]), np.ones(len(idx) + 1), 2016)


def test_profile_loader_normalizes_energy_and_rejects_invalid(tmp_path):
    path = tmp_path / "profiles.npz"
    np.savez(path, example=np.ones(8760))
    assert load_profiles(4500, path)["example"].sum() == pytest.approx(4500)
    with pytest.raises(ValueError):
        normalized(np.full(8760, -1))
    with pytest.raises(ValueError):
        normalized(np.zeros(8760))
    with pytest.raises(ValueError):
        load_profiles(float("inf"), path)


def test_offline_guard_blocks_actual_socket_entrypoint():
    import socket
    with no_network() as attempted:
        with pytest.raises(RuntimeError, match="forbidden"):
            socket.create_connection(("example.com", 443))
    assert attempted == ["outbound_socket"]


def test_public_marginal_sampler_is_replayable_and_preserves_unknown_heat():
    first, manifest = sample_public_homes(200, ("fixture_installer",), seed=110701)
    second, _ = sample_public_homes(200, ("fixture_installer",), seed=110701)
    assert [h.model_dump() for h in first] == [h.model_dump() for h in second]
    assert len(first) == 200
    assert all(h.demand_kwh > 0 and np.isfinite(h.demand_kwh) for h in first)
    assert manifest["realized_counts"]["persons_topcoded_5"]["1"] > manifest["realized_counts"]["persons_topcoded_5"]["5"]
    unknown = [h for h in first if h.heating.type == "Unknown"]
    assert unknown and all(h.heating.heat_demand_kwh is None for h in unknown)

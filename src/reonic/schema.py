"""Canonical field names. data.py turns Reonic's raw export into exactly these columns."""
from dataclasses import dataclass, field

HEATING_TYPES = ("gas", "oil", "heat_pump", "electric", "district", "other")
LOAD_PROFILES = ("H0", "FamilyOfFour", "SeniorOnePerson", "PartTimeOnePerson", "HomeOfficeOnePerson", "CustomFromEditor")

NUMERIC_FIELDS = (
    "annual_consumption_kwh",
    "electricity_price_eur_kwh",
    "energy_price_increase",
    "ev_km_per_year",
    "heating_demand_kwh",
    "existing_pv_kwp",
    "existing_battery_kwh",
    "household_size",  # almost always blank in the real data
    "heated_area_m2",  # almost always blank in the real data
)
BOOL_FIELDS = ("has_ev", "has_flexible_tariff", "has_existing_wallbox")
CATEGORICAL_FIELDS = ("heating_type", "load_profile")
INPUT_FIELDS = NUMERIC_FIELDS + BOOL_FIELDS + CATEGORICAL_FIELDS

# A component that was not offered has size 0. NaN = offered but size unknown (PV only).
TARGETS = ("pv_kwp", "battery_kwh", "heat_pump_kw", "wallbox_kw")
LABEL = {"pv_kwp": "PV", "battery_kwh": "Battery", "heat_pump_kw": "Heat pump", "wallbox_kw": "Wallbox"}
UNIT = {"pv_kwp": "kWp", "battery_kwh": "kWh", "heat_pump_kw": "kW", "wallbox_kw": "kW"}


@dataclass
class HomeInputs:
    """What a planner knows at first contact. None = unknown, never guessed."""

    annual_consumption_kwh: float | None = None
    electricity_price_eur_kwh: float | None = None
    energy_price_increase: float | None = None
    has_ev: bool | None = None
    ev_km_per_year: float | None = None
    has_flexible_tariff: bool | None = None
    load_profile: str | None = None
    heating_type: str | None = None
    heating_demand_kwh: float | None = None
    existing_pv_kwp: float | None = None
    existing_battery_kwh: float | None = None
    has_existing_wallbox: bool | None = None
    household_size: int | None = None
    heated_area_m2: float | None = None


@dataclass
class Design:
    pv_kwp: float
    battery_kwh: float
    heat_pump_kw: float
    wallbox_kw: float
    probability: dict[str, float] = field(default_factory=dict)  # model's P(component included)
    explanation: list[str] = field(default_factory=list)
    rules_applied: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    def values(self) -> dict[str, float]:
        return {t: getattr(self, t) for t in TARGETS}

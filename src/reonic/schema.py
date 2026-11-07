"""Canonical field names. Everything downstream uses these; data.COLUMN_MAP maps Reonic's raw columns onto them."""
from dataclasses import dataclass, field

HEATING_TYPES = ("gas", "oil", "heat_pump", "electric", "district", "other")

NUMERIC_FIELDS = (
    "annual_consumption_kwh",
    "household_size",
    "ev_km_per_year",
    "electricity_price_eur_kwh",
    "feed_in_tariff_eur_kwh",
    "budget_eur",
    "roof_area_m2",
    "heated_area_m2",
)
INPUT_FIELDS = NUMERIC_FIELDS + ("heating_type", "has_ev")

# A component that was not installed has size 0.
TARGETS = ("pv_kwp", "battery_kwh", "heat_pump_kw")
LABEL = {"pv_kwp": "PV", "battery_kwh": "Battery", "heat_pump_kw": "Heat pump"}
UNIT = {"pv_kwp": "kWp", "battery_kwh": "kWh", "heat_pump_kw": "kW"}


@dataclass
class HomeInputs:
    """What a planner types in. None = unknown, never guessed."""

    annual_consumption_kwh: float | None = None
    household_size: int | None = None
    heating_type: str | None = None
    has_ev: bool | None = None
    ev_km_per_year: float | None = None
    electricity_price_eur_kwh: float | None = None
    feed_in_tariff_eur_kwh: float | None = None
    budget_eur: float | None = None
    roof_area_m2: float | None = None
    heated_area_m2: float | None = None


@dataclass
class Design:
    pv_kwp: float
    battery_kwh: float
    heat_pump_kw: float
    probability: dict[str, float] = field(default_factory=dict)  # model's P(component included)
    explanation: list[str] = field(default_factory=list)
    rules_applied: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    def values(self) -> dict[str, float]:
        return {t: getattr(self, t) for t in TARGETS}

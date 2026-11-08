"""Warnings for inputs that are possible to type but not plausible for a home.

The design engine takes whatever the planner enters; before this module an implausible input (60 kWh a year, an 80 kWp
"existing" system) produced a full proposal with no warning at all. These flags only warn: they never change a number
and never refuse an input (refusing is the schema's job). Thresholds are deliberately wide, so a flag means "check
this", not "this is wrong". Codes are new; the contract's Flag.code is a free string, so no contract change.
"""
from __future__ import annotations

from engine.models.schemas import Flag, HomeInputs

DEMAND_LOW_KWH = 500          # a lived-in home uses more than this per year
DEMAND_HIGH_KWH = 50_000      # beyond this it is a business, not a home
EV_KM_HIGH = 100_000          # per year
EXISTING_PV_HIGH_KWP = 30.0   # the residential ceiling used by R03
EXISTING_STORAGE_HIGH_KWH = 100.0
MAX_KWP_PER_ROOF_MODULE = 0.5  # 500 Wp, above any module in the catalogue


def default_demand_flag(i: HomeInputs) -> Flag | None:
    """4,500 kWh that the planner did not enter. The learned policy has a feature for "demand left at the default", so
    exactly 4,500 can get a different proposal (even no PV) than 4,499 or 4,501. Warn loudly; the numbers stay as they are."""
    if abs(i.demand_kwh - 4500.0) < 1e-6 and "demandKwh" not in i.provenance:  # an entered 4,500 is real
        return Flag(severity="warn", code="DEMAND_DEFAULT_LIKE", message=(
            "Consumption is still the 4,500 kWh default. The model treats exactly 4,500 as 'not entered', so this proposal "
            "(PV in particular) can differ from the one for 4,499 or 4,501 kWh. Enter the real figure from the electricity bill."))
    return None


def input_flags(i: HomeInputs) -> list[Flag]:
    out: list[Flag] = []
    if 0 < i.demand_kwh < DEMAND_LOW_KWH:
        out.append(Flag(severity="warn", code="INPUT_DEMAND_LOW", message=(
            f"{i.demand_kwh:,.0f} kWh a year is unrealistically low for a home; check the consumption. "
            "The proposal is not reliable for this input.")))
    if i.demand_kwh > DEMAND_HIGH_KWH:
        out.append(Flag(severity="warn", code="INPUT_DEMAND_HIGH", message=(
            f"{i.demand_kwh:,.0f} kWh a year is far above a home's consumption; check the unit (kWh, not Wh). "
            "The proposal is not reliable for this input.")))
    if i.ev.has and i.ev.km_per_year is not None:
        if i.ev.km_per_year <= 0:
            out.append(Flag(severity="warn", code="INPUT_EV_KM", component="wallbox",
                            message="An electric car with 0 km a year adds no charging load; check the distance."))
        elif i.ev.km_per_year > EV_KM_HIGH:
            out.append(Flag(severity="warn", code="INPUT_EV_KM", component="wallbox",
                            message=f"{i.ev.km_per_year:,.0f} km a year is implausible for one car; check the distance."))
    if i.existing_pv and i.existing_pv.kwp > EXISTING_PV_HIGH_KWP:
        out.append(Flag(severity="warn", code="INPUT_EXISTING_PV", component="pv",
                        message=f"An existing {i.existing_pv.kwp:g} kWp system is above the {EXISTING_PV_HIGH_KWP:g} kWp residential limit; check the entry."))
    roof = i.building.roof_max_modules if i.building else None
    if i.existing_pv and roof is not None and roof >= 0 and i.existing_pv.kwp > roof * MAX_KWP_PER_ROOF_MODULE:
        out.append(Flag(severity="warn", code="INPUT_EXISTING_PV_ROOF", component="pv",
                        message=f"The existing {i.existing_pv.kwp:g} kWp does not fit a roof limited to {roof} modules; one of the two entries is wrong."))
    if i.existing_storage and i.existing_storage.kwh > EXISTING_STORAGE_HIGH_KWH:
        out.append(Flag(severity="warn", code="INPUT_EXISTING_STORAGE", component="battery",
                        message=f"An existing {i.existing_storage.kwh:g} kWh battery is far above a home's; check the entry."))
    return out

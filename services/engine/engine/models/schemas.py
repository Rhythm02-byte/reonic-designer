"""Pydantic models for the engine <-> web contract (PLAN section 7). JSON is camelCase."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Component = Literal["pv", "battery", "heatPump", "wallbox"]
HeatingType = Literal["Gas", "Oil", "Heatpump", "OtherRenewable", "OtherNonRenewable", "Unknown"]
RoofType = Literal[
    "concrete_tile", "clay_tile", "flat", "flat_ew", "metal", "bitumen",
    "slate", "beaver_tail", "trapezoid", "standing_seam", "other", "unknown",
]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Provenance(CamelModel):
    source: Literal["entered", "extracted", "derived", "installer_default", "national_default"]
    confidence: float = Field(ge=0, le=1, default=1.0)


class Ev(CamelModel):
    has: bool = False
    km_per_year: float | None = None
    planned_year: int | None = None
    smart_charging: bool | None = None


class ExistingPv(CamelModel):
    kwp: float
    tilt_deg: float | None = None
    azimuth_deg: float | None = None
    built_year: int | None = None
    feed_in_eur_kwh: float | None = None
    trusted: bool = True


class ExistingStorage(CamelModel):
    kwh: float
    built_year: int | None = None
    trusted: bool = True


class ExistingWallbox(CamelModel):
    kw: float


class Heating(CamelModel):
    type: HeatingType = "Unknown"
    fuel_kwh: float | None = None
    cost_eur_year: float | None = None
    hp_elec_kwh: float | None = None
    heat_demand_kwh: float | None = None
    planned_switch: bool | None = None


class Building(CamelModel):
    sqm: float | None = None
    built_year: int | None = None
    roof_type: RoofType | None = None
    roof_max_modules: int | None = None
    orientation: str | None = None


class Location(CamelModel):
    lat: float | None = None
    lon: float | None = None
    postcode: str | None = None


class HomeInputs(CamelModel):
    installer_id: str
    demand_kwh: float = 4500.0
    load_profile: str = "H0"
    persons: int | None = None
    home_office: bool | None = None
    price_eur_kwh: float = 0.32
    price_escalation: float = 0.03
    flex_tariff: bool | None = None
    base_price_month: float | None = None
    ev: Ev = Field(default_factory=Ev)
    existing_pv: ExistingPv | None = None
    existing_storage: ExistingStorage | None = None
    existing_wallbox: ExistingWallbox | None = None
    heating: Heating = Field(default_factory=Heating)
    building: Building | None = None
    location: Location | None = None
    provenance: dict[str, Provenance] = Field(default_factory=dict)


class PvDesign(CamelModel):
    modules: int
    module_wp: float
    kwp: float
    product_id: str | None = None


class InverterDesign(CamelModel):
    kw: float
    product_id: str | None = None


class BatteryDesign(CamelModel):
    kwh: float
    product_id: str | None = None


class WallboxDesign(CamelModel):
    kw: float
    product_id: str | None = None


class HeatPumpDesign(CamelModel):
    kw: float
    product_id: str | None = None
    buffer_l: int | None = None
    dhw_l: int | None = None


class SystemDesign(CamelModel):
    id: str = "proposal"
    label: str | None = None
    pv: PvDesign | None = None
    inverter: InverterDesign | None = None
    battery: BatteryDesign | None = None
    wallbox: WallboxDesign | None = None
    heat_pump: HeatPumpDesign | None = None
    locks: list[Component] = Field(default_factory=list)


class Metrics(CamelModel):
    pv_yield_kwh: float | None = None
    self_consumption: float | None = None
    autarky: float | None = None
    grid_import_kwh: float | None = None
    feed_in_kwh: float | None = None
    savings_eur_year: float | None = None
    payback_years: float | None = None
    npv20: float | None = None
    price_eur: float | None = None
    co2t: float | None = None
    full_cycles_per_year: float | None = None
    night_load_kwh: float | None = None
    hourly_typical_days: dict[str, dict[str, list[float]]] | None = Field(
        default=None, description="{summer|winter: {pvKwh, loadKwh, batteryKwh, gridKwh, socKwh: 24 hourly means}}; proposal and /simulate only.")


class Interval(CamelModel):
    p10: float
    p50: float
    p90: float
    prob_included: float | None = None


class ReasonCode(CamelModel):
    code: str
    component: Component
    value: float | str | None = None
    text: str | None = Field(default=None, description="Template sentence for the planner; the LLM may rephrase but never change numbers.")
    evidence: dict[str, float | str | bool | None] = Field(default_factory=dict)


class Flag(CamelModel):
    severity: Literal["info", "warn", "error"]
    code: str
    message: str
    component: Component | None = None
    percentile: float | None = None
    similar_ids: list[str] = Field(default_factory=list)


class SimilarHome(CamelModel):
    project_id: str
    distance: float
    kwp: float | None = None
    battery_kwh: float | None = None


class BomLine(CamelModel):
    """Mirrors Reonic's project_options_parts columns (camelCase)."""
    technology: str | None = None
    line_item_function: str | None = None
    component_type: str | None = None
    component_name: str
    component_brand: str | None = None
    quantity: float = 1
    quantity_units: str | None = None


class AskAnswer(CamelModel):
    label: str = Field(description="Button text, e.g. '12 modules' or 'Yes'.")
    value: bool | float | None = Field(
        default=None, description="What to write into `field`: number, boolean (ev.has) or 0 for 'none' (existingPv.kwp, existingStorage.kwh).")


class AskImpact(CamelModel):
    components: list[Component] = Field(default_factory=list, description="Components whose presence or catalog size changes with the answer.")
    price_swing_eur: float = Field(description="Largest difference in installed price between the possible answers (EUR, market.json mid prices).")


class AskNext(CamelModel):
    """One missing input worth asking for (value of information): re-running the policy over plausible answers changes the design."""
    field: str = Field(description="Dotted camelCase path into HomeInputs: demandKwh, building.roofMaxModules, ev.has, heating.heatDemandKwh, existingPv.kwp, existingStorage.kwh.")
    question: str
    why: str
    impact: AskImpact
    answers: list[AskAnswer] = Field(default_factory=list)


class DesignRequest(CamelModel):
    inputs: HomeInputs
    locks: list[Component] = Field(default_factory=list)
    current: SystemDesign | None = Field(default=None, description="Existing design whose locked components are kept.")


class BatteryPoint(CamelModel):
    """One point of the "why this size" curve (new battery size, PV fixed)."""
    kwh: float
    autarky: float
    self_consumption: float
    savings_eur_year: float
    payback_years: float | None = None
    npv20: float
    full_cycles_per_year: float


class PvPoint(CamelModel):
    """One point of the PV size curve (battery fixed)."""
    kwp: float
    autarky: float
    self_consumption: float
    savings_eur_year: float
    payback_years: float | None = None
    npv20: float
    pv_yield_kwh: float


class Curves(CamelModel):
    battery: list[BatteryPoint] = Field(default_factory=list, description="Installer battery sizes plus 0.")
    pv: list[PvPoint] = Field(default_factory=list, description="Proposed kWp +-40% in module steps.")


class Physics(CamelModel):
    economic_kwh: float = Field(description="Economic battery optimum (max NPV, capped by night load and the 150-350 cycles/yr band); 0 = none pays.")
    max_autarky_kwh: float = Field(description="Smallest battery reaching 99% of the best autarky (uneconomic variant).")
    night_load_kwh: float = Field(description="Average sunset-to-sunrise load per night.")


class DesignResponse(CamelModel):
    proposal: SystemDesign
    alternatives: list[SystemDesign] = Field(default_factory=list)
    metrics: dict[str, Metrics] = Field(default_factory=dict)
    confidence: dict[str, Interval] = Field(default_factory=dict)
    reasons: list[ReasonCode] = Field(default_factory=list)
    flags: list[Flag] = Field(default_factory=list)
    similar: list[SimilarHome] = Field(default_factory=list)
    bom: list[BomLine] = Field(default_factory=list)
    provenance: dict[str, Provenance] = Field(default_factory=dict)
    curves: Curves | None = None
    physics: Physics | None = None
    ask_next: list[AskNext] = Field(default_factory=list, description="At most 3 missing inputs ranked by P(design changes) x price swing; empty when nothing is worth asking.")
    engine_version: str
    latency_ms: float


class ValidateRequest(CamelModel):
    inputs: HomeInputs
    system: SystemDesign = Field(description="The planner's system; missing components count as 'none'.")


class ValidateResponse(CamelModel):
    flags: list[Flag] = Field(default_factory=list, description="Hard-rule violations (R01-R05) and unusual-for-similar-homes checks.")
    percentiles: dict[Component, float | None] = Field(
        default_factory=dict, description="0-100 percentile of the planner's size among similar homes that got the component.")
    similar_share: dict[Component, float] = Field(default_factory=dict, description="Share of similar homes that got the component.")
    n_similar: int = 0
    metrics: Metrics | None = Field(default=None, description="Simulated metrics of the planner's system.")
    engine_version: str


class SimulateRequest(CamelModel):
    inputs: HomeInputs
    system: SystemDesign = Field(description="System to simulate; missing components count as 'none'.")


class MetaField(CamelModel):
    name: str = Field(description="Dotted camelCase path into HomeInputs, e.g. 'ev.has'.")
    kind: Literal["number", "bool", "choice"]
    choices: list[str] = Field(default_factory=list)
    label: str
    unit: str | None = None


class MetaTarget(CamelModel):
    name: Literal["pvKwp", "batteryKwh", "heatPumpKw", "wallboxKw"]
    label: str
    unit: str
    catalog: list[float] = Field(default_factory=list, description="Sizes installers actually use, ascending.")


class MetaResponse(CamelModel):
    fields: list[MetaField]
    targets: list[MetaTarget]
    installers: list[str]
    synthetic: bool = Field(description="True when the engine runs on synthetic/fallback data, not the real dataset.")
    engine_version: str


class EvalModelScores(CamelModel):
    ems: float | None = Field(default=None, description="Expert-match score 0-100 (primary option); every other score is a 0-1 fraction.")
    whole_design: float | None = Field(default=None, description="Share of homes where every component is within tolerance (0-1).")
    pv: float | None = None
    battery: float | None = None
    heat_pump: float | None = None
    wallbox: float | None = None


class EvalSummary(CamelModel):
    split: str
    n_test: int
    chosen: str
    models: dict[str, EvalModelScores]
    selection: dict | None = None
    generated_at: str | None = None
    tolerances: dict[Literal["pv", "battery", "heatPump"], float] = Field(
        default_factory=dict, description="Relative size error that still counts as matching the expert, per component.")


class HoldoutSystem(CamelModel):
    pv_kwp: float | None = None
    battery_kwh: float | None = None
    heat_pump_kw: float | None = None
    wallbox_kw: float | None = None


class HoldoutRow(CamelModel):
    project_id: str
    installer_id: str
    inputs: HomeInputs
    expert: HoldoutSystem
    ours: HoldoutSystem


class HoldoutResponse(CamelModel):
    rows: list[HoldoutRow]

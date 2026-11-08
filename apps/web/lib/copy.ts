// Wording, formatting and the planner -> homeowner offer link.
import { TARGETS, type Inputs, type InputValue, type Target, type Values } from "./api";
export const MARGIN_PCT = 0.22; // installer margin on the offer total, from Faris's spike

export const PANEL_KWP = 0.45; // Reonic's modules are 450 Wp (src/reonic/data.py MODULE_WP)
// Same as src/reonic/schema.py LABEL / UNIT
export const LABEL: Record<Target, string> = { pv_kwp: "PV", battery_kwh: "Battery", heat_pump_kw: "Heat pump", wallbox_kw: "Wallbox" };
export const UNIT: Record<Target, string> = { pv_kwp: "kWp", battery_kwh: "kWh", heat_pump_kw: "kW", wallbox_kw: "kW" };

// Every input the designer API takes (src/reonic/schema.py), grouped as the planner sees them.
// `scale` shows a stored fraction as a percentage (0.03 -> 3).
export type FieldCopy = { label: string; unit?: string; step?: number; scale?: number };
export const FIELD_GROUPS: { title: string; existing?: boolean; fields: Record<string, FieldCopy> }[] = [
  {
    title: "Home & household",
    fields: {
      household_size: { label: "People in household", step: 1 },
      heated_area_m2: { label: "Heated area", unit: "m²", step: 5 },
      annual_consumption_kwh: { label: "Annual electricity use", unit: "kWh/yr", step: 100 },
    },
  },
  {
    title: "Electricity & tariff",
    fields: {
      electricity_price_eur_kwh: { label: "Electricity price", unit: "€/kWh", step: 0.01 },
      energy_price_increase: { label: "Price increase", unit: "% per yr", step: 0.5, scale: 100 },
      has_flexible_tariff: { label: "Flexible tariff" },
    },
  },
  {
    title: "Electric vehicle",
    fields: {
      has_ev: { label: "Electric car" },
      ev_km_per_year: { label: "Car distance", unit: "km/yr", step: 500 },
    },
  },
  {
    title: "Existing system",
    existing: true,
    fields: {
      existing_pv_kwp: { label: "Solar already on the roof", unit: "kWp", step: 0.5 },
      existing_battery_kwh: { label: "Battery already installed", unit: "kWh", step: 0.5 },
      has_existing_wallbox: { label: "Wallbox already installed" },
      heating_type: { label: "Current heating" },
      heating_demand_kwh: { label: "Heating demand", unit: "kWh/yr", step: 500 },
    },
  },
];
export const FIELD_COPY: Record<string, FieldCopy> = Object.assign({}, ...FIELD_GROUPS.map((g) => g.fields));

export const CHOICE_LABEL: Record<string, string> = {
  gas: "Gas", oil: "Oil", heat_pump: "Heat pump", electric: "Electric", district: "District heating", other: "Other",
  H0: "Standard household (H0)", FamilyOfFour: "Family of four", SeniorOnePerson: "One senior",
  PartTimeOnePerson: "One person, part-time", HomeOfficeOnePerson: "One person, home office", CustomFromEditor: "Custom",
};

// What the API never supplies per component; said once on each card instead of guessed.
export const NOT_SUPPLIED: Record<Target, string> = {
  pv_kwp: "Module, brand and inverter power",
  battery_kwh: "Product and brand",
  heat_pump_kw: "Product and brand",
  wallbox_kw: "Product and brand",
};

/** Name of a whole alternative setup, from the one part it changes. */
export function altLabel(t: Target, v: number) {
  const name = LABEL[t] === "PV" ? "solar" : LABEL[t].toLowerCase();
  return v === 0 ? `Without ${name}` : `With a ${num(v)} ${UNIT[t]} ${name}`;
}

export const DEMO_INPUTS: Inputs = {
  annual_consumption_kwh: 4500, household_size: 4, load_profile: "FamilyOfFour", electricity_price_eur_kwh: 0.35,
  energy_price_increase: 0.03, has_flexible_tariff: false, has_ev: true, ev_km_per_year: 12000,
  has_existing_wallbox: false, heating_type: "gas", heating_demand_kwh: null, heated_area_m2: 140,
  existing_pv_kwp: 0, existing_battery_kwh: 0,
};

// -- numbers -------------------------------------------------------------------------------------
const nf = (max: number) => new Intl.NumberFormat("en-GB", { maximumFractionDigits: max });
export const num = (n: number, max = 1) => nf(max).format(n);
export const eur = (n: number) => `€${nf(0).format(Math.round(n / 10) * 10)}`;
export const pct = (n: number) => `${Math.round(n * 100)} %`;
export const years = (n: number | null) => (n === null ? "n/a" : `${num(n, 1)} years`);
export const size = (v: number, unit: string) => (v > 0 ? `${num(v)} ${unit}` : "None");
/** ours: `wp` = the engine's module watts (Reonic's catalogue is not always 450 Wp); falls back to 450 Wp. */
export const panels = (kwp: number, wp?: number) => Math.round((kwp * 1000) / (wp && wp >= 300 && wp <= 700 ? wp : PANEL_KWP * 1000));

export function describe(values: Values, modules?: number | null) { // ours: modules = the engine's count
  const parts = [
    values.pv_kwp > 0 ? `${modules || panels(values.pv_kwp)} solar panels` : "no solar panels",
    values.battery_kwh > 0 ? `a ${num(values.battery_kwh)} kWh battery` : "no battery",
    values.heat_pump_kw > 0 ? `a ${num(values.heat_pump_kw)} kW heat pump` : "no heat pump",
    values.wallbox_kw > 0 ? `a ${num(values.wallbox_kw)} kW wallbox` : "no wallbox",
  ];
  return `3D house with ${parts.join(", ")}.`;
}

// -- offer link (planner -> homeowner) ---------------------------------------------------------------
// The homeowner picks one of these whole setups; parts are never combined on their own.
export type OfferOption = { label: string; values: Values };
export type Offer = {
  v: 2;
  customer: string;
  planner: string;
  inputs: Inputs;
  options: OfferOption[]; // options[0] is the installer's recommendation
  moduleWp?: number; // ours: the engine's module watts, so the homeowner sees the same panel count as the planner
  economics?: { savings_eur: number | null; payback_years: number | null; solar_share_of_demand?: number | null }; // ours: homeowner-facing ROI, no prices
  modelUrl?: string; // generated LoD2 GLB for the customer's pinned address (see HouseScene's House)
};

const toB64 = (s: string) => btoa(String.fromCharCode(...new TextEncoder().encode(s)));
const fromB64 = (s: string) => new TextDecoder().decode(Uint8Array.from(atob(s), (c) => c.charCodeAt(0)));

export const encodeOffer = (o: Offer) =>
  toB64(JSON.stringify(o)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

const isSize = (x: unknown): x is number => typeof x === "number" && Number.isFinite(x) && x >= 0 && x <= 1000;
const isInput = (x: unknown): x is InputValue =>
  x === null || typeof x === "boolean" || typeof x === "string" || (typeof x === "number" && Number.isFinite(x));
const isText = (x: unknown): x is string => typeof x === "string" && x.length <= 120;
// The hash is user-controlled: only our own LoD2 model route, never an arbitrary URL.
const isUrl = (x: unknown): x is string => typeof x === "string" && /^\/api\/lod2-house\/[0-9a-f-]{36}\/model$/.test(x);

/** The link is user-controlled: anything malformed yields null. */
export function decodeOffer(code: string): Offer | null {
  try {
    const o = JSON.parse(fromB64(code.replace(/-/g, "+").replace(/_/g, "/")));
    if (o?.v !== 2 || !isText(o.customer) || !isText(o.planner)) return null;
    if (typeof o.inputs !== "object" || o.inputs === null || !Object.values(o.inputs).every(isInput)) return null;
    if (!Array.isArray(o.options) || o.options.length < 1 || o.options.length > 6) return null;
    for (const opt of o.options) {
      if (!isText(opt?.label) || !TARGETS.every((t) => isSize(opt.values?.[t]))) return null;
    }
    if (o.moduleWp !== undefined && !(typeof o.moduleWp === "number" && o.moduleWp >= 300 && o.moduleWp <= 700)) delete o.moduleWp; // ours
    const isNum = (x: unknown): x is number => typeof x === "number" && Number.isFinite(x);
    if (o.economics !== undefined) {
      const e = o.economics;
      if (typeof e !== "object" || e === null) return null;
      if (!(e.savings_eur === null || isNum(e.savings_eur))) return null;
      if (!(e.payback_years === null || isNum(e.payback_years))) return null;
      if (e.solar_share_of_demand !== undefined && e.solar_share_of_demand !== null && (!isNum(e.solar_share_of_demand) || e.solar_share_of_demand < 0 || e.solar_share_of_demand > 1)) return null;
    }
    if (o.modelUrl !== undefined && !isUrl(o.modelUrl)) return null;
    return o as Offer;
  } catch {
    return null;
  }
}

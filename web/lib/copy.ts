// Wording, formatting and the planner -> homeowner offer link.
import { TARGETS, type Inputs, type InputValue, type Target, type Values } from "./api";

export const PANEL_KWP = 0.45; // Reonic's modules are 450 Wp (src/reonic/data.py MODULE_WP)
// Same as src/reonic/schema.py LABEL / UNIT
export const LABEL: Record<Target, string> = { pv_kwp: "PV", battery_kwh: "Battery", heat_pump_kw: "Heat pump", wallbox_kw: "Wallbox" };
export const UNIT: Record<Target, string> = { pv_kwp: "kWp", battery_kwh: "kWh", heat_pump_kw: "kW", wallbox_kw: "kW" };

export const GROUPS = ["Household", "Tariff", "Mobility", "Heating", "Existing system"] as const;
type FieldCopy = { label: string; group: (typeof GROUPS)[number]; unit?: string; step?: number; scale?: number };

export const FIELD_COPY: Record<string, FieldCopy> = {
  annual_consumption_kwh: { label: "Annual electricity use", unit: "kWh/yr", group: "Household", step: 100 },
  household_size: { label: "People in household", group: "Household", step: 1 },
  load_profile: { label: "Load profile", group: "Household" },
  electricity_price_eur_kwh: { label: "Electricity price", unit: "€/kWh", group: "Tariff", step: 0.01 },
  energy_price_increase: { label: "Price increase", unit: "%/yr", group: "Tariff", step: 0.5, scale: 100 },
  has_flexible_tariff: { label: "Dynamic tariff", group: "Tariff" },
  has_ev: { label: "Electric car", group: "Mobility" },
  ev_km_per_year: { label: "Car distance", unit: "km/yr", group: "Mobility", step: 500 },
  has_existing_wallbox: { label: "Wallbox already installed", group: "Mobility" },
  heating_type: { label: "Current heating", group: "Heating" },
  heating_demand_kwh: { label: "Heating demand", unit: "kWh/yr", group: "Heating", step: 500 },
  heated_area_m2: { label: "Heated area", unit: "m²", group: "Heating", step: 5 },
  existing_pv_kwp: { label: "Existing PV", unit: "kWp", group: "Existing system", step: 0.1 },
  existing_battery_kwh: { label: "Existing battery", unit: "kWh", group: "Existing system", step: 0.1 },
};

export const CHOICE_LABEL: Record<string, string> = {
  gas: "Gas", oil: "Oil", heat_pump: "Heat pump", electric: "Electric", district: "District heating", other: "Other",
  H0: "Standard household (H0)", FamilyOfFour: "Family of four", SeniorOnePerson: "Senior, living alone",
  PartTimeOnePerson: "Part-time, living alone", HomeOfficeOnePerson: "Home office, living alone",
  CustomFromEditor: "Custom profile",
};

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
export const signedEur = (n: number) => `${n >= 0 ? "+" : "−"}${eur(Math.abs(n))}`;
export const pct = (n: number) => `${Math.round(n * 100)} %`;
export const years = (n: number | null) => (n === null ? "n/a" : `${num(n, 1)} years`);
export const size = (v: number, unit: string) => (v > 0 ? `${num(v)} ${unit}` : "None");
export const panels = (kwp: number) => Math.round(kwp / PANEL_KWP);

export function describe(values: Values) {
  const parts = [
    values.pv_kwp > 0 ? `${panels(values.pv_kwp)} solar panels` : "no solar panels",
    values.battery_kwh > 0 ? `a ${num(values.battery_kwh)} kWh battery` : "no battery",
    values.heat_pump_kw > 0 ? `a ${num(values.heat_pump_kw)} kW heat pump` : "no heat pump",
    values.wallbox_kw > 0 ? `a ${num(values.wallbox_kw)} kW wallbox` : "no wallbox",
  ];
  return `3D house with ${parts.join(", ")}.`;
}

// -- confidence (spec: docs/specs/alternatives-confidence.md) ----------------------------------------
// Each group counts as unknown when every field in it is unknown.
const KEY_INPUTS: Record<Target, string[][]> = {
  pv_kwp: [["annual_consumption_kwh"]],
  battery_kwh: [["annual_consumption_kwh"]],
  heat_pump_kw: [["heating_type"], ["heating_demand_kwh", "heated_area_m2"]],
  wallbox_kw: [["has_ev"]],
};

export type Tone = "good" | "ok" | "warn";
export function confidence(t: Target, p: number, included: boolean, inputs: Inputs) {
  const unknown = KEY_INPUTS[t].filter((g) => g.every((f) => inputs[f] == null)).map((g) => FIELD_COPY[g[0]].label);
  const sure = included ? p : 1 - p;
  const level = Math.max(0, (sure >= 0.9 ? 2 : sure >= 0.7 ? 1 : 0) - (unknown.length ? 1 : 0));
  const [word, tone] = ([["Close call", "warn"], ["Likely", "ok"], ["Very likely", "good"]] as const)[level];
  return { word, tone: tone as Tone, sure, unknown };
}

export const RULE_TARGET: Record<string, Target> = { R01: "heat_pump_kw", R02: "battery_kwh", R03: "pv_kwp", R04: "battery_kwh" };

// -- offer link (planner -> homeowner) ---------------------------------------------------------------
export type Offer = { v: 1; inputs: Inputs; recommended: Values; options: Record<Target, number[]> };

const uniqSorted = (xs: number[]) => [...new Set(xs.map((x) => Math.round(x * 100) / 100))].sort((a, b) => a - b);

/** Sizes a homeowner may pick: the recommendation, its catalog neighbours and (except PV) "none". */
export function defaultOptions(t: Target, rec: number, catalog: number[]): number[] {
  const cat = uniqSorted(catalog.filter((c) => c > 0));
  const below = cat.filter((c) => c < rec).at(-1);
  const above = cat.find((c) => c > rec) ?? (rec === 0 ? cat[Math.floor(cat.length / 2)] : undefined);
  const near = t === "heat_pump_kw" ? [] : [below, above].filter((x): x is number => x !== undefined);
  return uniqSorted([...(t === "pv_kwp" && rec > 0 ? [] : [0]), rec, ...near]);
}

const toB64 = (s: string) => btoa(String.fromCharCode(...new TextEncoder().encode(s)));
const fromB64 = (s: string) => new TextDecoder().decode(Uint8Array.from(atob(s), (c) => c.charCodeAt(0)));

export const encodeOffer = (o: Offer) =>
  toB64(JSON.stringify(o)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

const isSize = (x: unknown): x is number => typeof x === "number" && Number.isFinite(x) && x >= 0 && x <= 1000;
const isInput = (x: unknown): x is InputValue =>
  x === null || typeof x === "boolean" || typeof x === "string" || (typeof x === "number" && Number.isFinite(x));

/** The link is user-controlled: anything malformed yields null. The API validates inputs again. */
export function decodeOffer(code: string): Offer | null {
  try {
    const o = JSON.parse(fromB64(code.replace(/-/g, "+").replace(/_/g, "/")));
    if (o?.v !== 1 || typeof o.inputs !== "object" || o.inputs === null) return null;
    if (!Object.values(o.inputs).every(isInput)) return null;
    for (const t of TARGETS) {
      const opts = o.options?.[t];
      if (!isSize(o.recommended?.[t]) || !Array.isArray(opts) || !opts.length || !opts.every(isSize)) return null;
      if (!opts.includes(o.recommended[t])) return null;
    }
    return o as Offer;
  } catch {
    return null;
  }
}

// ours: ADAPTER. Faris's lib/api.ts types and `api` signatures, implemented on our engine (lib/engine.ts, /engine/*).
// His UI keeps flat, snake_case inputs keyed by `meta.fields` names; this file maps them to and from our nested
// HomeInputs. When the engine is down, lib/engine.ts answers from typed fixtures and `meta().synthetic` is true,
// which his planner already labels ("Running on synthetic data").
// On a re-copy of his web/: keep this file, keep his exported names below in step with his lib/api.ts.
import { api as engine } from "./engine";
import type { Design as EngineDesign, HomeInputs, Sizes, Target as EngineTarget } from "./types";

// -- his types (exactly as in his lib/api.ts) -------------------------------------------------------------------
export const TARGETS = ["pv_kwp", "battery_kwh", "heat_pump_kw", "wallbox_kw"] as const;
export type Target = (typeof TARGETS)[number];
export type Values = Record<Target, number>;

export type InputValue = number | boolean | string | null;
export type Inputs = Record<string, InputValue>;

export type Field = { name: string; kind: "number" | "bool" | "choice"; choices: string[] };
export type Meta = {
  fields: Field[];
  targets: { name: Target; label: string; unit: string; catalog: number[] }[];
  synthetic: boolean;
};

export type Economics = { cost_eur: number; savings_eur: number | null; payback_years: number | null; solar_share_of_demand?: number | null };
export type Alternative = { value: number; values: Values; flags: string[]; validated: boolean };
export type Design = {
  values: Values;
  probability: Values;
  explanation: string[];
  flags: string[];
  economics: Economics;
  alternatives: Partial<Record<Target, Alternative>>;
  // -- ours: additive, optional -------------------------------------------------------------------------------
  /** Expert range for each part (p10..p90 of what installers picked for similar homes). */
  ranges?: Partial<Record<Target, { p10: number; p50: number; p90: number }>>;
  /** Every engine flag with its severity; `flags` above holds only warn/error messages. */
  notes?: Note[];
  /** The few unknown inputs that would change the design most; `field` is a flat input name. */
  askNext?: Ask[];
  /** The engine's PV module count (its modules are not always 450 Wp, so kWp / 0.45 can be off by one). */
  modules?: number | null;
  /** The full parts list for `values` (modules, inverter, battery, wallbox, heat pump, service lines). */
  parts?: Part[];
  source?: "live" | "demo";
};
export type Validation = { economics: Economics };
export type HouseModel = { id: string; url: string; panels: number | null; source: string };

type Whole = { whole_design_within_tolerance: number } & Record<Target, { within_tolerance: number }>;
export type Evaluation = {
  n_test: number;
  model: Whole;
  baseline: Whole; // ours: B0, the installer's usual design
  reference?: Whole; // ours: B1, a generic rule of thumb
};

export type HoldoutRow = {
  project_id: string;
  inputs: Inputs;
  expert: Record<Target, number | null>;
  ours: Values;
};

// -- ours: extension types ----------------------------------------------------------------------------------------
export type Part = { type: string | null; name: string; brand: string | null; quantity: number; units: string | null };
export type Severity = "info" | "warn" | "error";
export type Note = { target: Target | null; severity: Severity; message: string };
export type Ask = {
  field: string;
  question: string;
  why: string;
  parts: Target[];
  priceSwingEur: number;
  answers: { label: string; value: number | boolean }[];
};

// -- names --------------------------------------------------------------------------------------------------------
const CAMEL: Record<Target, EngineTarget> = { pv_kwp: "pvKwp", battery_kwh: "batteryKwh", heat_pump_kw: "heatPumpKw", wallbox_kw: "wallboxKw" };
const SNAKE = Object.fromEntries(TARGETS.map((t) => [CAMEL[t], t])) as Record<EngineTarget, Target>;
const COMPONENT: Record<string, Target> = { pv: "pv_kwp", battery: "battery_kwh", heatPump: "heat_pump_kw", wallbox: "wallbox_kw" };

const toValues = (s: Partial<Sizes>): Values => ({
  pv_kwp: s.pvKwp ?? 0, battery_kwh: s.batteryKwh ?? 0, heat_pump_kw: s.heatPumpKw ?? 0, wallbox_kw: s.wallboxKw ?? 0,
});
const toSizes = (v: Partial<Values>): Partial<Sizes> =>
  Object.fromEntries(Object.entries(v).map(([k, x]) => [CAMEL[k as Target], x]));

// Flat input name -> the engine's dotted path (the key provenance and Ask-next use).
const PATH: Record<string, string> = {
  annual_consumption_kwh: "demandKwh",
  household_size: "persons",
  heated_area_m2: "building.sqm",
  load_profile: "loadProfile",
  electricity_price_eur_kwh: "priceEurKwh",
  energy_price_increase: "priceEscalation",
  has_flexible_tariff: "flexTariff",
  home_office: "homeOffice",
  has_ev: "ev.has",
  ev_km_per_year: "ev.kmPerYear",
  existing_pv_kwp: "existingPv.kwp",
  existing_battery_kwh: "existingStorage.kwh",
  has_existing_wallbox: "existingWallbox.kw",
  heating_type: "heating.type",
  heating_demand_kwh: "heating.heatDemandKwh",
  roof_max_modules: "building.roofMaxModules",
};
const FLAT_OF = Object.fromEntries(Object.entries(PATH).map(([k, p]) => [p, k]));

type HeatingType = NonNullable<HomeInputs["heating"]>["type"];
// [his choice, our enum]; the first pair per engine value wins on the way back.
const HEATING: [string, HeatingType][] = [
  ["gas", "Gas"], ["oil", "Oil"], ["heat_pump", "Heatpump"], ["other_renewable", "OtherRenewable"], ["other", "OtherNonRenewable"],
  ["district", "OtherNonRenewable"], ["electric", "OtherNonRenewable"],
];
const PROFILE: [string, string][] = [
  ["H0", "H0"], ["FamilyOfFour", "FamilyOfFour"], ["SeniorOnePerson", "Senior"], ["HomeOfficeOnePerson", "HomeOffice"], ["CustomFromEditor", "Custom"],
];
const there = <T,>(pairs: [string, T][], v: unknown) => pairs.find((p) => p[0] === v)?.[1];
const back = <T,>(pairs: [string, T][], v: unknown) => pairs.find((p) => p[1] === v)?.[0] ?? null;

const BOOL = new Set(["has_flexible_tariff", "home_office", "has_ev", "has_existing_wallbox"]);
const FIELDS: Field[] = Object.keys(PATH).map((name) =>
  name === "heating_type"
    ? { name, kind: "choice", choices: HEATING.slice(0, 5).map((p) => p[0]) }
    : name === "load_profile"
      ? { name, kind: "choice", choices: PROFILE.map((p) => p[0]) }
      : { name, kind: BOOL.has(name) ? "bool" : "number", choices: [] },
);

const DEFAULT_DEMAND_KWH = 4500; // the engine's default; Ask-next asks for the real one while it is this

/** Flat inputs -> our HomeInputs. Every known (non-empty) field is reported to the engine as "entered". */
function toWire(i: Inputs, installer: string): HomeInputs {
  const n = (k: string) => (typeof i[k] === "number" && Number.isFinite(i[k]) ? (i[k] as number) : null);
  const b = (k: string) => (typeof i[k] === "boolean" ? (i[k] as boolean) : null);
  const s = (k: string) => (typeof i[k] === "string" && i[k] !== "" ? (i[k] as string) : null);
  const sqm = n("heated_area_m2");
  const roof = n("roof_max_modules");
  const pv = n("existing_pv_kwp");
  const bat = n("existing_battery_kwh");
  const known = Object.keys(PATH).filter((k) => i[k] !== null && i[k] !== undefined && i[k] !== "");
  return {
    installerId: s("installer_id") ?? installer,
    demandKwh: n("annual_consumption_kwh") ?? DEFAULT_DEMAND_KWH,
    loadProfile: there(PROFILE, s("load_profile")) ?? "H0",
    persons: n("household_size"),
    homeOffice: b("home_office"),
    priceEurKwh: n("electricity_price_eur_kwh") ?? 0.32,
    priceEscalation: n("energy_price_increase") ?? 0.03,
    flexTariff: b("has_flexible_tariff"),
    ev: { has: b("has_ev") === true, kmPerYear: b("has_ev") === false ? null : n("ev_km_per_year") },
    existingPv: pv ? { kwp: pv, trusted: true } : null,
    existingStorage: bat ? { kwh: bat, trusted: true } : null,
    existingWallbox: b("has_existing_wallbox") ? { kw: 11 } : null,
    heating: { type: there(HEATING, s("heating_type")) ?? "Unknown", heatDemandKwh: n("heating_demand_kwh") },
    building: sqm !== null || roof !== null ? { sqm, roofMaxModules: roof } : null,
    provenance: Object.fromEntries(known.map((k) => [PATH[k], { source: "entered" as const, confidence: 1 }])),
  };
}

/** Our HomeInputs (held-out projects) -> flat inputs. */
function toFlat(h: HomeInputs): Inputs {
  return {
    installer_id: h.installerId,
    annual_consumption_kwh: h.demandKwh ?? null,
    household_size: h.persons ?? null,
    load_profile: back(PROFILE, h.loadProfile),
    home_office: h.homeOffice ?? null,
    electricity_price_eur_kwh: h.priceEurKwh ?? null,
    energy_price_increase: h.priceEscalation ?? null,
    has_flexible_tariff: h.flexTariff ?? null,
    has_ev: h.ev?.has ?? null,
    ev_km_per_year: h.ev?.kmPerYear ?? null,
    existing_pv_kwp: h.existingPv?.kwp ?? 0,
    existing_battery_kwh: h.existingStorage?.kwh ?? 0,
    has_existing_wallbox: !!h.existingWallbox,
    heating_type: back(HEATING, h.heating?.type),
    heating_demand_kwh: h.heating?.heatDemandKwh ?? null,
    heated_area_m2: h.building?.sqm ?? null,
    roof_max_modules: h.building?.roofMaxModules ?? null,
  };
}

// -- meta, cached for the installer default and the catalogs ----------------------------------------------------
let metaOnce: ReturnType<typeof engine.meta> | null = null;
const engineMeta = () => (metaOnce ??= engine.meta().catch((e) => ((metaOnce = null), Promise.reject(e))));

const economics = (m: EngineDesign["metrics"]): Economics => ({
  cost_eur: m?.priceEur ?? 0,
  savings_eur: m?.savingsEurYear ?? null,
  payback_years: m?.paybackYears ?? null,
});

/** The size a part gets when the planner offers it although the design leaves it out. */
function includeSize(t: Target, d: EngineDesign, catalog: number[]): number | null {
  const c = d.confidence[CAMEL[t]];
  if (c && c.p50 > 0) return Math.round(c.p50 * 10) / 10;
  const alt = d.alternatives.find((a) => a.sizes[CAMEL[t]] > 0);
  if (alt) return alt.sizes[CAMEL[t]];
  return catalog.length ? catalog[Math.floor(catalog.length / 2)] : null;
}

/** Display only: internal rule ids ("R06: ...") mean nothing to the reader. */
const plain = (s: string) => s.replace(/^R\d\d:?\s*/, "");

async function toDesign(d: EngineDesign, h: HomeInputs, locked: Partial<Values>, source: "live" | "demo"): Promise<Design> {
  const values = toValues(d.sizes);
  const { data: meta } = await engineMeta();
  const catalog = (t: Target) => meta.targets.find((x) => x.name === CAMEL[t])?.catalog ?? [];
  // His offer: one flip per part the planner hasn't set, checked by the engine's rules for its own warnings.
  const flips = TARGETS.flatMap((t) => {
    if (locked[t] !== undefined) return [];
    const v = values[t] > 0 ? 0 : includeSize(t, d, catalog(t));
    return v === null || v === values[t] ? [] : [[t, v] as const];
  });
  const alternatives = Object.fromEntries(
    await Promise.all(
      flips.map(async ([t, v]) => {
        const alt = { ...values, [t]: v };
        let validated = false;
        const flags = await engine
          .validate(h, toSizes(alt) as Sizes)
          .then((r) => {
            validated = r.source === "live" || source === "demo";
            return validated ? r.data.filter((f) => f.severity !== "info").map((f) => plain(f.message)) : ["Not validated: the engine is unavailable."];
          })
          .catch(() => ["Not validated: the check failed. Retry before sharing this option."]);
        return [t, { value: v, values: alt, flags, validated }] as const;
      }),
    ),
  ) as Design["alternatives"];
  const ranges: Design["ranges"] = {};
  for (const t of TARGETS) {
    const c = d.confidence[CAMEL[t]];
    // A locked part's interval is just the planner's own value ("Experts pick 20 kWh"): show no range for it.
    if (c && locked[t] === undefined) ranges[t] = { p10: c.p10, p50: c.p50, p90: c.p90 };
  }
  return {
    values,
    probability: Object.fromEntries(TARGETS.map((t) => [t, d.confidence[CAMEL[t]]?.probIncluded ?? (values[t] > 0 ? 1 : 0)])) as Values,
    explanation: d.reasons.map((r) => plain(r.text)),
    flags: d.flags.filter((f) => f.severity !== "info").map((f) => plain(f.message)),
    economics: economics(d.metrics),
    alternatives,
    ranges,
    notes: d.flags.map((f) => ({ target: f.component ? (COMPONENT[f.component] ?? null) : null, severity: f.severity, message: plain(f.message) })),
    askNext: d.askNext.map((a) => ({
      field: FLAT_OF[a.field] ?? a.field,
      question: a.question,
      why: a.why,
      parts: a.impact.components.map((c) => SNAKE[c]),
      priceSwingEur: a.impact.priceSwingEur,
      answers: a.answers,
    })),
    modules: d.modules,
    parts: d.bom?.map((b) => ({
      type: b.componentType ?? null,
      name: b.componentName,
      brand: b.componentBrand ?? null,
      quantity: b.quantity ?? 1,
      units: b.quantityUnits ?? null,
    })),
    source,
  };
}

const whole = (m: { wholeDesign: number; pv: number; battery: number; heatPump: number; wallbox: number }): Whole => ({
  whole_design_within_tolerance: m.wholeDesign,
  pv_kwp: { within_tolerance: m.pv },
  battery_kwh: { within_tolerance: m.battery },
  heat_pump_kw: { within_tolerance: m.heatPump },
  wallbox_kw: { within_tolerance: m.wallbox },
});

const installer = async () => (await engineMeta()).data.installers[0] ?? "default";

export const api = {
  meta: async (): Promise<Meta> => {
    const { data, source } = await engineMeta();
    return {
      fields: FIELDS,
      targets: data.targets.map((t) => ({ name: SNAKE[t.name], label: t.label, unit: t.unit, catalog: t.catalog })),
      synthetic: data.synthetic || source === "demo",
    };
  },
  design: async (inputs: Inputs, locked: Partial<Values> = {}): Promise<Design> => {
    const h = toWire(inputs, await installer());
    const r = await engine.design(h, toSizes(locked));
    return toDesign(r.data, h, locked, r.source);
  },
  validate: async (inputs: Inputs, values: Values): Promise<Validation> => {
    const h = toWire(inputs, await installer());
    const r = await engine.simulate(h, toSizes(values) as Sizes);
    return { economics: economics(r.data) };
  },
  evaluation: async (): Promise<Evaluation> => {
    const { data } = await engine.evalSummary();
    const model = data.models[data.chosen];
    const baseline = data.models.B0 ?? Object.values(data.models)[0];
    if (!model || !baseline) return {} as Evaluation; // his Reality shows "No evaluation yet"
    const reference = data.models.B1;
    return { n_test: data.nTest, model: whole(model), baseline: whole(baseline), ...(reference && { reference: whole(reference) }) };
  },
  holdout: async (): Promise<{ rows: HoldoutRow[] }> => {
    const { data } = await engine.holdout(12);
    return {
      rows: data.map((r) => ({
        project_id: r.projectId,
        inputs: toFlat(r.inputs),
        expert: Object.fromEntries(TARGETS.map((t) => [t, r.expert[CAMEL[t]]])) as Record<Target, number | null>,
        ours: toValues(r.ours),
      })),
    };
  },
};

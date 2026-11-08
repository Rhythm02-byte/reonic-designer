// UI-side types. Engine wire types come from packages/contracts (generated); everything the UI touches is
// camelCase and keyed by Target, and lib/api.ts is the only place that knows the wire field names.
import type { components } from "../../../packages/contracts/src/api";

export type Schemas = components["schemas"];
export type HomeInputs = Schemas["HomeInputs"];
export type Flag = Schemas["Flag"];
export type Provenance = Schemas["Provenance"];

export const TARGETS = ["pvKwp", "batteryKwh", "heatPumpKw", "wallboxKw"] as const;
export type Target = (typeof TARGETS)[number];
/** kWp, kWh, kW, kW. 0 means "none". */
export type Sizes = Record<Target, number>;

export type Interval = { p10: number; p50: number; p90: number; probIncluded: number | null };

export type Metrics = {
  pvYieldKwh: number | null;
  selfConsumption: number | null;
  autarky: number | null; // 0..1
  savingsEurYear: number | null;
  paybackYears: number | null;
  npv20: number | null;
  priceEur: number | null;
  /** Hourly means (24 values) of a typical summer / winter day; proposal and /simulate only. */
  typicalDays?: { summer: TypicalDay; winter: TypicalDay } | null;
};
export type TypicalDay = { pvKwh: number[]; loadKwh: number[]; batteryKwh: number[]; gridKwh: number[]; socKwh: number[] };

export type CurvePoint = { kwh: number; autarky: number | null; savingsEurYear: number | null; paybackYears: number | null; npv20: number | null };
export type Physics = { economicKwh: number | null; maxAutarkyKwh: number | null; nightLoadKwh: number | null };

/** One missing input worth asking for. `field` is the engine's dotted path; `value` is what answering writes into it. */
export type AskNext = {
  field: string;
  question: string;
  why: string;
  impact: { components: Target[]; priceSwingEur: number };
  answers: { label: string; value: number | boolean }[];
};

export type Reason = { code: string; target: Target; text: string };

export type Design = {
  sizes: Sizes;
  modules: number | null;
  alternatives: { label: string; sizes: Sizes; metrics: Metrics | null }[];
  metrics: Metrics | null;
  confidence: Partial<Record<Target, Interval>>;
  reasons: Reason[];
  flags: Flag[];
  /** At most 3 questions, best first; empty when nothing is worth asking. */
  askNext: AskNext[];
  curves: { battery: CurvePoint[] } | null;
  physics: Physics | null;
  /** Provenance the engine reports for inputs, keyed by dotted wire path ("ev.has", "heating.type"). */
  provenance: Record<string, Provenance>;
  engineVersion: string;
  latencyMs: number;
  /** Parts list (Reonic's project_options_parts shape); absent in the offline fixtures. */
  bom?: BomLine[];
};
export type BomLine = Schemas["BomLine"];

export type Field = { name: string; kind: "number" | "bool" | "choice"; choices: string[]; label: string; unit?: string };
export type Meta = {
  fields: Field[];
  targets: { name: Target; label: string; unit: string; catalog: number[] }[];
  installers: string[];
  synthetic: boolean;
  engineVersion: string;
};

export type ModelScore = { ems: number | null; wholeDesign: number; pv: number; battery: number; heatPump: number; wallbox: number };
export type EvalSummary = {
  split: string;
  nTest: number;
  chosen: string;
  models: Record<string, ModelScore>;
  selection: string | null;
  /** Relative size error that still counts as matching the expert, per component. */
  tolerances: { pv: number; battery: number; heatPump: number };
  generatedAt: string;
};

export type HoldoutRow = {
  projectId: string;
  installerId: string;
  inputs: HomeInputs;
  expert: Record<Target, number | null>; // null = offered, size unknown
  ours: Sizes;
};

/** Where an answer came from: the live engine, or the typed fixtures used while it is unreachable. */
export type Source = "live" | "demo";
export type Sourced<T> = { data: T; source: Source };

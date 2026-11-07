// Types and calls for the Python designer API (src/reonic/api.py), proxied by next.config.ts.

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

export type Economics = {
  cost_eur: number;
  pv_yield_kwh: number;
  demand_kwh: number | null;
  self_use_share: number | null;
  solar_share_of_demand: number | null;
  savings_eur: number | null;
  payback_years: number | null;
};

export type Alternative = { value: number; values: Values; flags: string[]; economics: Economics };

export type Design = {
  values: Values;
  probability: Values;
  explanation: string[];
  rules_applied: string[];
  flags: string[];
  economics: Economics;
  alternatives: Partial<Record<Target, Alternative>>;
};

export type Validation = { flags: string[]; economics: Economics };

type Metrics = { include_accuracy: number; within_tolerance: number; size_mae: number | null; expert_include_rate: number };
export type Evaluation = {
  n_train: number;
  n_test: number;
  split: string;
  model: Record<Target, Metrics> & { whole_design_within_tolerance: number };
  baseline: Record<Target, Metrics> & { whole_design_within_tolerance: number };
  by_installer: Record<string, number>;
};

export type HoldoutRow = {
  project_id: string;
  installer_id: string;
  inputs: Inputs;
  expert: Record<Target, number | null>; // null = PV offered, size unknown in the export
  ours: Values;
  baseline: Values;
};

async function call<T>(path: string, body?: unknown): Promise<T> {
  const init: RequestInit | undefined =
    body === undefined
      ? undefined
      : { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) };
  let res: Response;
  try {
    res = await fetch(`/api/${path}`, init);
  } catch {
    throw new Error("Can't reach the designer API. Start it with: uvicorn reonic.api:app --port 8000");
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(
      data?.error ?? `The designer API isn't answering (${res.status}). Is uvicorn running on port 8000?`,
    );
  }
  return data as T;
}

export const api = {
  meta: () => call<Meta>("meta"),
  design: (inputs: Inputs, locked: Partial<Values> = {}) => call<Design>("design", { inputs, locked }),
  validate: (inputs: Inputs, values: Values) => call<Validation>("validate", { inputs, values }),
  evaluation: () => call<Evaluation>("eval"),
  holdout: () => call<{ rows: HoldoutRow[] }>("holdout"),
};

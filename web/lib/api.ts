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

export type Economics = { cost_eur: number; savings_eur: number | null; payback_years: number | null };
export type Alternative = { value: number; values: Values; flags: string[] };
export type Design = {
  values: Values;
  probability: Values; // the model's chance of including each part; only used to ask for a second look
  explanation: string[];
  flags: string[];
  economics: Economics;
  alternatives: Partial<Record<Target, Alternative>>; // one flip per part the planner hasn't set
};
export type Validation = { economics: Economics };

// reports/eval.json; {} until `python -m reonic eval` has run.
type Whole = { whole_design_within_tolerance: number } & Record<Target, { within_tolerance: number }>;
// baseline = rule of thumb (easy to beat); typical = ignores the home, proposes what most homes got (the fair reference).
export type Evaluation = { n_test: number; model: Whole; baseline: Whole; typical?: Whole };

export type HoldoutRow = {
  project_id: string;
  inputs: Inputs;
  expert: Record<Target, number | null>; // null = PV offered, size unknown in the export
  ours: Values;
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

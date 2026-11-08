// ours: the only file that knows the engine's wire format (our nested, camelCase types in ./types). lib/api.ts adapts it
// to Faris's flat UI types.
// Calls go through the Next proxy (next.config.ts, /engine/*). If the engine is unreachable (or does not have an
// endpoint yet) the typed fixtures answer instead, and the result says so (`source: "demo"`).
import { isDemoForced } from "./pitch";
import { PITCH_EVAL, pitchDesign } from "./pitchDemo";
import { designFixture, EVAL_FIXTURE, HOLDOUT_FIXTURE, META_FIXTURE, simulateFixture } from "./fixtures";
import { PANEL_KWP } from "./format";
import { TARGETS } from "./types";
import type { components } from "../../../packages/contracts/src/api";
import type { AskNext, Design, EvalSummary, Flag, HoldoutRow, HomeInputs, Meta, Metrics, Sizes, Sourced, Target } from "./types";

type S = components["schemas"];
type Component = NonNullable<S["Flag"]["component"]>;

const COMPONENT: Record<Target, Component> = { pvKwp: "pv", batteryKwh: "battery", heatPumpKw: "heatPump", wallboxKw: "wallbox" };
const TARGET_OF = Object.fromEntries(TARGETS.map((t) => [COMPONENT[t], t])) as Record<Component, Target>;

// -- wire <-> UI ------------------------------------------------------------------------------------------------
export function toSystem(s: Sizes, id = "current"): S["SystemDesign"] {
  return {
    id,
    pv: s.pvKwp > 0 ? { modules: Math.round(s.pvKwp / PANEL_KWP), moduleWp: PANEL_KWP * 1000, kwp: s.pvKwp } : null,
    battery: s.batteryKwh > 0 ? { kwh: s.batteryKwh } : null,
    heatPump: s.heatPumpKw > 0 ? { kw: s.heatPumpKw } : null,
    wallbox: s.wallboxKw > 0 ? { kw: s.wallboxKw } : null,
  };
}

export function fromSystem(d: S["SystemDesign"] | null | undefined): Sizes {
  return { pvKwp: d?.pv?.kwp ?? 0, batteryKwh: d?.battery?.kwh ?? 0, heatPumpKw: d?.heatPump?.kw ?? 0, wallboxKw: d?.wallbox?.kw ?? 0 };
}

// {summer|winter: {pvKwh, loadKwh, batteryKwh, gridKwh, socKwh: 24 hourly means}}; only on the proposal and /simulate.
const typicalDays = (d: S["Metrics"]["hourlyTypicalDays"]): Metrics["typicalDays"] =>
  d?.summer && d.winter ? ({ summer: d.summer, winter: d.winter } as Metrics["typicalDays"]) : null;

const metrics = (m: Partial<S["Metrics"]> | null | undefined): Metrics | null =>
  m
    ? {
        pvYieldKwh: m.pvYieldKwh ?? null, selfConsumption: m.selfConsumption ?? null, autarky: m.autarky ?? null,
        savingsEurYear: m.savingsEurYear ?? null, paybackYears: m.paybackYears ?? null, npv20: m.npv20 ?? null, priceEur: m.priceEur ?? null,
        typicalDays: typicalDays(m.hourlyTypicalDays),
      }
    : null;

const toAsk = (r: S["AskNext"]): AskNext => ({
  field: r.field, question: r.question, why: r.why,
  impact: { components: (r.impact.components ?? []).map((c) => TARGET_OF[c]).filter(Boolean), priceSwingEur: r.impact.priceSwingEur },
  answers: (r.answers ?? []).flatMap((a) => (typeof a.value === "number" || typeof a.value === "boolean" ? [{ label: a.label, value: a.value }] : [])),
});

/** What answering a question writes into the inputs (wire paths live here only); the field counts as entered afterwards. */
export function applyAnswer(i: HomeInputs, field: string, value: number | boolean): HomeInputs {
  const next: HomeInputs = { ...i, provenance: { ...i.provenance, [field]: { source: "entered", confidence: 1 } } };
  const n = Number(value);
  switch (field) {
    case "demandKwh": return { ...next, demandKwh: n };
    case "building.roofMaxModules": return { ...next, building: { ...i.building, roofMaxModules: n } };
    case "ev.has": return { ...next, ev: { ...i.ev, has: value === true, kmPerYear: value === true ? (i.ev?.kmPerYear ?? null) : null } };
    case "heating.heatDemandKwh": return { ...next, heating: { ...i.heating, type: i.heating?.type ?? "Unknown", heatDemandKwh: n } };
    case "existingPv.kwp": return { ...next, existingPv: n > 0 ? { kwp: n, trusted: true } : null };
    case "existingStorage.kwh": return { ...next, existingStorage: n > 0 ? { kwh: n, trusted: true } : null };
    default: return i;
  }
}

function toDesign(r: S["DesignResponse"]): Design {
  const m = r.metrics ?? {};
  const confidence: Design["confidence"] = {};
  for (const [k, v] of Object.entries(r.confidence ?? {})) {
    const t = TARGET_OF[k as Component];
    if (t) confidence[t] = { p10: v.p10, p50: v.p50, p90: v.p90, probIncluded: v.probIncluded ?? null };
  }
  return {
    sizes: fromSystem(r.proposal),
    modules: r.proposal.pv?.modules ?? null,
    // "Without battery", "Economic battery", "Max independence"; the engine sends none while the battery is locked.
    alternatives: (r.alternatives ?? []).map((a) => ({ label: a.label ?? a.id, sizes: fromSystem(a), metrics: metrics(m[a.id]) })),
    metrics: metrics(m[r.proposal.id] ?? m.proposal ?? Object.values(m)[0]),
    confidence,
    reasons: (r.reasons ?? []).filter((x) => x.text).map((x) => ({ code: x.code, target: TARGET_OF[x.component], text: x.text! })),
    flags: (r.flags ?? []) as Flag[],
    askNext: (r.askNext ?? []).map(toAsk),
    curves: r.curves?.battery?.length
      ? {
          battery: r.curves.battery.map((p) => ({
            kwh: p.kwh ?? 0, autarky: p.autarky ?? null, savingsEurYear: p.savingsEurYear ?? null, paybackYears: p.paybackYears ?? null, npv20: p.npv20 ?? null,
          })),
        }
      : null,
    physics: r.physics
      ? { economicKwh: r.physics.economicKwh ?? null, maxAutarkyKwh: r.physics.maxAutarkyKwh ?? null, nightLoadKwh: r.physics.nightLoadKwh ?? null }
      : null,
    provenance: r.provenance ?? {},
    engineVersion: r.engineVersion,
    latencyMs: r.latencyMs,
    bom: r.bom ?? [],
  };
}

// Scores are fractions 0..1, except `ems` (expert-match score), which is 0..100.
type WireEval = S["EvalSummary"];

function toEval(r: WireEval): EvalSummary {
  const models = Object.fromEntries(
    Object.entries(r.models).map(([k, v]) => [
      k,
      { ems: v.ems ?? null, wholeDesign: v.wholeDesign ?? 0, pv: v.pv ?? 0, battery: v.battery ?? 0, heatPump: v.heatPump ?? 0, wallbox: v.wallbox ?? 0 },
    ]),
  );
  const sel = r.selection as { criterion?: unknown } | null | undefined;
  return {
    split: r.split, nTest: r.nTest, chosen: r.chosen, models,
    selection: typeof sel?.criterion === "string" ? `Chosen by ${sel.criterion}.` : null,
    tolerances: { ...EVAL_FIXTURE.tolerances, ...r.tolerances },
    generatedAt: r.generatedAt ?? "unknown",
  };
}

// -- transport --------------------------------------------------------------------------------------------------
const BASE = "/engine";
class Down extends Error {}

let downAt = 0; // after a failed attempt, skip the engine for a few seconds instead of retrying on every keystroke
async function call<T>(path: string, body?: unknown): Promise<T> {
  if (Date.now() - downAt < 4000) throw new Down();
  let res: Response;
  try {
    res = await fetch(
      `${BASE}/${path}`,
      { signal: AbortSignal.timeout(20_000), ...(body === undefined ? {} : { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) }) },
    );
  } catch {
    downAt = Date.now();
    throw new Down();
  }
  if (res.status === 404 || res.status >= 500) {
    if (res.status !== 404) downAt = Date.now();
    throw new Down(); // not there (yet): the caller falls back to the fixture
  }
  const data = await res.json().catch(() => { downAt = Date.now(); throw new Down(); });
  if (!res.ok) throw new Error(`The engine rejected this request (${res.status}). ${typeof data?.detail === "string" ? data.detail : ""}`.trim());
  downAt = 0;
  return data as T;
}

async function withFallback<T>(live: () => Promise<T>, demo: () => T): Promise<Sourced<T>> {
  if (isDemoForced()) return { data: demo(), source: "demo" }; // pitch mode (?demo=1): never call the engine
  try {
    return { data: await live(), source: "live" };
  } catch (e) {
    if (e instanceof Down) return { data: demo(), source: "demo" };
    throw e;
  }
}

const holdoutSizes = (x: S["HoldoutSystem"]): Record<Target, number | null> => ({
  pvKwp: x.pvKwp ?? null, batteryKwh: x.batteryKwh ?? null, heatPumpKw: x.heatPumpKw ?? null, wallboxKw: x.wallboxKw ?? null,
});
const toHoldoutRow = (r: S["HoldoutRow"]): HoldoutRow => {
  const ours = holdoutSizes(r.ours);
  return {
    projectId: r.projectId, installerId: r.installerId, inputs: r.inputs, expert: holdoutSizes(r.expert),
    ours: { pvKwp: ours.pvKwp ?? 0, batteryKwh: ours.batteryKwh ?? 0, heatPumpKw: ours.heatPumpKw ?? 0, wallboxKw: ours.wallboxKw ?? 0 },
  };
};

const ALL: Component[] = ["pv", "battery", "heatPump", "wallbox"];

export const api = {
  meta: () =>
    withFallback(
      async () => {
        const r = await call<Partial<Meta>>("meta");
        return { ...META_FIXTURE, ...r, installers: r.installers?.length ? r.installers : META_FIXTURE.installers };
      },
      () => META_FIXTURE,
    ),

  /** `locked` keeps those components at the given sizes; the engine designs the rest around them. */
  design: (inputs: HomeInputs, locked: Partial<Sizes> = {}, current?: Sizes) =>
    withFallback(
      async () => {
        const locks = (Object.keys(locked) as Target[]).map((t) => COMPONENT[t]);
        const sys = current || locks.length ? toSystem({ ...current, ...locked } as Sizes) : undefined;
        return toDesign(await call<S["DesignResponse"]>("design", { inputs, locks, current: sys }));
      },
      () => (isDemoForced() ? pitchDesign(inputs, locked) : designFixture(inputs, locked)),
    ),

  /** Metrics for exactly this system. */
  simulate: (inputs: HomeInputs, sizes: Sizes) =>
    withFallback(
      async () => metrics(await call<S["Metrics"]>("simulate", { inputs, system: toSystem(sizes) })),
      () => simulateFixture(inputs, sizes),
    ),

  /** Rule checks and "unusual for similar homes" flags for exactly this system. */
  validate: (inputs: HomeInputs, sizes: Sizes) =>
    withFallback(
      async () => ((await call<{ flags?: Flag[] }>("validate", { inputs, system: toSystem(sizes) })).flags ?? []) as Flag[],
      () => designFixture(inputs, sizes).flags,
    ),

  /** The offer page: everything pinned, so the engine returns the curves and flags around exactly this system. */
  designPinned: (inputs: HomeInputs, sizes: Sizes) =>
    withFallback(
      async () => toDesign(await call<S["DesignResponse"]>("design", { inputs, locks: ALL, current: toSystem(sizes) })),
      () => designFixture(inputs, sizes),
    ),

  evalSummary: () => withFallback(async () => toEval(await call<WireEval>("eval/summary")), () => (isDemoForced() ? PITCH_EVAL : EVAL_FIXTURE)),

  holdout: (n = 12) =>
    withFallback(
      async () => (await call<S["HoldoutResponse"]>(`holdout?n=${n}`)).rows.map(toHoldoutRow),
      () => HOLDOUT_FIXTURE,
    ),
};

// Typed stand-ins for the engine, used only while it is unreachable (lib/api.ts switches to live calls on its own).
// The numbers come from a toy model: they make the UI work, they are not engine output. The UI says so.
import type { CurvePoint, Design, EvalSummary, Flag, HoldoutRow, HomeInputs, Meta, Metrics, Reason, Sizes, Target } from "./types";
import { PANEL_KWP } from "./format";

const CATALOG: Record<Target, number[]> = {
  pvKwp: [0, 4.5, 6.3, 8.1, 9.45, 10.8, 13.5, 16.2],
  batteryKwh: [0, 5, 7.5, 10, 12.5, 15, 20],
  heatPumpKw: [0, 6, 8, 10.5, 12],
  wallboxKw: [0, 7.4, 11, 22],
};

export const META_FIXTURE: Meta = {
  fields: [
    { name: "demandKwh", kind: "number", choices: [], label: "Annual electricity use", unit: "kWh/yr" },
    { name: "persons", kind: "number", choices: [], label: "People in household" },
    { name: "heating.type", kind: "choice", choices: ["Gas", "Oil", "Heatpump", "OtherRenewable", "OtherNonRenewable", "Unknown"], label: "Current heating" },
    { name: "ev.has", kind: "bool", choices: [], label: "Electric car" },
    { name: "ev.kmPerYear", kind: "number", choices: [], label: "Car distance", unit: "km/yr" },
  ],
  targets: [
    { name: "pvKwp", label: "PV", unit: "kWp", catalog: CATALOG.pvKwp },
    { name: "batteryKwh", label: "Battery", unit: "kWh", catalog: CATALOG.batteryKwh },
    { name: "heatPumpKw", label: "Heat pump", unit: "kW", catalog: CATALOG.heatPumpKw },
    { name: "wallboxKw", label: "Wallbox", unit: "kW", catalog: CATALOG.wallboxKw },
  ],
  installers: ["default"],
  synthetic: true,
  engineVersion: "fixture",
};

const nearest = (xs: number[], v: number) => xs.reduce((a, b) => (Math.abs(b - v) < Math.abs(a - v) ? b : a));

function propose(i: HomeInputs): Sizes {
  const car = i.ev?.has ? (i.ev.kmPerYear ?? 10000) : 0;
  const kwp = (i.demandKwh / 1000) * 1.5 + car / 6000;
  const pvKwp = nearest(CATALOG.pvKwp, kwp);
  return {
    pvKwp,
    batteryKwh: pvKwp > 0 ? nearest(CATALOG.batteryKwh, pvKwp * 1.05) : 0,
    heatPumpKw: i.heating?.type === "Oil" ? 10.5 : 0,
    wallboxKw: i.ev?.has ? 11 : 0,
  };
}

/** Toy yearly energy balance. */
export function simulateFixture(i: HomeInputs, s: Sizes): Metrics {
  const car = i.ev?.has && s.wallboxKw > 0 ? (i.ev.kmPerYear ?? 10000) * 0.18 : 0;
  const load = i.demandKwh + car + s.heatPumpKw * 400;
  const yieldKwh = s.pvKwp * 950;
  const cover = Math.min(1, yieldKwh / load);
  const direct = 0.42 * cover;
  const stored = (1 - Math.exp(-s.batteryKwh / ((load / 1000) * 1.6))) * 0.38 * cover;
  const autarky = Math.min(0.92, direct + stored);
  const selfUse = yieldKwh > 0 ? Math.min(1, (autarky * load) / yieldKwh) : null;
  const feedIn = yieldKwh * (1 - (selfUse ?? 0));
  const savings = autarky * load * i.priceEurKwh + feedIn * 0.08;
  const price = s.pvKwp * 1350 + s.batteryKwh * 650 + s.heatPumpKw * 900 + (s.wallboxKw > 0 ? 900 : 0) + (s.pvKwp > 0 ? 1500 : 0);
  return {
    pvYieldKwh: yieldKwh,
    selfConsumption: selfUse,
    autarky,
    savingsEurYear: savings,
    paybackYears: savings > 0 ? price / savings : null,
    npv20: savings * 16 - price,
    priceEur: price,
  };
}

const interval = (v: number, included: number) => ({ p10: v * 0.75, p50: v, p90: v * 1.3, probIncluded: included });

export function designFixture(inputs: HomeInputs, locked: Partial<Sizes>): Design {
  const sizes = { ...propose(inputs), ...locked };
  const modules = Math.round(sizes.pvKwp / PANEL_KWP);
  const curve: CurvePoint[] = [0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20].map((kwh) => {
    const m = simulateFixture(inputs, { ...sizes, batteryKwh: kwh });
    return { kwh, autarky: m.autarky, savingsEurYear: m.savingsEurYear, paybackYears: m.paybackYears, npv20: m.npv20 };
  });
  const best = curve.reduce((a, b) => ((b.npv20 ?? -Infinity) > (a.npv20 ?? -Infinity) ? b : a));
  const reasons: Reason[] = [
    { code: "PV_DEMAND", target: "pvKwp", text: `PV ${sizes.pvKwp.toFixed(1)} kWp: about 1.5 kWp per 1,000 kWh of yearly use, plus the car.` },
    { code: "BATTERY_PV", target: "batteryKwh", text: `Battery ${sizes.batteryKwh} kWh: roughly one kWh per kWp of PV.` },
  ];
  const flags: Flag[] = [];
  if (sizes.batteryKwh > sizes.pvKwp * 1.6) flags.push({ severity: "warn", code: "BATTERY_LARGE", component: "battery", message: "The battery is large for this PV size; it will rarely fill." });
  if (modules > 40) flags.push({ severity: "error", code: "ROOF_MODULES", component: "pv", message: "More modules than a typical roof holds." });
  if (sizes.wallboxKw > 0 && !inputs.ev?.has) flags.push({ severity: "warn", code: "WALLBOX_NO_EV", component: "wallbox", message: "A wallbox without an electric car." });
  return {
    sizes,
    modules,
    alternatives: [],
    metrics: simulateFixture(inputs, sizes),
    confidence: {
      pvKwp: interval(sizes.pvKwp || 8, sizes.pvKwp > 0 ? 0.97 : 0.05),
      batteryKwh: interval(sizes.batteryKwh || 7.5, sizes.batteryKwh > 0 ? 0.9 : 0.1),
      heatPumpKw: interval(sizes.heatPumpKw || 8, sizes.heatPumpKw > 0 ? 0.6 : 0.01),
      wallboxKw: interval(sizes.wallboxKw || 11, sizes.wallboxKw > 0 ? 0.95 : 0.03),
    },
    reasons,
    flags,
    curves: { battery: curve },
    physics: { economicKwh: best.kwh, maxAutarkyKwh: 20, nightLoadKwh: Math.round((inputs.demandKwh / 365) * 0.45 * 10) / 10 },
    askNext: [],
    provenance: { loadProfile: { source: "national_default", confidence: 0.6 } },
    engineVersion: "fixture",
    latencyMs: 0,
  };
}

export const EVAL_FIXTURE: EvalSummary = {
  split: "time",
  nTest: 200,
  chosen: "H1",
  models: {
    B0: { ems: 40, wholeDesign: 0.1, pv: 0.3, battery: 0.3, heatPump: 0.7, wallbox: 0.6 },
    B1: { ems: 55, wholeDesign: 0.2, pv: 0.45, battery: 0.45, heatPump: 0.85, wallbox: 0.75 },
    H1: { ems: 70, wholeDesign: 0.4, pv: 0.6, battery: 0.6, heatPump: 0.9, wallbox: 0.8 },
  },
  selection: null,
  tolerances: { pv: 0.2, battery: 0.25, heatPump: 0.25 },
  generatedAt: "demo",
};

const home = (demandKwh: number, ev: boolean, heating: "Gas" | "Oil"): HomeInputs => ({
  installerId: "default", loadProfile: "H0", priceEurKwh: 0.32, priceEscalation: 0.03,
  demandKwh, persons: 3, ev: { has: ev, kmPerYear: ev ? 12000 : null }, heating: { type: heating },
});
const row = (projectId: string, inputs: HomeInputs, expert: HoldoutRow["expert"], ours: Sizes): HoldoutRow => ({
  projectId, installerId: inputs.installerId, inputs, expert, ours,
});
export const HOLDOUT_FIXTURE: HoldoutRow[] = [
  row("demo-0001", home(4200, true, "Gas"), { pvKwp: 9.45, batteryKwh: 10, heatPumpKw: 0, wallboxKw: 11 }, { pvKwp: 9.45, batteryKwh: 10, heatPumpKw: 0, wallboxKw: 11 }),
  row("demo-0002", home(3000, false, "Oil"), { pvKwp: 6.3, batteryKwh: 5, heatPumpKw: 10.5, wallboxKw: 0 }, { pvKwp: 6.3, batteryKwh: 7.5, heatPumpKw: 10.5, wallboxKw: 0 }),
  row("demo-0003", home(6000, true, "Gas"), { pvKwp: 13.5, batteryKwh: 12.5, heatPumpKw: 0, wallboxKw: 22 }, { pvKwp: 10.8, batteryKwh: 12.5, heatPumpKw: 0, wallboxKw: 11 }),
];

// Demo designs for the pitch (?demo=1). Built on the toy model in ./fixtures, plus what the story needs:
// "ask next" questions and a roof cap. The numbers are NOT engine output, and every page says so.
// The measured figures quoted in `why` are real aggregates from eval/results/latest.json (2026 test, n=325).
import { designFixture, META_FIXTURE, simulateFixture } from "./fixtures";
import { PANEL_KWP } from "./format";
import type { AskNext, Design, EvalSummary, HomeInputs, Sizes } from "./types";

const CATALOG = Object.fromEntries(META_FIXTURE.targets.map((t) => [t.name, t.catalog])) as Record<keyof Sizes, number[]>;
const nearest = (xs: number[], v: number) => xs.reduce((a, b) => (Math.abs(b - v) < Math.abs(a - v) ? b : a));
const atMost = (xs: number[], v: number) => xs.filter((x) => x <= v).at(-1) ?? 0;

const entered = (i: HomeInputs, field: string) => i.provenance?.[field]?.source === "entered";

function priceSwing(a: HomeInputs, b: HomeInputs) {
  const pa = simulateFixture(a, designFixture(a, {}).sizes).priceEur ?? 0;
  const pb = simulateFixture(b, designFixture(b, {}).sizes).priceEur ?? 0;
  return Math.round(Math.abs(pb - pa) / 100) * 100;
}

function askNext(i: HomeInputs): AskNext[] {
  const out: AskNext[] = [];
  const roof = i.building?.roofMaxModules ?? null;
  if (roof === null) {
    out.push({
      field: "building.roofMaxModules",
      question: "How many modules fit the roof?",
      why: "Roof size is the biggest unknown behind PV size. On 2026 projects, knowing it lifted PV agreement from 60% to 82% (upper bound).",
      impact: { components: ["pvKwp", "batteryKwh"], priceSwingEur: priceSwing({ ...i, building: { ...i.building, roofMaxModules: 12 } }, i) || 3000 },
      answers: [
        { label: "12 modules", value: 12 },
        { label: "20 modules", value: 20 },
        { label: "30 modules", value: 30 },
      ],
    });
  }
  if (i.demandKwh === 4500 && !entered(i, "demandKwh")) {
    out.push({
      field: "demandKwh",
      question: "What does the home really use per year?",
      why: "4,500 kWh is the usual placeholder. Real use doubled whole-design agreement on 2026 projects (12% to 21%).",
      impact: { components: ["pvKwp", "batteryKwh"], priceSwingEur: priceSwing({ ...i, demandKwh: 3500 }, { ...i, demandKwh: 6500 }) },
      answers: [
        { label: "3,500 kWh", value: 3500 },
        { label: "5,200 kWh", value: 5200 },
        { label: "6,500 kWh", value: 6500 },
      ],
    });
  }
  return out;
}

/**
 * Evaluation scores for ?demo=1: the REAL aggregates of the frozen 2026 test (eval/results/latest.json, generated
 * 2026-11-07 21:17 UTC, temporal split, n=325, scored once). Only the example projects stay made up.
 */
export const PITCH_EVAL: EvalSummary = {
  split: "time",
  nTest: 325,
  chosen: "composite",
  models: {
    B1: { ems: 55.0, wholeDesign: 0.148, pv: 0.329, battery: 0.4, heatPump: 0.994, wallbox: 0.782 },
    B0: { ems: 61.1, wholeDesign: 0.206, pv: 0.425, battery: 0.474, heatPump: 0.991, wallbox: 0.76 },
    composite: { ems: 61.0, wholeDesign: 0.209, pv: 0.597, battery: 0.474, heatPump: 0.991, wallbox: 0.782 },
  },
  selection: "Chosen per component on the Q4 2025 validation window.",
  tolerances: { pv: 0.2, battery: 0.25, heatPump: 0.25 },
  generatedAt: "2026-11-07T21:17:25+00:00",
};

/** The demo designer behind ?demo=1: the toy proposal, capped to the roof, with "ask next". */
export function pitchDesign(inputs: HomeInputs, locked: Partial<Sizes>): Design {
  const base = designFixture(inputs, locked);
  const roof = inputs.building?.roofMaxModules ?? null;
  let design = base;
  if (roof !== null && locked.pvKwp === undefined) {
    const cap = atMost(CATALOG.pvKwp, roof * PANEL_KWP);
    if (base.sizes.pvKwp > cap) {
      const pvKwp = cap;
      const batteryKwh = locked.batteryKwh ?? (pvKwp > 0 ? nearest(CATALOG.batteryKwh, pvKwp * 1.05) : 0);
      design = designFixture(inputs, { ...locked, pvKwp, batteryKwh });
      design.reasons = [
        { code: "PV_ROOF", target: "pvKwp", text: `PV ${pvKwp.toFixed(1)} kWp: that is what ${roof} modules on this roof allow.` },
        ...design.reasons.filter((r) => r.target !== "pvKwp"),
      ];
    }
  }
  const reasons = [...design.reasons];
  if (design.sizes.wallboxKw > 0 && inputs.ev?.has) {
    reasons.push({ code: "WALLBOX_EV", target: "wallboxKw", text: `Wallbox ${design.sizes.wallboxKw} kW: the household drives an electric car.` });
  }
  if (design.sizes.heatPumpKw === 0 && inputs.heating?.type === "Gas") {
    reasons.push({ code: "HP_NONE", target: "heatPumpKw", text: "No heat pump: the home keeps its gas heating unless the planner adds one." });
  }
  // What the planner entered is reported back as entered, like the engine does.
  const provenance = { ...design.provenance, ...inputs.provenance };
  return { ...design, reasons, provenance, askNext: askNext(inputs), engineVersion: "pitch-demo" };
}

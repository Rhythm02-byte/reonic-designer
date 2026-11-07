// Wording and number formatting shared by the planner and the homeowner view.
import type { HomeInputs, Metrics, Sizes, Target } from "./types";

export const PANEL_KWP = 0.45; // Reonic's modules are 450 Wp
export const LABEL: Record<Target, string> = { pvKwp: "PV", batteryKwh: "Battery", heatPumpKw: "Heat pump", wallboxKw: "Wallbox" };
export const UNIT: Record<Target, string> = { pvKwp: "kWp", batteryKwh: "kWh", heatPumpKw: "kW", wallboxKw: "kW" };
export const HOME_NAME: Record<Target, string> = { pvKwp: "Solar panels", batteryKwh: "Home battery", heatPumpKw: "Heat pump", wallboxKw: "Wallbox" };

export const HEATING_LABEL: Record<string, string> = {
  Gas: "Gas", Oil: "Oil", Heatpump: "Heat pump", OtherRenewable: "Other renewable", OtherNonRenewable: "Other fossil", Unknown: "Unknown",
};

const nf = (max: number) => new Intl.NumberFormat("en-GB", { maximumFractionDigits: max });
export const num = (n: number, max = 1) => nf(max).format(n);
export const eur = (n: number) => `€${nf(0).format(Math.round(n / 10) * 10)}`;
export const eurSigned = (n: number) => `${n < 0 ? "−" : "+"}€${nf(0).format(Math.abs(Math.round(n / 10) * 10))}`;
export const pct = (n: number) => `${Math.round(n * 100)} %`;
export const years = (n: number | null) => (n === null ? "n/a" : `${num(n, 1)} years`);
export const size = (v: number, unit: string) => (v > 0 ? `${num(v)} ${unit}` : "None");
export const panels = (kwp: number) => Math.round(kwp / PANEL_KWP);

export function describe(s: Sizes) {
  const parts = [
    s.pvKwp > 0 ? `${panels(s.pvKwp)} solar panels` : "no solar panels",
    s.batteryKwh > 0 ? `a ${num(s.batteryKwh)} kWh battery` : "no battery",
    s.heatPumpKw > 0 ? `a ${num(s.heatPumpKw)} kW heat pump` : "no heat pump",
    s.wallboxKw > 0 ? `a ${num(s.wallboxKw)} kW wallbox` : "no wallbox",
  ];
  return `3D house with ${parts.join(", ")}.`;
}

/** Flat view of the few inputs the planner edits. Everything else stays in the HomeInputs it came from. */
export type Home = {
  demandKwh: number | null; persons: number | null; heatingType: string; hasEv: boolean; evKm: number | null; roofModules: number | null;
};
export const homeOf = (i: HomeInputs): Home => ({
  demandKwh: i.demandKwh ?? null,
  persons: i.persons ?? null,
  heatingType: i.heating?.type ?? "Unknown",
  hasEv: i.ev?.has ?? false,
  evKm: i.ev?.kmPerYear ?? null,
  roofModules: i.building?.roofMaxModules ?? null,
});

/** Without a car the distance means nothing; sent anyway the model reads it as one and adds a wallbox. */
export function withHome(i: HomeInputs, h: Partial<Home>): HomeInputs {
  const next = { ...homeOf(i), ...h };
  return {
    ...i,
    demandKwh: next.demandKwh ?? 4500,
    persons: next.persons,
    heating: { ...i.heating, type: next.heatingType as NonNullable<HomeInputs["heating"]>["type"] },
    ev: { ...i.ev, has: next.hasEv, kmPerYear: next.hasEv ? next.evKm : null },
    building: next.roofModules === null && !i.building ? i.building : { ...i.building, roofMaxModules: next.roofModules },
  };
}

export const DEMO_INPUTS: HomeInputs = {
  installerId: "default",
  demandKwh: 4500,
  loadProfile: "H0",
  persons: 4,
  priceEurKwh: 0.32,
  priceEscalation: 0.03,
  ev: { has: true, kmPerYear: 12000 },
  heating: { type: "Gas" },
};

/** Metric deltas for the diff bar. */
export function deltas(a: Metrics | null, b: Metrics | null) {
  const d = (x: number | null | undefined, y: number | null | undefined) => (x == null || y == null ? null : y - x);
  return { price: d(a?.priceEur, b?.priceEur), autarkyPts: d(a?.autarky, b?.autarky) === null ? null : Math.round((b!.autarky! - a!.autarky!) * 100) };
}

/** What "none" means for each part, in the homeowner's words. */
export const CHOICE_NOTE: { none: Record<Target, string> } = {
  none: {
    pvKwp: "No solar panels in this setup.",
    batteryKwh: "No battery: solar power you don't use right away goes to the grid.",
    heatPumpKw: "Your current heating stays as it is.",
    wallboxKw: "No wallbox: the car charges from a normal socket or public chargers.",
  },
};

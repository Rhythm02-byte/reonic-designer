// A reference product per target, to turn a kWp/kWh/kW size into "N x product" for the planner.
// ponytail: only pv_kwp is a real Reonic number (PANEL_KWP, from src/reonic/data.py MODULE_WP). The rest are
// placeholder units since the dataset has no per-product catalog (see data.py: battery/heat pump/wallbox sizes
// are continuous, not counts of a fixed product) — swap in real SKUs when Reonic shares them.
import { PANEL_KWP } from "./copy";
import type { Target } from "./api";

export const CATALOG: Record<Target, { name: string; unitSize: number }> = {
  pv_kwp: { name: "Solar panel (450 Wp)", unitSize: PANEL_KWP },
  battery_kwh: { name: "Battery module (5 kWh)", unitSize: 5 }, // ponytail: assumed unit size, no real SKU
  heat_pump_kw: { name: "Heat pump", unitSize: Infinity }, // one unit regardless of kW
  wallbox_kw: { name: "Wallbox", unitSize: Infinity }, // one unit regardless of kW
};

/** How many units of the reference product a size needs; 0 when nothing is installed. */
export function quantityFor(t: Target, value: number): number {
  if (value <= 0) return 0;
  const { unitSize } = CATALOG[t];
  return Number.isFinite(unitSize) ? Math.max(1, Math.ceil(value / unitSize)) : 1;
}

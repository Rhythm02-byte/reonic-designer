// The planner -> homeowner offer link. Everything travels in the URL hash, so it never reaches a server log.
import { TARGETS } from "./types";
import type { HomeInputs, Sizes, Target } from "./types";

export type Offer = { v: 2; inputs: HomeInputs; recommended: Sizes; options: Record<Target, number[]> };

/** The homeowner may resize only these; the rest stays as recommended. */
export const SHAREABLE: Target[] = ["batteryKwh", "wallboxKw"];

const uniqSorted = (xs: number[]) => [...new Set(xs.map((x) => Math.round(x * 100) / 100))].sort((a, b) => a - b);

/** Sizes a homeowner may pick: the recommendation, its catalog neighbours and (except PV) "none". */
export function defaultOptions(t: Target, rec: number, catalog: number[]): number[] {
  const cat = uniqSorted(catalog.filter((c) => c > 0));
  const below = cat.filter((c) => c < rec).at(-1);
  const above = cat.find((c) => c > rec) ?? (rec === 0 ? cat[Math.floor(cat.length / 2)] : undefined);
  const near = t === "heatPumpKw" ? [] : [below, above].filter((x): x is number => x !== undefined);
  return uniqSorted([...(t === "pvKwp" && rec > 0 ? [] : [0]), rec, ...near]);
}

export function buildOptions(rec: Sizes, catalogs: Record<Target, number[]>): Record<Target, number[]> {
  return Object.fromEntries(
    TARGETS.map((t) => [t, SHAREABLE.includes(t) ? defaultOptions(t, rec[t], catalogs[t] ?? []) : [rec[t]]]),
  ) as Record<Target, number[]>;
}

const toB64 = (s: string) => btoa(String.fromCharCode(...new TextEncoder().encode(s)));
const fromB64 = (s: string) => new TextDecoder().decode(Uint8Array.from(atob(s), (c) => c.charCodeAt(0)));

export const encodeOffer = (o: Offer) => toB64(JSON.stringify(o)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

const isSize = (x: unknown): x is number => typeof x === "number" && Number.isFinite(x) && x >= 0 && x <= 1000;

/** The link is user-controlled: anything malformed yields null. The engine validates the inputs again. */
export function decodeOffer(code: string): Offer | null {
  try {
    const o = JSON.parse(fromB64(code.replace(/-/g, "+").replace(/_/g, "/")));
    if (o?.v !== 2 || typeof o.inputs !== "object" || o.inputs === null) return null;
    if (typeof o.inputs.installerId !== "string" || typeof o.inputs.demandKwh !== "number") return null;
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

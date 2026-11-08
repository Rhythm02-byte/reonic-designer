"use client";
// Customers per planner, kept in this browser.
// ponytail: localStorage only, so the team list is per browser; move it to the API once planners share a backend.
import { useSyncExternalStore } from "react";
import type { Inputs, Values } from "./api";
import { DEMO_INPUTS } from "./copy";
import type { GeoLocation } from "@/components/Location";
import type { HouseAsset, HouseLayout } from "./real-house";

export type CustomerStatus = "lead" | "quoted" | "won" | "lost";
export const STATUS_ORDER: CustomerStatus[] = ["lead", "quoted", "won", "lost"];
export const STATUS_LABEL: Record<CustomerStatus, string> = { lead: "Lead", quoted: "Quoted", won: "Won", lost: "Lost" };

export type Customer = { id: string; name: string; owner: string; inputs: Inputs; locked?: Partial<Values>; location?: GeoLocation; realHouse?: HouseAsset; roofLayout?: HouseLayout; roofCapacityConfirmed?: boolean; status?: CustomerStatus };
export type Workspace = { me: string; active: string; customers: Customer[] };
export const TEAM = ["Anna Weber", "Jonas Keller", "Lea Brandt"];
const SEED: Workspace = {
  me: TEAM[0],
  active: "c1",
  customers: [
    { id: "c1", name: "Familie Berger", owner: TEAM[0], inputs: DEMO_INPUTS },
    { id: "c2", name: "Haus Yilmaz", owner: TEAM[0], inputs: { ...DEMO_INPUTS, annual_consumption_kwh: 3200, household_size: 2, has_ev: false, heating_type: "oil" } },
    { id: "c3", name: "Schneider, Garching", owner: TEAM[1], inputs: { ...DEMO_INPUTS, annual_consumption_kwh: 6200, household_size: 5, ev_km_per_year: 18000 } },
    { id: "c4", name: "Müller Bungalow", owner: TEAM[2], inputs: { ...DEMO_INPUTS, annual_consumption_kwh: 2800, household_size: 2, has_ev: false, heating_type: "heat_pump" } },
  ],
};
// ours: review fix, a new customer starts with the household facts unknown (empty = unknown, "Ask next" asks),
// not the demo family's 4,500 kWh / EV / gas. Only tariff defaults are prefilled.
const NEW_INPUTS: Inputs = Object.fromEntries(Object.keys(DEMO_INPUTS).map((k) => [k, null]));
Object.assign(NEW_INPUTS, { electricity_price_eur_kwh: DEMO_INPUTS.electricity_price_eur_kwh, energy_price_increase: DEMO_INPUTS.energy_price_increase });
const KEY = "rhythm.workspace.v1";
const subs = new Set<() => void>();
let cache: Workspace | null = null;
function read(): Workspace {
  if (!cache) {
    try {
      const w = JSON.parse(localStorage.getItem(KEY) ?? "null");
      // ours: every customer must be an object with id, name and inputs, else a hand-edited/old entry crashes the planner
      const ok = (c: unknown) => !!c && typeof c === "object" && typeof (c as { id?: unknown }).id === "string" &&
        typeof (c as { name?: unknown }).name === "string" && !!(c as { inputs?: unknown }).inputs && typeof (c as { inputs?: unknown }).inputs === "object";
      cache = w && typeof w.me === "string" && Array.isArray(w.customers) && w.customers.length && w.customers.every(ok) ? w : SEED;
    } catch {
      cache = SEED;
    }
  }
  return cache!;
}
export function update(fn: (w: Workspace) => Workspace) {
  cache = fn(read());
  try {
    localStorage.setItem(KEY, JSON.stringify(cache));
  } catch {
    // Private mode or full storage: the change lives until the tab closes.
  }
  subs.forEach((f) => f());
}
const subscribe = (f: () => void) => {
  subs.add(f);
  return () => subs.delete(f);
};

export function useWorkspace(): Workspace {
  return useSyncExternalStore(subscribe, read, () => SEED);
}

/** Creates the customer, makes it the active one, and returns its id. */
export function addCustomer(newName: string, location: GeoLocation | null, owner?: string): string {
  const cid = crypto.randomUUID();
  update((w) => ({
    ...w,
    active: cid,
    customers: [...w.customers, { id: cid, name: newName, owner: owner ?? w.me, inputs: NEW_INPUTS, location: location ?? undefined }], // ours: review fix
  }));
  return cid;
}

/** Removes a customer; refuses to empty the workspace. Switches off the active customer if needed. */
export function removeCustomer(id: string) {
  update((w) => {
    if (w.customers.length <= 1) return w;
    const customers = w.customers.filter((c) => c.id !== id);
    return { ...w, customers, active: w.active === id ? customers[0].id : w.active };
  });
}

export function setCustomerStatus(id: string, status: CustomerStatus) {
  update((w) => ({ ...w, customers: w.customers.map((c) => (c.id === id ? { ...c, status } : c)) }));
}

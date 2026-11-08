// Pitch mode (iemko): the /pitch deck shows the real pages in iframes and drives the planner with window messages.
// Opt-in only: without ?demo=1 and without a message from /pitch, the app behaves as before.
import type { Inputs, Values } from "./api";

/** `?demo=1` forces the labelled toy model (lib/fixtures.ts) even when the engine is up, so the pitch runs offline. */
export function isDemoForced(): boolean {
  if (typeof window === "undefined") return false;
  return new URLSearchParams(window.location.search).get("demo") === "1";
}

/** Sent by /pitch to the planner iframe. With `because`, the planner treats it as a planner change (diff bar). */
export type PitchPlan = { type: "pitch:plan"; inputs: Inputs; locked?: Partial<Values>; because?: string };

export function isPitchPlan(data: unknown): data is PitchPlan {
  const d = data as Partial<PitchPlan> | null;
  return !!d && d.type === "pitch:plan" && typeof d.inputs === "object" && d.inputs !== null;
}

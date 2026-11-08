// Pitch mode: the /pitch deck shows the real pages in iframes and drives them with window messages.
// Everything here is opt-in: without ?demo=1 and without a message from /pitch, the app behaves as before.
import type { HomeInputs, Sizes } from "./types";

/** `?demo=1` forces the labelled demo data (lib/pitchDemo.ts) even when the engine is up, so the pitch runs offline. */
export function isDemoForced(): boolean {
  if (typeof window === "undefined") return false;
  return new URLSearchParams(window.location.search).get("demo") === "1";
}

/** Sent by /pitch to the planner iframe. With `because`, the planner treats it as a user change (diff bar). */
export type PitchPlan = { type: "pitch:plan"; inputs: HomeInputs; locked?: Partial<Sizes>; because?: string };

export function isPitchPlan(data: unknown): data is PitchPlan {
  const d = data as Partial<PitchPlan> | null;
  return !!d && d.type === "pitch:plan" && typeof d.inputs === "object" && d.inputs !== null;
}

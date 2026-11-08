// Test Lab: types + helpers for eval/history/runs.jsonl (written by eval/record.py).
export type Scores = Partial<Record<"ems" | "wholeDesign" | "pv" | "battery" | "heatPump" | "wallbox" | "latencyP50ms", number>>;
type Block = { n: number | null; models: Record<string, Scores> };
type MeanSd = { mean: number | null; sd: number | null; n: number | null };

export type Run = {
  id: string;
  timestamp: string;
  kind: "all" | "quick" | "full" | "honesty" | "oracle" | "research";
  label?: string;
  git: { branch: string; commit: string | null; dirty: boolean };
  durationSec?: number;
  testScored: boolean;
  comparisonKey?: string;
  validation?: Block;
  test?: Block;
  repeated?: { ours: MeanSd; b0: MeanSd; gap: MeanSd };
  honesty?: { realWhole?: number; shuffledWhole?: number; fuzzBroken?: number; fuzzN?: number };
  oracle?: Record<string, { gainWhole: number | null; upperBound: boolean }>;
};

/** One run per line; malformed lines are skipped and counted, never fatal. */
export function parseHistory(text: string): { runs: Run[]; invalid: number } {
  const runs: Run[] = [];
  let invalid = 0;
  for (const line of text.split(/\r?\n/)) {
    if (!line.trim()) continue;
    try {
      const r = JSON.parse(line) as Run;
      if (typeof r.id !== "string" || !Number.isFinite(Date.parse(r.timestamp)) || typeof r.git?.branch !== "string") throw 0;
      runs.push(r);
    } catch {
      invalid++;
    }
  }
  return { runs: runs.sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp)), invalid };
}

export const MODELS = [
  { key: "B1", name: "Rule of thumb" },
  { key: "B0", name: "Installer's usual design" },
  { key: "ours", name: "Ours" },
] as const;

/** Runs that score the validation window: the comparable series for the timeline. */
export const scored = (runs: Run[]) => runs.filter((r) => r.kind !== "research" && r.validation?.models.ours);
/** Never derive a comparison key for legacy runs or join unlike evaluation populations. */
export const comparable = (a: Run, b: Run) =>
  typeof a.comparisonKey === "string" && a.comparisonKey.trim().length > 0 &&
  a.comparisonKey === b.comparisonKey && a.kind !== "research" && b.kind !== "research" &&
  a.validation?.n === b.validation?.n;

export function researchPair(run: Run): [string, Scores][] {
  return Object.entries(run.validation?.models ?? {});
}
export const latestWith = <K extends keyof Run>(runs: Run[], key: K) => [...runs].reverse().find((r) => r[key] != null);

export const pts = (v: number | null | undefined, rate: boolean) =>
  v == null ? null : rate ? v * 100 : v;
export const fmt = (v: number | null | undefined, rate = false, digits = 1) =>
  v == null ? "–" : `${(rate ? v * 100 : v).toFixed(digits)}${rate ? "%" : ""}`;
export const when = (iso: string) =>
  new Date(iso).toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Berlin" }); // fixed zone: server and browser render the same text (no hydration mismatch)

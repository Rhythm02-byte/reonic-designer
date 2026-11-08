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
// ours: Test Lab at-a-glance helpers (headline numbers, research table, de-duplicated history).
export const day = (iso: string) => new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "Europe/Berlin" });

/** Latest run that scored the unseen 2026 homes for our model. */
export const examRun = (runs: Run[]) => [...runs].reverse().find((r) => r.kind !== "research" && r.test?.models.ours);

export type ResearchRow = { name: string; gain: number; adopted: boolean };
/** One row per research run: gain = candidate minus default, in points of whole-design match (repeated splits). */
export function researchRows(runs: Run[]): ResearchRow[] {
  return runs.filter((r) => r.kind === "research").map((r) => {
    const label = r.label ?? "";
    const name = label.replace(/^research\s+/, "").replace(/\s+vs\s+default.*$/, "").replace(/__/g, " · ").replace(/_/g, " ");
    const gap = r.repeated?.gap?.mean;
    return { name: name || r.id, gain: gap != null ? gap * 100 : 0, adopted: /\(adopt\)/.test(label) };
  }).sort((a, b) => b.gain - a.gain);
}

/** Whole-design % (validation) per run; identical results collapsed; newest 12 points. */
export function historyPoints(runs: Run[]) {
  const seen = new Set<string>();
  const out: { t: string; ours: number; b0: number | null }[] = [];
  for (const r of runs) {
    const m = r.kind === "research" ? undefined : r.validation?.models;
    const ours = m?.ours?.wholeDesign;
    if (ours == null) continue;
    const b0 = m?.B0?.wholeDesign ?? null;
    const key = `${r.validation?.n}|${ours}|${b0}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ t: r.timestamp, ours: ours * 100, b0: b0 == null ? null : b0 * 100 });
  }
  return out.slice(-12);
}

export const when = (iso: string) =>
  new Date(iso).toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Berlin" }); // fixed zone: server and browser render the same text (no hydration mismatch)

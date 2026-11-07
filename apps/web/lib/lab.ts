export type Scores = Partial<Record<"ems" | "wholeDesign" | "pv" | "battery" | "heatPump" | "wallbox" | "latencyP50ms" | "latencyP95ms", number | null>>;
export type Run = {
  id: string; timestamp: string;
  git: { branch: string; commit: string | null; dirty: boolean };
  engineVersion?: string | null; policyConfig?: Record<string, unknown>; durationSec?: number | null;
  splits: Record<string, { nTest: number | null; models: Record<string, Scores> }>;
  selection?: { model?: string | null; nValidation?: number | null; config?: Record<string, unknown> };
  oracle?: Record<string, { n?: number | null; upperBound?: boolean; unknown: Scores; answered: Scores; gain: Scores }>;
  honesty?: { shuffledLabel?: { ems?: number | null; passed?: boolean | null }; repeatedSplit?: { mean?: number | null; sd?: number | null; n?: number | null }; fuzz?: { passed?: number | null; total?: number | null } };
};

export function selectedModel(run: Run) {
  const models = run.splits.temporal?.models ?? {};
  const chosen = run.selection?.model;
  return chosen && models[chosen] ? chosen : models.composite ? "composite" : models.M1 ? "M1" : null;
}
export function selectedScores(run: Run): Scores {
  const model = selectedModel(run);
  return model ? run.splits.temporal?.models[model] ?? {} : {};
}
export function format(value: number | null | undefined, rate = false) {
  return typeof value === "number" && Number.isFinite(value) ? `${(value * (rate ? 100 : 1)).toFixed(1)}${rate ? "%" : ""}` : "Not recorded";
}

/** Validate the fields the UI traverses; a malformed line never takes down the page. */
export function parseHistory(source: string): { runs: Run[]; invalid: number } {
  const runs: Run[] = [];
  let invalid = 0;
  const object = (v: unknown): v is Record<string, unknown> => !!v && typeof v === "object" && !Array.isArray(v);
  const seen = new Set<string>();
  for (const line of source.split(/\r?\n/).filter((line) => line.trim())) {
    try {
      const value: unknown = JSON.parse(line);
      if (!object(value) || typeof value.id !== "string" || seen.has(value.id) || typeof value.timestamp !== "string" || !Number.isFinite(Date.parse(value.timestamp)) || !object(value.git) || typeof value.git.branch !== "string" || !object(value.splits)) throw new Error("Invalid record");
      for (const split of Object.values(value.splits)) {
        if (!object(split) || !object(split.models)) throw new Error("Invalid split");
        for (const model of Object.values(split.models)) {
          if (!object(model) || Object.values(model).some((n) => n !== null && (typeof n !== "number" || !Number.isFinite(n)))) throw new Error("Invalid metrics");
        }
      }
      if (value.selection != null && !object(value.selection)) throw new Error("Invalid selection");
      if (value.oracle != null && (!object(value.oracle) || Object.values(value.oracle).some((v) => !object(v) || !object(v.gain) || !object(v.unknown) || !object(v.answered)))) throw new Error("Invalid oracle");
      if (value.honesty != null && (!object(value.honesty) || Object.values(value.honesty).some((v) => v != null && !object(v)))) throw new Error("Invalid honesty");
      seen.add(value.id);
      runs.push(value as Run);
    } catch { invalid++; }
  }
  return { runs: runs.sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp)), invalid };
}

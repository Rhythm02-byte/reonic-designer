"use client";
// The proof: how often the model gets the whole design right on projects it never saw, next to a rule of thumb,
// and a few of those projects side by side ("expert vs ours"). Numbers come from /eval/summary and /holdout.
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { LABEL, pct, size, UNIT } from "@/lib/format";
import { TARGETS } from "@/lib/types";
import type { EvalSummary, HoldoutRow, ModelScore, Source, Target } from "@/lib/types";
import { Badge, Button, ErrorNote } from "./ui";

type Tolerances = EvalSummary["tolerances"];
const TOLERANCE_KEY: Partial<Record<Target, keyof Tolerances>> = { pvKwp: "pv", batteryKwh: "battery", heatPumpKw: "heatPump" };

/** Both agree on include/exclude, and the size is within the evaluation's tolerance when known (the wallbox has none). */
function matches(t: Target, ours: number, expert: number | null, tol: Tolerances) {
  if (expert === null) return ours > 0; // offered, size unknown
  if (expert === 0) return ours === 0;
  const k = TOLERANCE_KEY[t];
  return ours > 0 && (k === undefined || Math.abs(ours - expert) / expert <= tol[k]);
}

// The heat pump is left out of the bars: nearly every project gets the same answer.
const BARS: { label: string; get: (m: ModelScore) => number }[] = [
  { label: "Whole design", get: (m) => m.wholeDesign },
  { label: "Solar", get: (m) => m.pv },
  { label: "Battery", get: (m) => m.battery },
  { label: "Wallbox", get: (m) => m.wallbox },
];

function pickModels(r: EvalSummary) {
  const ours = r.models[r.chosen] ?? Object.values(r.models).at(-1);
  const rule = r.models.B1 ?? r.models.B0;
  return ours && rule ? { ours, rule } : null;
}

function Bars({ ours, rule }: { ours: ModelScore; rule: ModelScore }) {
  return (
    <div className="space-y-3">
      <div className="flex gap-4 text-xs text-zinc-300" aria-hidden>
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-paper" /> Our model
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-zinc-500" /> Rule of thumb
        </span>
      </div>
      <ul className="space-y-2.5">
        {BARS.map(({ label, get }) => (
          <li key={label}>
            <div className="flex justify-between text-xs">
              <span className="text-paper">{label}</span>
              <span className="text-zinc-300 tabular-nums">
                {pct(get(ours))} <span className="sr-only">for our model,</span>
                <span aria-hidden> · </span>
                {pct(get(rule))} <span className="sr-only">for the rule of thumb</span>
              </span>
            </div>
            <div className="mt-1 space-y-0.5" aria-hidden>
              <div className="h-1.5 rounded-full bg-paper" style={{ width: `${Math.max(get(ours) * 100, 1)}%` }} />
              <div className="h-1.5 rounded-full bg-zinc-500" style={{ width: `${Math.max(get(rule) * 100, 1)}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Reality({ onLoad }: { onLoad: (row: HoldoutRow) => void }) {
  const [report, setReport] = useState<{ data: EvalSummary; source: Source } | null>(null);
  const [rows, setRows] = useState<HoldoutRow[] | null>(null);
  const [i, setI] = useState(-1);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.evalSummary().then(setReport, (e: Error) => setError(e.message));
    api.holdout().then((r) => setRows(r.data), (e: Error) => setError(e.message));
  }, []);

  const row = rows && i >= 0 ? rows[i] : null;
  const next = () => {
    if (!rows?.length) return;
    const k = (i + 1) % rows.length;
    setI(k);
    onLoad(rows[k]);
  };
  const models = report ? pickModels(report.data) : null;

  return (
    // The one loud element of the page: ink on the gradient (white fails AA there), a dark panel for the evidence.
    <section aria-labelledby="reality" className="bg-reonic space-y-3 rounded-2xl p-4 text-ink">
      <h2 id="reality" className="text-xs font-semibold tracking-wide uppercase">Checked against reality</h2>
      <ErrorNote error={error} />
      {report === null ? (
        !error && <div className="h-14 animate-pulse rounded-xl bg-ink/10" />
      ) : models ? (
        <p className="text-lg leading-snug font-semibold tracking-tight">
          {pct(models.ours.wholeDesign)} of {report.data.nTest} projects the model never saw get the whole design right. A rule of
          thumb gets {pct(models.rule.wholeDesign)}.
        </p>
      ) : (
        <p className="text-sm font-semibold">No evaluation yet. Run <code>npm run eval</code>.</p>
      )}
      {report?.source === "demo" && (
        <p className="text-xs font-medium">Demo numbers: the engine is not connected, so none of this was measured.</p>
      )}

      <div className="space-y-4 rounded-xl bg-ink p-4 text-sm text-zinc-300">
        {models && report && (
          <>
            <Bars ours={models.ours} rule={models.rule} />
            <p className="text-xs">
              Measured on the {report.data.nTest} held-out projects ({report.data.split} split). Right = each size within the
              evaluation&apos;s tolerance of the expert&apos;s, or both agree on none.
              {models.rule.wallbox > models.ours.wallbox && " On the wallbox alone the rule of thumb is still better."}
            </p>
          </>
        )}
        <Button variant="secondary" className="w-full" onClick={next} disabled={!rows?.length}>
          {row ? "Next real project" : rows === null && !error ? "Loading real projects…" : "Try a real project"}
        </Button>
        {rows === null && !error && <div aria-hidden className="h-24 animate-pulse rounded-lg bg-white/10" />}
        {row && (
          <div>
            <table className="w-full">
              <caption className="sr-only">The expert&apos;s design for this project compared with our model</caption>
              <thead>
                <tr className="text-left text-xs text-zinc-400">
                  <th scope="col" className="py-1 font-mono font-normal">
                    {row.projectId.slice(0, 8)}
                  </th>
                  <th scope="col" className="py-1 font-medium">Expert</th>
                  <th scope="col" className="py-1 font-medium">Ours</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {TARGETS.map((t) => (
                  <tr key={t}>
                    <th scope="row" className="py-1.5 text-left font-medium text-paper">
                      {LABEL[t]}
                    </th>
                    <td className="py-1.5 tabular-nums">{row.expert[t] === null ? "Yes, size unknown" : size(row.expert[t], UNIT[t])}</td>
                    <td className="py-1.5 tabular-nums">
                      {size(row.ours[t], UNIT[t])}{" "}
                      {report && matches(t, row.ours[t], row.expert[t], report.data.tolerances) ? <Badge tone="good">match</Badge> : <Badge tone="warn">off</Badge>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-xs text-zinc-400">
              &ldquo;Ours&rdquo; never saw this project. The house shows the live model, which was trained on all projects.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

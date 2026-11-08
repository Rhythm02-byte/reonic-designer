"use client";
// ours: replaces his Reality panel in the Planner (same look). The comparison is our model against the installer's
// usual design (B0), worded honestly; a generic rule of thumb (B1) is shown only as a footnote.
import { useEffect, useMemo, useState } from "react";
import { api, TARGETS, type Evaluation, type HoldoutRow, type Target } from "@/lib/api";
import { LABEL, pct, size, UNIT } from "@/lib/copy";
import { Badge, Button, ErrorNote } from "./ui";

// Same as the engine's eval tolerances: relative size error that still counts as "matches the expert".
const TOLERANCE: Record<Target, number> = { pv_kwp: 0.2, battery_kwh: 0.25, heat_pump_kw: 0.25, wallbox_kw: Infinity };

function matches(t: Target, ours: number, expert: number | null) {
  if (expert === null) return ours > 0;
  if (expert === 0) return ours === 0;
  return ours > 0 && Math.abs(ours - expert) / expert <= TOLERANCE[t];
}

type Whole = Evaluation["model"];
const BARS: { label: string; get: (w: Whole) => number }[] = [
  { label: "Whole design", get: (w) => w.whole_design_within_tolerance },
  { label: "Solar", get: (w) => w.pv_kwp.within_tolerance },
  { label: "Battery", get: (w) => w.battery_kwh.within_tolerance },
  { label: "Wallbox", get: (w) => w.wallbox_kw.within_tolerance },
];

const level = (a: number, b: number) => Math.round(a * 100) === Math.round(b * 100);

/** One honest sentence: where the model clearly gains, and where it only matches the installer's habit. */
function headline(r: Evaluation) {
  const m = r.model;
  const b = r.baseline;
  const solarGain = m.pv_kwp.within_tolerance - b.pv_kwp.within_tolerance;
  const whole = m.whole_design_within_tolerance - b.whole_design_within_tolerance;
  const first =
    solarGain >= 0.05
      ? "Solar matches the experts far more often"
      : solarGain <= -0.05
        ? "Solar matches the experts less often"
        : "Solar matches the experts about as often";
  const second = level(m.whole_design_within_tolerance, b.whole_design_within_tolerance)
    ? "the whole design is level with the installer's own habit"
    : Math.abs(whole) < 0.05
      ? "the whole design is on par with the installer's own habit (within noise)"
      : whole > 0
        ? "the whole design matches more often than the installer's own habit"
        : "the whole design matches less often than the installer's own habit";
  return `${first}; ${second}.`;
}

function Bars({ report }: { report: Evaluation }) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-300" aria-hidden>
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-paper" /> Our model
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-zinc-500" /> Installer&apos;s usual design
        </span>
      </div>
      <ul className="space-y-2.5">
        {BARS.map(({ label, get }) => {
          const m = get(report.model);
          const b = get(report.baseline);
          return (
            <li key={label}>
              <div className="flex justify-between text-xs">
                <span className="text-paper">{label}</span>
                <span className="text-zinc-300 tabular-nums">
                  {pct(m)} <span className="sr-only">for our model,</span>
                  <span aria-hidden> · </span>
                  {pct(b)} <span className="sr-only">for the installer&apos;s usual design</span>
                </span>
              </div>
              <div className="mt-1 space-y-0.5" aria-hidden>
                <div className="h-1.5 rounded-full bg-paper" style={{ width: `${Math.max(m * 100, 1)}%` }} />
                <div className="h-1.5 rounded-full bg-zinc-500" style={{ width: `${Math.max(b * 100, 1)}%` }} />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function Evidence({ onLoad }: { onLoad: (row: HoldoutRow) => void }) {
  const [report, setReport] = useState<Evaluation | null>(null);
  const [rows, setRows] = useState<HoldoutRow[] | null>(null);
  const [i, setI] = useState(-1);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.evaluation().then(setReport, (e: Error) => setError(e.message));
    api.holdout().then((r) => setRows(r.rows), (e: Error) => setError(e.message));
  }, []);

  // Fixed order (by project id), starting with the first project where every part matches, so the first one shown
  // does not depend on the draw. Labelled below: this is not a typical project.
  const ordered = useMemo(() => {
    if (!rows) return null;
    const sorted = [...rows].sort((a, b) => a.project_id.localeCompare(b.project_id));
    const ok = (r: HoldoutRow) => TARGETS.every((t) => matches(t, r.ours[t], r.expert[t]));
    const start = Math.max(0, sorted.findIndex(ok));
    return [...sorted.slice(start), ...sorted.slice(0, start)];
  }, [rows]);
  const allMatch = ordered ? ordered.filter((r) => TARGETS.every((t) => matches(t, r.ours[t], r.expert[t]))).length : 0;
  const row = ordered && i >= 0 ? ordered[i] : null;
  const next = () => {
    if (!ordered?.length) return;
    const k = (i + 1) % ordered.length;
    setI(k);
    onLoad(ordered[k]);
  };
  const ready = report !== null && "model" in report;

  return (
    <section aria-labelledby="reality" className="bg-reonic space-y-3 rounded-2xl p-4 text-ink">
      <h2 id="reality" className="text-xs font-semibold tracking-wide uppercase">Checked against reality</h2>
      <ErrorNote error={error} />
      {report === null ? (
        !error && <div className="h-14 animate-pulse rounded-xl bg-ink/10" />
      ) : ready ? (
        <>
          <p className="text-lg leading-snug font-semibold tracking-tight">{headline(report)}</p>
          <p className="text-xs">
            On {report.n_test} projects the model never saw, compared with the design each installer usually picks. A
            whole-design match means every part agrees with what the installer recorded. It is not the chance that this
            home&apos;s design is right.
          </p>
        </>
      ) : (
        <p className="text-sm font-semibold">No evaluation yet. Run the evaluation (make eval).</p>
      )}

      <div className="space-y-4 rounded-xl bg-ink p-4 text-sm text-zinc-300">
        {ready && (
          <>
            <Bars report={report} />
            <p className="text-xs">
              Right = solar within 20 %, battery and heat pump within 25 %, wallbox included or not.
              {report.reference &&
                ` A generic rule of thumb gets the whole design right in ${pct(report.reference.whole_design_within_tolerance)}.`}
            </p>
          </>
        )}
        <Button variant="secondary" className="w-full" onClick={next} disabled={!ordered?.length}>
          {row ? "Next real project" : "Try a real project"}
        </Button>
        {row && (
          <div>
            <table className="w-full">
              <caption className="sr-only">The expert&apos;s design for this project compared with our model</caption>
              <thead>
                <tr className="text-left text-xs text-zinc-400">
                  <th scope="col" className="py-1 font-mono font-normal">
                    {row.project_id.slice(0, 8)}
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
                      {matches(t, row.ours[t], row.expert[t]) ? <Badge tone="good">match</Badge> : <Badge tone="warn">off</Badge>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-xs text-zinc-400">
              &ldquo;Ours&rdquo; never saw this project: the model was trained only on projects before 2026. The house shows
              that same model. These {ordered?.length} projects are drawn to cover different kinds of homes, in a fixed order; the
              first is one where every part matches, so it is not typical (all parts match in {allMatch} of {ordered?.length}).
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

"use client";
// Held-out projects (reports/test_predictions.csv) and the evaluation report (reports/eval.json).
import { useEffect, useState } from "react";
import { api, TARGETS, type Evaluation, type HoldoutRow, type Target } from "@/lib/api";
import { CHOICE_LABEL, FIELD_COPY, LABEL, num, pct, size, UNIT } from "@/lib/copy";
import { Badge, Button, Card, ErrorNote, Stat } from "./ui";

// Same as src/reonic/evaluate.py TOLERANCE: relative size error that still counts as "matches the expert".
const TOLERANCE: Record<Target, number> = { pv_kwp: 0.2, battery_kwh: 0.25, heat_pump_kw: 0.25, wallbox_kw: Infinity };
const TOLERANCE_TEXT = "PV within 20 %, battery and heat pump within 25 %, wallbox: included or not";

/** Mirrors evaluate.metrics: both agree on include/exclude, and the size is within tolerance when known. */
function matches(t: Target, ours: number, expert: number | null) {
  if (expert === null) return ours > 0; // offered, size unknown
  if (expert === 0) return ours === 0;
  return ours > 0 && Math.abs(ours - expert) / expert <= TOLERANCE[t];
}

function useLoad<T>(load: () => Promise<T>) {
  const [state, setState] = useState<{ data?: T; error?: string }>({});
  useEffect(() => {
    load().then((data) => setState({ data }), (e: Error) => setState({ error: e.message }));
  }, [load]);
  return state;
}

const loadHoldout = () => api.holdout().then((r) => r.rows);

export function CompareTab({ onLoad }: { onLoad: (row: HoldoutRow) => void }) {
  const { data: rows, error } = useLoad(loadHoldout);
  const [i, setI] = useState(0);
  if (error) return <ErrorNote error={error} />;
  if (!rows) return <div className="h-96 animate-pulse rounded-2xl bg-sand" />;
  if (!rows.length) return <p className="text-sm">No held-out results yet. Run <code>python -m reonic eval</code>.</p>;

  const row = rows[i];
  const who = [
    { key: "expert", label: "Expert planner" },
    { key: "ours", label: "Our model (held out)" },
    { key: "baseline", label: "Rule of thumb" },
  ] as const;
  const score = (k: "ours" | "baseline") => TARGETS.filter((t) => matches(t, row[k][t] ?? 0, row.expert[t])).length;
  const shown = ["annual_consumption_kwh", "heating_type", "has_ev", "existing_pv_kwp", "load_profile", "electricity_price_eur_kwh"];

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
      <Card className="p-5">
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-0 flex-1">
            <label htmlFor="project" className="text-xs text-muted">
              Held-out project ({rows.length} the model never saw while training)
            </label>
            <select
              id="project"
              value={i}
              onChange={(e) => setI(Number(e.target.value))}
              className="mt-1 w-full rounded-lg bg-white px-2.5 py-1.5 font-mono text-sm text-ink ring-1 ring-zinc-200"
            >
              {rows.map((r, k) => (
                <option key={r.project_id} value={k}>
                  #{k + 1} · {r.project_id.slice(0, 8)} · installer {r.installer_id.slice(0, 6)}
                </option>
              ))}
            </select>
          </div>
          <Button variant="secondary" onClick={() => setI((i - 1 + rows.length) % rows.length)} aria-label="Previous project">
            ←
          </Button>
          <Button variant="secondary" onClick={() => setI((i + 1) % rows.length)} aria-label="Next project">
            →
          </Button>
        </div>

        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-sm">
            <caption className="sr-only">Expert design compared with our model and the rule of thumb</caption>
            <thead>
              <tr className="text-left text-xs text-muted">
                <th scope="col" className="py-2 font-medium">Component</th>
                {who.map((w) => (
                  <th key={w.key} scope="col" className="py-2 font-medium">
                    {w.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {TARGETS.map((t) => (
                <tr key={t}>
                  <th scope="row" className="py-2.5 text-left font-medium text-ink">
                    {LABEL[t]}
                  </th>
                  {who.map(({ key }) => {
                    const v = row[key][t];
                    const ok = key !== "expert" && matches(t, v ?? 0, row.expert[t]);
                    return (
                      <td key={key} className="py-2.5 tabular-nums">
                        <span className={key === "expert" ? "font-medium text-ink" : ""}>
                          {v === null ? "Yes, size unknown" : size(v, UNIT[t])}
                        </span>{" "}
                        {key !== "expert" && (ok ? <Badge tone="good">match</Badge> : <Badge tone="warn">off</Badge>)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-muted">Match = {TOLERANCE_TEXT}.</p>
      </Card>

      <div className="space-y-4">
        <Card className="grid grid-cols-2 gap-4 p-5">
          <Stat label="Our model" value={`${score("ours")} / 4`} sub="components match" />
          <Stat label="Rule of thumb" value={`${score("baseline")} / 4`} sub="components match" />
        </Card>
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-ink">What the planner knew</h3>
          <dl className="mt-2 space-y-1.5 text-sm">
            {shown.map((f) => {
              const v = row.inputs[f];
              const copy = FIELD_COPY[f];
              return (
                <div key={f} className="flex justify-between gap-3">
                  <dt className="text-muted">{copy?.label ?? f}</dt>
                  <dd className="text-right text-ink tabular-nums">
                    {v === null ? <span className="text-muted">unknown</span>
                      : typeof v === "boolean" ? (v ? "yes" : "no")
                      : typeof v === "number" ? `${num(v * (copy?.scale ?? 1), 2)} ${copy?.unit ?? ""}`
                      : (CHOICE_LABEL[v] ?? v)}
                  </dd>
                </div>
              );
            })}
          </dl>
          <Button className="mt-4 w-full" onClick={() => onLoad(row)}>
            Load into designer
          </Button>
          <p className="mt-2 text-xs text-muted">
            Opens the live model, which was trained on all projects. The table above is the honest held-out result.
          </p>
        </Card>
      </div>
    </div>
  );
}

export function EvalTab() {
  const { data: report, error } = useLoad(api.evaluation);
  if (error) return <ErrorNote error={error} />;
  if (!report) return <div className="h-96 animate-pulse rounded-2xl bg-sand" />;
  if (!("model" in report)) return <p className="text-sm">No evaluation yet. Run <code>python -m reonic eval</code>.</p>;
  return <EvalReport r={report} />;
}

function EvalReport({ r }: { r: Evaluation }) {
  const rows = [
    { key: "include_accuracy", label: "Right include / leave out" },
    { key: "within_tolerance", label: "Matches the expert" },
  ] as const;
  return (
    <div className="space-y-6">
      <Card className="p-6">
        <p className="text-sm text-muted">Whole design matches the expert, on {r.n_test} projects the model never saw</p>
        <div className="mt-2 flex flex-wrap items-end gap-x-10 gap-y-3">
          <div>
            <div className="text-5xl font-semibold tracking-tight text-ink tabular-nums">
              {pct(r.model.whole_design_within_tolerance)}
            </div>
            <div className="text-sm text-body">our model</div>
          </div>
          <div>
            <div className="text-3xl font-semibold tracking-tight text-muted tabular-nums">
              {pct(r.baseline.whole_design_within_tolerance)}
            </div>
            <div className="text-sm text-body">rule of thumb</div>
          </div>
        </div>
        <p className="mt-4 max-w-2xl text-sm">
          All four components have to be right at once: {TOLERANCE_TEXT}. Trained on {r.n_train.toLocaleString("en-GB")} projects,{" "}
          {r.split} split. <span className="font-serif italic">One wrong component fails the whole design.</span>
        </p>
      </Card>

      <Card className="overflow-x-auto p-5">
        <table className="w-full min-w-[560px] text-sm">
          <caption className="mb-3 text-left text-sm font-semibold text-ink">Per component</caption>
          <thead>
            <tr className="text-left text-xs text-muted">
              <th scope="col" className="py-2 font-medium">Component</th>
              <th scope="col" className="py-2 font-medium">Experts include it</th>
              {rows.map((x) => (
                <th key={x.key} scope="col" className="py-2 font-medium">
                  {x.label} <span className="font-normal">(model vs rule)</span>
                </th>
              ))}
              <th scope="col" className="py-2 font-medium">Avg size error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {TARGETS.map((t) => (
              <tr key={t}>
                <th scope="row" className="py-2.5 text-left font-medium text-ink">
                  {LABEL[t]}
                </th>
                <td className="py-2.5 tabular-nums">{pct(r.model[t].expert_include_rate)}</td>
                {rows.map((x) => (
                  <td key={x.key} className="py-2.5 tabular-nums">
                    <span className="font-medium text-ink">{pct(r.model[t][x.key])}</span>{" "}
                    <span className="text-muted">vs {pct(r.baseline[t][x.key])}</span>
                  </td>
                ))}
                <td className="py-2.5 tabular-nums">
                  {r.model[t].size_mae === null ? "n/a" : `${num(r.model[t].size_mae)} ${UNIT[t]}`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {Object.keys(r.by_installer ?? {}).length > 0 && (
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-ink">Whole design matches, per installer</h3>
          <ul className="mt-3 space-y-2">
            {Object.entries(r.by_installer).map(([id, v]) => (
              <li key={id} className="grid grid-cols-[110px_1fr_48px] items-center gap-3 text-sm">
                <span className="font-mono text-xs text-muted">{id.slice(0, 8)}</span>
                <span className="h-2 overflow-hidden rounded-full bg-sand" aria-hidden>
                  <span className="block h-full rounded-full bg-emerald-500" style={{ width: `${v * 100}%` }} />
                </span>
                <span className="text-right tabular-nums">{pct(v)}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}

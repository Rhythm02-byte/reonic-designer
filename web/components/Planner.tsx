"use client";
import { useEffect, useState } from "react";
import { api, TARGETS, type Design, type Evaluation, type Field, type HoldoutRow, type Inputs, type InputValue, type Meta, type Target } from "@/lib/api";
import { CHOICE_LABEL, DEMO_INPUTS, defaultOptions, describe, encodeOffer, eur, FIELD_COPY, LABEL, pct, size, UNIT, years } from "@/lib/copy";
import { House } from "./House";
import { Badge, Button, Card, ErrorNote, Logo, PersonaChip, Segmented, Stat } from "./ui";

export default function Planner() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [inputs, setInputs] = useState<Inputs>(DEMO_INPUTS);
  const [source, setSource] = useState<string | null>(null);
  // The last good design stays on screen while the next one is computed.
  const [state, setState] = useState<{ key: string | null; design: Design | null; error: string | null }>({
    key: null, design: null, error: null,
  });

  useEffect(() => {
    api.meta().then(setMeta, (e: Error) => setMetaError(e.message));
  }, []);

  const key = JSON.stringify(inputs);
  useEffect(() => {
    let live = true;
    const id = setTimeout(() => {
      api.design(inputs).then(
        (design) => live && setState({ key, design, error: null }),
        (e: Error) => live && setState((s) => ({ ...s, key, error: e.message })),
      );
    }, 250);
    return () => {
      live = false;
      clearTimeout(id);
    };
  }, [inputs, key]);

  const { design } = state;
  const busy = state.key !== key;
  const setInput = (name: string, v: InputValue) => setInputs((p) => ({ ...p, [name]: v }));
  const load = (row: HoldoutRow) => {
    setInputs(row.inputs);
    setSource(row.project_id);
  };

  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-30 border-b border-zinc-200/70 bg-paper/85 backdrop-blur">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 sm:px-6">
          <Logo />
          <PersonaChip who="planner" />
          <div className="ml-auto flex items-center gap-3">
            <span aria-live="polite" className="text-xs text-muted">
              {busy ? "Updating…" : ""}
            </span>
            <ShareLink meta={meta} design={busy ? null : design} inputs={inputs} />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] space-y-4 px-4 py-6 sm:px-6">
        <ErrorNote error={metaError ?? state.error} />
        {meta?.synthetic && (
          <p className="text-sm text-amber-800">Running on synthetic data: numbers are for the demo only.</p>
        )}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="space-y-4">
            <section className="space-y-2" aria-labelledby="home">
              <h2 id="home" className="text-sm font-semibold text-ink">
                The home
              </h2>
              {meta ? (
                <Card className="space-y-3 p-4">
                  {Object.keys(FIELD_COPY)
                    .flatMap((name) => meta.fields.filter((f) => f.name === name))
                    .map((f) => (
                      <FieldInput key={f.name} field={f} value={inputs[f.name] ?? null} set={(v) => setInput(f.name, v)} />
                    ))}
                </Card>
              ) : (
                <Skeleton className="h-80" />
              )}
              <p className="text-xs text-muted">
                {source ? `Other inputs come from project ${source.slice(0, 8)}.` : "Other inputs use typical values."}
              </p>
            </section>
            <Reality onLoad={load} />
          </aside>

          <section className="min-w-0 space-y-4" aria-label="Design">
            <Card className="overflow-hidden">
              <div className="relative h-[320px] bg-gradient-to-b from-sand-2 to-sand sm:h-[520px]">
                {design && <House values={design.values} hasEv={inputs.has_ev === true} description={describe(design.values)} />}
                <p className="pointer-events-none absolute top-3 left-4 text-xs text-muted">Drag to turn</p>
              </div>
              {design ? <Economics design={design} /> : <Skeleton className="m-4 h-20" />}
            </Card>
            {design && (
              <Card className="p-4">
                <h2 className="text-sm font-semibold text-ink">Why this design</h2>
                <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm">
                  {design.explanation.slice(0, 2).map((l) => (
                    <li key={l}>{l}</li>
                  ))}
                </ul>
              </Card>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

function Skeleton({ className }: { className: string }) {
  return <div className={`animate-pulse rounded-2xl bg-sand ${className}`} />;
}

const inputClass =
  "w-full rounded-lg bg-white px-2.5 py-1.5 text-sm text-ink ring-1 ring-zinc-200 placeholder:text-zinc-400 focus:ring-2 focus:ring-emerald-500 focus:outline-none";

function FieldInput({ field, value, set }: { field: Field; value: InputValue; set: (v: InputValue) => void }) {
  const copy = FIELD_COPY[field.name];
  const id = `field-${field.name}`;
  if (field.kind === "bool") {
    return (
      <div className="space-y-1">
        <div className="text-sm text-ink" aria-hidden>
          {copy.label}
        </div>
        <Segmented
          name={id}
          label={copy.label}
          value={value === true ? "yes" : value === false ? "no" : ""}
          options={[
            { value: "yes", label: "Yes" },
            { value: "no", label: "No" },
          ]}
          onChange={(v) => set(v === "yes")}
        />
      </div>
    );
  }
  if (field.kind === "choice") {
    return (
      <div className="space-y-1">
        <label htmlFor={id} className="text-sm text-ink">
          {copy.label}
        </label>
        {/* "Unknown" stays: a real project can leave this empty. */}
        <select id={id} className={inputClass} value={typeof value === "string" ? value : ""} onChange={(e) => set(e.target.value || null)}>
          <option value="">Unknown</option>
          {field.choices.map((c) => (
            <option key={c} value={c}>
              {CHOICE_LABEL[c] ?? c}
            </option>
          ))}
        </select>
      </div>
    );
  }
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="text-sm text-ink">
        {copy.label}
      </label>
      <div className="flex items-center gap-2">
        <input
          id={id}
          type="number"
          inputMode="decimal"
          min={0}
          step={copy.step ?? "any"}
          placeholder="Unknown"
          className={inputClass}
          value={typeof value === "number" ? value : ""}
          onChange={(e) => {
            if (e.target.value === "") set(null);
            else if (Number.isFinite(e.target.valueAsNumber)) set(e.target.valueAsNumber);
          }}
        />
        {copy.unit && <span className="w-14 shrink-0 text-xs text-muted">{copy.unit}</span>}
      </div>
    </div>
  );
}

function Economics({ design }: { design: Design }) {
  const e = design.economics;
  return (
    <div className="border-t border-zinc-100 p-4">
      <div className="grid grid-cols-3 gap-4">
        <Stat label="Investment" value={eur(e.cost_eur)} />
        <Stat label="Savings per year" value={e.savings_eur === null ? "n/a" : eur(e.savings_eur)} />
        <Stat label="Payback" value={years(e.payback_years)} sub="PV + battery" />
      </div>
      <p className="mt-3 text-xs text-muted">
        Rough assumptions: list prices, today&apos;s electricity price, a simple yield model. Heat pump fuel savings are not
        included. {e.savings_eur === null && "Savings need the annual electricity use."}
      </p>
    </div>
  );
}

// -- held-out projects (reports/test_predictions.csv) and the evaluation report (reports/eval.json) --------
// Same as src/reonic/evaluate.py TOLERANCE: relative size error that still counts as "matches the expert".
const TOLERANCE: Record<Target, number> = { pv_kwp: 0.2, battery_kwh: 0.25, heat_pump_kw: 0.25, wallbox_kw: Infinity };

/** Mirrors evaluate.metrics: both agree on include/exclude, and the size is within tolerance when known. */
function matches(t: Target, ours: number, expert: number | null) {
  if (expert === null) return ours > 0; // offered, size unknown
  if (expert === 0) return ours === 0;
  return ours > 0 && Math.abs(ours - expert) / expert <= TOLERANCE[t];
}

function Reality({ onLoad }: { onLoad: (row: HoldoutRow) => void }) {
  const [report, setReport] = useState<Evaluation | null>(null);
  const [rows, setRows] = useState<HoldoutRow[] | null>(null);
  const [i, setI] = useState(-1);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.evaluation().then(setReport, (e: Error) => setError(e.message));
    api.holdout().then((r) => setRows(r.rows), (e: Error) => setError(e.message));
  }, []);

  const row = rows && i >= 0 ? rows[i] : null;
  const next = () => {
    if (!rows?.length) return;
    const k = (i + 1) % rows.length;
    setI(k);
    onLoad(rows[k]);
  };

  return (
    <Card className="space-y-3 p-4">
      <h2 className="text-sm font-semibold text-ink">Checked against reality</h2>
      <ErrorNote error={error} />
      {report === null ? (
        !error && <div className="h-14 animate-pulse rounded-lg bg-sand" />
      ) : "model" in report ? (
        <div>
          <p className="text-sm">
            <span className="text-2xl font-semibold tracking-tight text-ink tabular-nums">
              {pct(report.model.whole_design_within_tolerance)}
            </span>{" "}
            of {report.n_test} projects the model never saw get the whole design right. A rule of thumb gets{" "}
            {pct(report.baseline.whole_design_within_tolerance)}.
          </p>
          <p className="mt-1 text-xs text-muted">
            Right = PV within 20 %, battery and heat pump within 25 %, wallbox included or not, all at once.
          </p>
        </div>
      ) : (
        <p className="text-sm">
          No evaluation yet. Run <code>python -m reonic eval</code>.
        </p>
      )}

      <Button variant="secondary" className="w-full" onClick={next} disabled={!rows?.length}>
        {row ? "Next real project" : "Try a real project"}
      </Button>
      {row && (
        <div>
          <table className="w-full text-sm">
            <caption className="sr-only">The expert&apos;s design for this project compared with our model</caption>
            <thead>
              <tr className="text-left text-xs text-muted">
                <th scope="col" className="py-1 font-mono font-normal">
                  {row.project_id.slice(0, 8)}
                </th>
                <th scope="col" className="py-1 font-medium">Expert</th>
                <th scope="col" className="py-1 font-medium">Ours</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {TARGETS.map((t) => (
                <tr key={t}>
                  <th scope="row" className="py-1.5 text-left font-medium text-ink">
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
          <p className="mt-2 text-xs text-muted">
            &ldquo;Ours&rdquo; never saw this project. The house shows the live model, which was trained on all projects.
          </p>
        </div>
      )}
    </Card>
  );
}

// -- share with the homeowner ------------------------------------------------------------------------------
// The homeowner may resize the battery and the wallbox (docs/specs/homeowner-view.md); the rest stays as recommended.
const SHARE: Target[] = ["battery_kwh", "wallbox_kw"];

function ShareLink({ meta, design, inputs }: { meta: Meta | null; design: Design | null; inputs: Inputs }) {
  if (!meta || !design) return <Button disabled>Share with customer</Button>;
  const rec = design.values;
  const options = Object.fromEntries(
    meta.targets.map(({ name, catalog }) => [name, SHARE.includes(name) ? defaultOptions(name, rec[name], catalog) : [rec[name]]]),
  ) as Record<Target, number[]>;
  return (
    // The link carries this home's data in its hash: send it only to this customer.
    <a
      href={`/offer#${encodeOffer({ v: 1, inputs, recommended: rec, options })}`}
      target="_blank"
      rel="noopener"
      className="inline-flex items-center gap-1.5 rounded-full bg-ink px-4 py-1.5 text-sm font-medium text-paper hover:bg-ink/85 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500"
    >
      Share with customer <span aria-hidden>↗</span>
      <span className="sr-only">(opens the homeowner view in a new tab)</span>
    </a>
  );
}

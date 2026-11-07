"use client";
import { useEffect, useMemo, useState } from "react";
import { api, TARGETS, type Design, type Evaluation, type Field, type HoldoutRow, type Inputs, type InputValue, type Meta, type Target } from "@/lib/api";
import { CHOICE_LABEL, DEMO_INPUTS, defaultOptions, describe, encodeOffer, eur, FIELD_COPY, LABEL, pct, size, UNIT, years } from "@/lib/copy";
import { House } from "./House";
import { Badge, Button, Card, CheckList, ErrorNote, Footer, Header, Icon, type IconName, Logo, PersonaChip, pill, pillLook, Segmented, Stat } from "./ui";

const WIDTH = "max-w-[1500px]";

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

  // Without an electric car the distance means nothing; sent anyway, the model reads it as one and adds a wallbox.
  // The value stays in state so switching back to "Yes" restores it.
  const sent = useMemo(() => (inputs.has_ev === false ? { ...inputs, ev_km_per_year: null } : inputs), [inputs]);
  const key = JSON.stringify(sent);
  useEffect(() => {
    let live = true;
    const id = setTimeout(() => {
      api.design(sent).then(
        (design) => live && setState({ key, design, error: null }),
        (e: Error) => live && setState((s) => ({ ...s, key, error: e.message })),
      );
    }, 250);
    return () => {
      live = false;
      clearTimeout(id);
    };
  }, [sent, key]);

  const { design } = state;
  const busy = state.key !== key;
  const setInput = (name: string, v: InputValue) => setInputs((p) => ({ ...p, [name]: v }));
  const load = (row: HoldoutRow) => {
    setInputs(row.inputs);
    setSource(row.project_id);
  };

  return (
    <div className="flex min-h-dvh flex-col">
      <Header width={WIDTH}>
        <Logo />
        <PersonaChip who="planner" />
        <div className="ml-auto flex items-center gap-3">
          <span aria-live="polite" className="text-xs text-muted">
            {busy ? "Updating…" : ""}
          </span>
          <ShareLink meta={meta} design={busy ? null : design} inputs={sent} />
        </div>
      </Header>

      <main className={`mx-auto w-full flex-1 space-y-6 px-4 py-8 sm:px-6 ${WIDTH}`}>
        <div className="max-w-3xl space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            Plan the system <span className="text-reonic">an expert would</span>
          </h1>
          <p className="max-w-[65ch] text-base">
            Describe the home. The model proposes solar, battery, heat pump and wallbox sizes the way experienced Reonic
            planners did on real projects.
          </p>
        </div>
        <ErrorNote error={metaError ?? state.error} />
        {meta?.synthetic && (
          <p className="text-sm text-amber-800">Running on synthetic data: numbers are for the demo only.</p>
        )}

        {/* Mobile order: inputs, house, proof. From lg the house spans both rows of the right column. */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[320px_minmax(0,1fr)] lg:grid-rows-[auto_1fr]">
          <section className="space-y-2 lg:col-start-1" aria-labelledby="home">
            <h2 id="home" className="text-sm font-semibold text-ink">
              The home
            </h2>
            {meta ? (
              <Card className="space-y-3 p-4">
                {Object.keys(FIELD_COPY)
                  .flatMap((name) => meta.fields.filter((f) => f.name === name))
                  .filter((f) => f.name !== "ev_km_per_year" || inputs.has_ev !== false)
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
          <section className="min-w-0 space-y-4 lg:col-start-2 lg:row-span-2 lg:row-start-1" aria-label="Design">
            <Card className="overflow-hidden">
              <div className="relative h-[320px] bg-gradient-to-b from-sand-2 to-sand sm:h-[520px]">
                {design && <House values={design.values} hasEv={inputs.has_ev === true} description={describe(design.values)} />}
                <p className="pointer-events-none absolute top-3 left-4 text-xs text-quiet">Drag to turn</p>
              </div>
              {design ? <Economics design={design} /> : <Skeleton className="m-4 h-20" />}
            </Card>
            {design && (
              <Card className="p-4 text-sm">
                <h2 className="mb-3 text-sm font-semibold text-ink">Why this design</h2>
                <CheckList items={design.explanation.slice(0, 2)} />
              </Card>
            )}
          </section>
          <div className="lg:col-start-1 lg:self-start">
            <Reality onLoad={load} />
          </div>
        </div>
      </main>
      <Footer width={WIDTH}>
        Built for the Reonic challenge at thinc! München 2026. Every size is a proposal for a planner to check, not a quote.
      </Footer>
    </div>
  );
}

function Skeleton({ className }: { className: string }) {
  return <div className={`animate-pulse rounded-2xl bg-sand ${className}`} />;
}

const inputClass =
  "w-full rounded-lg bg-white px-2.5 py-1.5 text-sm text-ink ring-1 ring-zinc-200 placeholder:text-zinc-400 focus:ring-2 focus:ring-blue-600 focus:outline-none";

const FIELD_ICON: Record<string, IconName> = {
  annual_consumption_kwh: "zap", household_size: "users", heating_type: "flame", has_ev: "car", ev_km_per_year: "route",
};

function FieldLabel({ name, htmlFor, children }: { name: string; htmlFor?: string; children: string }) {
  const Tag = htmlFor ? "label" : "div";
  return (
    <Tag htmlFor={htmlFor} aria-hidden={htmlFor ? undefined : true} className="flex items-center gap-2 text-sm text-ink">
      {FIELD_ICON[name] && <Icon name={FIELD_ICON[name]} />}
      {children}
    </Tag>
  );
}

function FieldInput({ field, value, set }: { field: Field; value: InputValue; set: (v: InputValue) => void }) {
  const copy = FIELD_COPY[field.name];
  const id = `field-${field.name}`;
  if (field.kind === "bool") {
    return (
      <div className="space-y-1">
        <FieldLabel name={field.name}>{copy.label}</FieldLabel>
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
        <FieldLabel name={field.name} htmlFor={id}>{copy.label}</FieldLabel>
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
      <FieldLabel name={field.name} htmlFor={id}>{copy.label}</FieldLabel>
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
    <div className="border-t border-zinc-200 p-4">
      <div className="grid grid-cols-3 gap-4">
        <Stat icon="wallet" label="Investment" value={eur(e.cost_eur)} />
        <Stat icon="trend" label="Savings per year" value={e.savings_eur === null ? "n/a" : eur(e.savings_eur)} />
        <Stat icon="clock" label="Payback" value={years(e.payback_years)} sub="PV + battery" />
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

// The per-part bars; the heat pump is left out because nearly every project gets the same answer (99 %).
const BARS: { label: string; get: (w: Evaluation["model"]) => number }[] = [
  { label: "Whole design", get: (w) => w.whole_design_within_tolerance },
  { label: "Solar", get: (w) => w.pv_kwp.within_tolerance },
  { label: "Battery", get: (w) => w.battery_kwh.within_tolerance },
  { label: "Wallbox", get: (w) => w.wallbox_kw.within_tolerance },
];

function Bars({ report }: { report: Evaluation }) {
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
                  {pct(b)} <span className="sr-only">for the rule of thumb</span>
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
  const ready = report !== null && "model" in report;

  return (
    // The one loud element of the page: ink on the gradient (white fails AA there), a dark panel for the evidence.
    <section aria-labelledby="reality" className="bg-reonic space-y-3 rounded-2xl p-4 text-ink">
      <h2 id="reality" className="text-xs font-semibold tracking-wide uppercase">Checked against reality</h2>
      <ErrorNote error={error} />
      {report === null ? (
        !error && <div className="h-14 animate-pulse rounded-xl bg-ink/10" />
      ) : ready ? (
        <p className="text-lg leading-snug font-semibold tracking-tight">
          {pct(report.model.whole_design_within_tolerance)} of {report.n_test} projects the model never saw get the whole
          design right. A rule of thumb gets {pct(report.baseline.whole_design_within_tolerance)}.
        </p>
      ) : (
        <p className="text-sm font-semibold">
          No evaluation yet. Run <code>python -m reonic eval</code>.
        </p>
      )}

      <div className="space-y-4 rounded-xl bg-ink p-4 text-sm text-zinc-300">
        {ready && (
          <>
            <Bars report={report} />
            <p className="text-xs">
              Right = solar within 20 %, battery and heat pump within 25 %, wallbox included or not.
              {report.baseline.wallbox_kw.within_tolerance > report.model.wallbox_kw.within_tolerance &&
                " On the wallbox alone the rule of thumb is still better."}
            </p>
          </>
        )}
        <Button variant="secondary" className="w-full" onClick={next} disabled={!rows?.length}>
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
              &ldquo;Ours&rdquo; never saw this project. The house shows the live model, which was trained on all projects.
            </p>
          </div>
        )}
      </div>
    </section>
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
      className={`${pill} ${pillLook.primary}`}
    >
      Share with customer <Icon name="arrow" className="size-4" />
      <span className="sr-only">(opens the homeowner view in a new tab)</span>
    </a>
  );
}

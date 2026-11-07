"use client";
import { useEffect, useRef, useState } from "react";
import { api, TARGETS, type Design, type Field, type HoldoutRow, type Inputs, type InputValue, type Meta, type Target, type Values } from "@/lib/api";
import {
  CHOICE_LABEL, confidence, DEMO_INPUTS, defaultOptions, describe, encodeOffer, eur, FIELD_COPY, GROUPS, LABEL, num, pct,
  RULE_TARGET, signedEur, size, UNIT, years,
} from "@/lib/copy";
import { CompareTab, EvalTab } from "./Compare";
import { House } from "./House";
import { Badge, Button, Card, ErrorNote, Flags, Logo, PersonaChip, Segmented, Stat } from "./ui";

type Info = Meta["targets"][number];
const WITHOUT: Record<Target, string> = {
  pv_kwp: "Without solar", battery_kwh: "Without a battery", heat_pump_kw: "Without a heat pump", wallbox_kw: "Without a wallbox",
};
const VIEWS = [
  { value: "design", label: "Design" },
  { value: "compare", label: "Compare" },
  { value: "evaluation", label: "Evaluation" },
] as const;
type View = (typeof VIEWS)[number]["value"];

export default function Planner() {
  const [view, setView] = useState<View>("design");
  const [meta, setMeta] = useState<Meta | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [inputs, setInputs] = useState<Inputs>(DEMO_INPUTS);
  const [locked, setLocked] = useState<Partial<Values>>({});
  const [source, setSource] = useState<string | null>(null);
  const [selected, setSelected] = useState<Target | null>(null);
  const [sharing, setSharing] = useState(false);
  // The last good design stays on screen while the next one is computed.
  const [state, setState] = useState<{ key: string | null; design: Design | null; error: string | null }>({
    key: null, design: null, error: null,
  });

  useEffect(() => {
    api.meta().then(setMeta, (e: Error) => setMetaError(e.message));
  }, []);

  const key = JSON.stringify([inputs, locked]);
  useEffect(() => {
    let live = true;
    const id = setTimeout(() => {
      api.design(inputs, locked).then(
        (design) => live && setState({ key, design, error: null }),
        (e: Error) => live && setState((s) => ({ ...s, key, error: e.message })),
      );
    }, 250);
    return () => {
      live = false;
      clearTimeout(id);
    };
  }, [inputs, locked, key]);

  const { design } = state;
  const busy = state.key !== key;

  const setInput = (name: string, v: InputValue) => setInputs((p) => ({ ...p, [name]: v }));
  const setLock = (t: Target, v: number | undefined) =>
    setLocked((prev) => {
      const next = { ...prev };
      if (v === undefined) delete next[t];
      else next[t] = v;
      return next;
    });
  const select = (t: Target) => {
    setSelected(t);
    document.getElementById(`card-${t}`)?.scrollIntoView({ block: "nearest" });
  };
  const load = (row: HoldoutRow) => {
    setInputs(row.inputs);
    setLocked({});
    setSource(row.project_id);
    setView("design");
  };

  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-30 border-b border-zinc-200/70 bg-paper/85 backdrop-blur">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 sm:px-6">
          <Logo />
          <PersonaChip who="planner" />
          <div className="order-last w-full sm:order-none sm:ml-4 sm:w-80">
            <Segmented name="view" label="View" value={view} options={[...VIEWS]} onChange={setView} />
          </div>
          <div className="ml-auto flex items-center gap-3">
            <span aria-live="polite" className="text-xs text-muted">
              {busy && view === "design" ? "Updating…" : ""}
            </span>
            <Button onClick={() => setSharing(true)} disabled={!design || busy}>
              Share with customer
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] space-y-4 px-4 py-6 sm:px-6">
        <ErrorNote error={metaError ?? state.error} />
        {meta?.synthetic && (
          <p className="text-sm text-amber-800">Running on synthetic data: numbers are for the demo only.</p>
        )}

        {view === "design" && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[300px_minmax(0,1fr)] xl:grid-cols-[300px_minmax(0,1fr)_380px]">
            <aside className="space-y-3">
              <div className="flex items-baseline justify-between">
                <h2 className="text-sm font-semibold text-ink">The home</h2>
                <div className="flex gap-1">
                  <Button variant="ghost" className="px-2! text-xs" onClick={() => {
                      setInputs(DEMO_INPUTS);
                      setSource(null);
                    }}>
                    Example
                  </Button>
                  <Button
                    variant="ghost"
                    className="px-2! text-xs"
                    onClick={() => setInputs(Object.fromEntries(Object.keys(inputs).map((k) => [k, null])))}
                  >
                    Clear all
                  </Button>
                </div>
              </div>
              {source && (
                <p className="rounded-xl bg-blue-50 p-3 text-xs text-blue-900">
                  Loaded held-out project <span className="font-mono">{source.slice(0, 8)}</span>. The live model was trained on all
                  projects, this one included, so it can differ from the held-out result on the Compare tab.
                </p>
              )}
              <p className="text-xs text-muted">Leave a field empty when you don&apos;t know it. Nothing is guessed.</p>
              {meta ? <HomeForm fields={meta.fields} inputs={inputs} setInput={setInput} /> : <Skeleton className="h-96" />}
            </aside>

            <section className="min-w-0 space-y-4" aria-label="Design">
              <Card className="overflow-hidden">
                <div className="relative h-[320px] bg-gradient-to-b from-sand-2 to-sand sm:h-[460px]">
                  {design && (
                    <House
                      values={design.values}
                      hasEv={inputs.has_ev === true}
                      selected={selected}
                      onSelect={select}
                      description={describe(design.values)}
                    />
                  )}
                  <p className="pointer-events-none absolute top-3 left-4 text-xs text-muted">Drag to turn · click a component</p>
                </div>
                {design && <Economics design={design} />}
              </Card>
              {design && <Why design={design} />}
            </section>

            <section className="space-y-3 lg:col-span-2 xl:col-span-1" aria-label="Components">
              <h2 className="text-sm font-semibold text-ink">Components</h2>
              {design && meta ? (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-1">
                  {meta.targets.map((info) => (
                    <ComponentCard
                      key={info.name}
                      info={info}
                      design={design}
                      inputs={inputs}
                      lockedValue={locked[info.name]}
                      setLock={(v) => setLock(info.name, v)}
                      selected={selected === info.name}
                      onSelect={() => setSelected(info.name)}
                    />
                  ))}
                </div>
              ) : (
                <Skeleton className="h-96" />
              )}
            </section>
          </div>
        )}
        {view === "compare" && <CompareTab onLoad={load} />}
        {view === "evaluation" && <EvalTab />}
      </main>

      {sharing && design && meta && (
        <ShareDialog meta={meta} design={design} inputs={inputs} onClose={() => setSharing(false)} />
      )}
    </div>
  );
}

function Skeleton({ className }: { className: string }) {
  return <div className={`animate-pulse rounded-2xl bg-sand ${className}`} />;
}

// -- the home (left column) ------------------------------------------------------------------------
function HomeForm({ fields, inputs, setInput }: { fields: Field[]; inputs: Inputs; setInput: (n: string, v: InputValue) => void }) {
  return (
    <Card className="divide-y divide-zinc-100">
      {GROUPS.map((g) => {
        const group = fields.filter((f) => (FIELD_COPY[f.name]?.group ?? "Household") === g);
        return (
          group.length > 0 && (
            <fieldset key={g} className="space-y-3 p-4">
              <legend className="float-left mb-1 w-full text-xs font-medium tracking-wide text-muted uppercase">{g}</legend>
              {group.map((f) => (
                <FieldInput key={f.name} field={f} value={inputs[f.name] ?? null} set={(v) => setInput(f.name, v)} />
              ))}
            </fieldset>
          )
        );
      })}
    </Card>
  );
}

const inputClass =
  "w-full rounded-lg bg-white px-2.5 py-1.5 text-sm text-ink ring-1 ring-zinc-200 placeholder:text-zinc-400 focus:ring-2 focus:ring-emerald-500 focus:outline-none";

function FieldInput({ field, value, set }: { field: Field; value: InputValue; set: (v: InputValue) => void }) {
  const copy = FIELD_COPY[field.name] ?? { label: field.name, group: "Household" };
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
          value={value === null ? "unknown" : value ? "yes" : "no"}
          options={[
            { value: "yes", label: "Yes" },
            { value: "no", label: "No" },
            { value: "unknown", label: "Unknown" },
          ]}
          onChange={(v) => set(v === "unknown" ? null : v === "yes")}
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
  const scale = copy.scale ?? 1;
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
          value={typeof value === "number" ? +(value * scale).toFixed(6) : ""}
          onChange={(e) => {
            if (e.target.value === "") set(null);
            else if (Number.isFinite(e.target.valueAsNumber)) set(e.target.valueAsNumber / scale);
          }}
        />
        {copy.unit && <span className="w-14 shrink-0 text-xs text-muted">{copy.unit}</span>}
      </div>
    </div>
  );
}

// -- the design (centre column) ------------------------------------------------------------------------
function Economics({ design }: { design: Design }) {
  const e = design.economics;
  return (
    <div className="border-t border-zinc-100 p-4">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Investment" value={eur(e.cost_eur)} />
        <Stat label="Savings per year" value={e.savings_eur === null ? "n/a" : eur(e.savings_eur)} />
        <Stat label="Payback (PV + battery)" value={years(e.payback_years)} />
        <Stat label="Solar used at home" value={e.self_use_share === null ? "n/a" : pct(e.self_use_share)} />
      </div>
      <p className="mt-3 text-xs text-muted">
        Rough assumptions: list prices, today&apos;s electricity price, a simple yield model. Heat pump fuel savings are not
        included. {e.savings_eur === null && "Savings need the annual electricity use."}
      </p>
    </div>
  );
}

function Why({ design }: { design: Design }) {
  return (
    <div className="space-y-3">
      <Card className="p-4">
        <h2 className="text-sm font-semibold text-ink">
          Why this design <span className="font-serif font-normal text-muted italic">in the planner&apos;s words</span>
        </h2>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm">
          {design.explanation.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
        {design.rules_applied.length > 0 && (
          <ul className="mt-3 space-y-1 text-sm">
            {design.rules_applied.map((r) => (
              <li key={r} className="flex items-start gap-2">
                <Badge tone="neutral">Rule</Badge>
                {r}
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Flags flags={design.flags} />
    </div>
  );
}

// -- components (right column) --------------------------------------------------------------------------
function delta(a: number | null, b: number | null, fmt: (n: number) => string) {
  return a === null || b === null ? "n/a" : fmt(a - b);
}
const signedYears = (n: number) => `${n >= 0 ? "+" : "−"}${num(Math.abs(n), 1)} yrs`;

function ComponentCard({
  info, design, inputs, lockedValue, setLock, selected, onSelect,
}: {
  info: Info;
  design: Design;
  inputs: Inputs;
  lockedValue: number | undefined;
  setLock: (v: number | undefined) => void;
  selected: boolean;
  onSelect: () => void;
}) {
  const t = info.name;
  const v = design.values[t];
  const isLocked = lockedValue !== undefined;
  const conf = confidence(t, design.probability[t], v > 0, inputs);
  const rules = design.rules_applied.filter((r) => RULE_TARGET[r.slice(0, 3)] === t);
  const alt = design.alternatives[t];
  const e = design.economics;
  const listId = `catalog-${t}`;

  return (
    <Card id={`card-${t}`} className={`scroll-mt-24 p-4 transition-shadow ${selected ? "ring-2 ring-ink" : ""}`}>
      <div className="flex items-start justify-between gap-2">
        <button type="button" onClick={onSelect} className="text-left">
          <h3 className="text-sm font-medium text-body">{info.label}</h3>
          <div className="text-2xl font-semibold tracking-tight text-ink tabular-nums">{size(v, info.unit)}</div>
        </button>
        {isLocked ? <Badge tone="neutral">Set by you</Badge> : <Badge tone={conf.tone}>{conf.word}</Badge>}
      </div>
      <p className="mt-1 text-xs text-muted">
        {isLocked
          ? "Your override wins. The other components were re-planned around it."
          : `The model is ${pct(conf.sure)} sure ${v > 0 ? "to include it" : "to leave it out"}.`}
        {!isLocked && conf.unknown.length > 0 && ` Rated lower: ${conf.unknown.join(" and ")} unknown.`}
      </p>
      {rules.map((r) => (
        <p key={r} className="mt-2 flex items-start gap-2 text-xs">
          <Badge tone="neutral">Rule</Badge>
          {r}
        </p>
      ))}

      <div className="mt-3 flex items-center gap-2">
        <label htmlFor={`override-${t}`} className="text-xs text-muted">
          Override
        </label>
        <input
          id={`override-${t}`}
          type="number"
          inputMode="decimal"
          min={0}
          max={1000}
          step="any"
          list={listId}
          placeholder={num(v)}
          value={lockedValue ?? ""}
          onChange={(ev) => {
            if (ev.target.value === "") setLock(undefined);
            else if (Number.isFinite(ev.target.valueAsNumber)) setLock(ev.target.valueAsNumber);
          }}
          className={`${inputClass} w-24!`}
        />
        <span className="text-xs text-muted">{info.unit}</span>
        <datalist id={listId}>
          {[0, ...info.catalog].map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>
        {isLocked && (
          <Button variant="ghost" className="ml-auto px-2! text-xs" onClick={() => setLock(undefined)}>
            Back to model
          </Button>
        )}
      </div>

      {alt && (
        <div className="mt-3 rounded-xl bg-sand-2 p-3 ring-1 ring-zinc-100">
          <div className="flex items-center justify-between gap-2">
            <div className="text-sm text-ink">
              <span className="text-muted">Alternative: </span>
              {alt.value > 0 ? size(alt.value, info.unit) : WITHOUT[t].toLowerCase()}
            </div>
            <Button variant="secondary" className="px-3! py-1! text-xs" onClick={() => setLock(alt.value)}>
              Use this
            </Button>
          </div>
          <dl className="mt-2 grid grid-cols-3 gap-2 text-xs">
            <div>
              <dt className="text-muted">Cost</dt>
              <dd className="font-medium text-ink tabular-nums">{signedEur(alt.economics.cost_eur - e.cost_eur)}</dd>
            </div>
            <div>
              <dt className="text-muted">Savings/yr</dt>
              <dd className="font-medium text-ink tabular-nums">{delta(alt.economics.savings_eur, e.savings_eur, signedEur)}</dd>
            </div>
            <div>
              <dt className="text-muted">Payback</dt>
              <dd className="font-medium text-ink tabular-nums">{delta(alt.economics.payback_years, e.payback_years, signedYears)}</dd>
            </div>
          </dl>
          {TARGETS.filter((o) => o !== t && alt.values[o] !== design.values[o]).map((o) => (
            <p key={o} className="mt-1 text-xs text-body">
              Re-plans {LABEL[o]}: {num(design.values[o])} → {size(alt.values[o], UNIT[o])}
            </p>
          ))}
          {alt.flags
            .filter((f) => !design.flags.includes(f))
            .map((f) => (
              <p key={f} className="mt-1 text-xs text-amber-800">
                {f}
              </p>
            ))}
          <p className="mt-1 text-[11px] text-muted">Rough assumptions.</p>
        </div>
      )}
    </Card>
  );
}

// -- share with the homeowner -----------------------------------------------------------------------------
const SHARE_DEFAULT: Target[] = ["battery_kwh", "wallbox_kw"];

function ShareDialog({ meta, design, inputs, onClose }: { meta: Meta; design: Design; inputs: Inputs; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [copied, setCopied] = useState(false);
  const rec = design.values;
  const [options, setOptions] = useState<Record<Target, number[]>>(
    () =>
      Object.fromEntries(
        meta.targets.map(({ name, catalog }) => [
          name,
          SHARE_DEFAULT.includes(name) ? defaultOptions(name, rec[name], catalog) : [rec[name]],
        ]),
      ) as Record<Target, number[]>,
  );
  useEffect(() => ref.current?.showModal(), []);

  const url = `${window.location.origin}/offer#${encodeOffer({ v: 1, inputs, recommended: rec, options })}`;
  const toggle = (t: Target, x: number) =>
    setOptions((o) => ({ ...o, [t]: o[t].includes(x) ? o[t].filter((y) => y !== x) : [...o[t], x].sort((a, b) => a - b) }));

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      aria-labelledby="share-title"
      className="m-auto w-[min(640px,calc(100%-2rem))] rounded-2xl bg-paper p-0 text-body shadow-xl ring-1 ring-zinc-200 backdrop:bg-ink/30"
    >
      <div className="space-y-4 p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="share-title" className="text-lg font-semibold text-ink">
              Share with the customer
            </h2>
            <p className="text-sm text-muted">
              Choose what the homeowner may change. Their home data stays fixed and they can&apos;t go outside these options.
            </p>
          </div>
          <Button variant="ghost" aria-label="Close" onClick={() => ref.current?.close()}>
            ✕
          </Button>
        </div>

        <div className="divide-y divide-zinc-100 rounded-xl bg-white ring-1 ring-zinc-200">
          {meta.targets.map(({ name: t, label, unit, catalog }) => {
            const open = options[t].length > 1;
            const choices = [...new Set([0, rec[t], ...catalog])].sort((a, b) => a - b);
            return (
              <div key={t} className="space-y-2 p-3">
                <label className="flex items-center justify-between gap-3 text-sm">
                  <span>
                    <span className="font-medium text-ink">{label}</span>{" "}
                    <span className="text-muted">recommended {size(rec[t], unit)}</span>
                  </span>
                  <span className="flex items-center gap-2 text-xs text-muted">
                    Homeowner may change
                    <input
                      type="checkbox"
                      className="size-4 accent-emerald-600"
                      checked={open}
                      onChange={() =>
                        setOptions((o) => ({ ...o, [t]: open ? [rec[t]] : defaultOptions(t, rec[t], catalog) }))
                      }
                    />
                  </span>
                </label>
                {open && (
                  <fieldset className="flex flex-wrap gap-1.5">
                    <legend className="sr-only">{label} options</legend>
                    {choices.map((c) => (
                      <label
                        key={c}
                        className="cursor-pointer rounded-full px-2.5 py-0.5 text-xs ring-1 ring-zinc-200 has-checked:bg-ink has-checked:text-paper has-checked:ring-ink has-disabled:cursor-default has-focus-visible:outline-2 has-focus-visible:outline-emerald-500"
                      >
                        <input
                          type="checkbox"
                          className="sr-only"
                          checked={options[t].includes(c)}
                          disabled={c === rec[t]}
                          onChange={() => toggle(t, c)}
                        />
                        {c > 0 ? `${num(c)} ${unit}` : "None"}
                      </label>
                    ))}
                  </fieldset>
                )}
              </div>
            );
          })}
        </div>

        <div className="space-y-2">
          <label htmlFor="share-url" className="text-xs text-muted">
            Link for the homeowner. It carries this home&apos;s data, so share it only with this customer.
          </label>
          <input id="share-url" readOnly value={url} onFocus={(e) => e.target.select()} className={`${inputClass} font-mono text-xs`} />
          <div className="flex flex-wrap justify-end gap-2">
            <Button
              variant="secondary"
              onClick={() => navigator.clipboard.writeText(url).then(() => setCopied(true), () => setCopied(false))}
            >
              {copied ? "Copied" : "Copy link"}
            </Button>
            <a
              href={url}
              target="_blank"
              rel="noopener"
              className="inline-flex items-center rounded-full bg-ink px-4 py-1.5 text-sm font-medium text-paper hover:bg-ink/85"
            >
              Open homeowner view ↗
            </a>
          </div>
        </div>
      </div>
    </dialog>
  );
}

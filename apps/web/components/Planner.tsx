"use client";
import Link from "next/link";
import { useEffect, useEffectEvent, useMemo, useRef, useState } from "react";
import { api, TARGETS, type Design, type Evaluation, type Field, type HoldoutRow, type HouseModel, type Inputs, type InputValue, type Meta, type Target, type Values } from "@/lib/api";
import { altLabel, CHOICE_LABEL, describe, eur, FIELD_COPY, FIELD_GROUPS, LABEL, NOT_SUPPLIED, num, type Offer, pct, size, UNIT, years } from "@/lib/copy";
import { type Customer, TEAM, update, useWorkspace, type Workspace } from "@/lib/workspace"; // ours:
import { House } from "./House";
import { RealHouse } from "./RealHouse";
import { locationKey } from "@/lib/real-house";
import { Location } from "./Location"; // ours:
import { AskNext } from "./AskNext"; import { PartRange } from "./PartRange"; import { PartsList } from "./PartsList"; import { Share } from "./Share"; import { Evidence } from "./Evidence"; import { isPitchPlan, type PitchPlan } from "@/lib/pitch"; // ours:
import { Badge, Button, Card, CheckDot, CheckList, ErrorNote, Footer, Header, Icon, type IconName, Logo, MinusDot, pill, pillLook, Segmented, Avatar, Stat, Checkbox } from "./ui";
import { Select } from "./Select";

const WIDTH = "max-w-[1500px]";

// What the planner is editing. It stays a draft, marked unsaved, until "Save" writes it to the customer.
type Draft = { inputs: Inputs; locked: Partial<Values> };
type Step = { id: string; draft: Draft; label: string; before: Values | null };
const NO_LOCKS: Partial<Values> = {}; // ours: fix (stable identity for the design effect)

// ours: restart the short highlight on the section a header link jumped to (CSS drops it for reduced motion)
function flash(id: string) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove("anchor-flash");
  void el.offsetWidth;
  el.classList.add("anchor-flash");
  el.addEventListener("animationend", () => el.classList.remove("anchor-flash"), { once: true });
}

export default function Planner() {
  const ws = useWorkspace();
  const [scope, setScope] = useState<"mine" | "team">("mine");
  // A held-out project opens as an unsaved preview so it never overwrites a customer.
  const [preview, setPreview] = useState<{ id: string; inputs: Inputs } | null>(null);
  const [query, setQuery] = useState("");
  const [meta, setMeta] = useState<Meta | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [history, setHistory] = useState<Step[]>([]);
  const [selected, setSelected] = useState<Target | null>(null);
  // Alternatives the planner has ticked on or off for the homeowner; unticked default: the ones without warnings.
  const [offered, setOffered] = useState<Partial<Record<Target, boolean>>>({});
  // The last good design stays on screen while the next one is computed.
  const [state, setState] = useState<{ id: string | null; key: string | null; design: Design | null; error: string | null }>({
    id: null, key: null, design: null, error: null, // ours: id = whose design this is
  });
  const [recommendation, setRecommendation] = useState<{ inputKey: string | null; values: Values | null }>({ inputKey: null, values: null });
  const recommendationRef = useRef(recommendation);

  useEffect(() => {
    api.meta().then(setMeta, (e: Error) => setMetaError(e.message));
  }, []);

  const customer = ws.customers.find((c) => c.id === ws.active) ?? ws.customers[0];
  // Faris: LoD2 cadastre house for the pinned address is the stylised view; the standard house is the fallback.
  const [houseModel, setHouseModel] = useState<{ key: string | null; model: HouseModel | null }>({ key: null, model: null });
  const houseKey = customer.location ? `${customer.location.lat},${customer.location.lng}` : null;
  useEffect(() => {
    let live = true;
    void Promise.resolve().then(() => {
      if (!houseKey || !customer.location) return;
      return api.house(customer.location.lat, customer.location.lng).then((model) => live && setHouseModel({ key: houseKey, model }), () => live && setHouseModel({ key: houseKey, model: null }));
    });
    return () => { live = false; };
  }, [houseKey, customer.location]);
  const modelUrl = !preview && houseModel.key === houseKey ? houseModel.model?.url : undefined;
  const id = preview?.id ?? customer.id;
  const saved: Draft = preview ? { inputs: preview.inputs, locked: NO_LOCKS } : { inputs: customer.inputs, locked: customer.locked ?? NO_LOCKS }; // ours: fix, a fresh {} each render re-ran the design effect forever
  const draft = drafts[id] ?? saved;
  const dirty = !preview && JSON.stringify(draft) !== JSON.stringify(saved);
  const { inputs, locked } = draft;
  const q = query.trim().toLowerCase();
  const list = ws.customers.filter((c) => (scope === "team" || c.owner === ws.me) && c.name.toLowerCase().includes(q));

  // Without an electric car the distance means nothing; sent anyway, the model reads it as one and adds a wallbox.
  // The value stays in state so switching back to "Yes" restores it.
  const sent = useMemo(() => (inputs.has_ev === false ? { ...inputs, ev_km_per_year: null } : inputs), [inputs]);
  const inputKey = JSON.stringify(sent);
  const key = JSON.stringify([sent, locked]);
  useEffect(() => {
    let live = true;
    const t = setTimeout(() => {
      api.design(sent, locked).then(
        (design) => {
          if (!live) return;
          setState({ id, key, design, error: null });
          if (Object.keys(locked).length === 0) {
            const next = { inputKey, values: design.values };
            recommendationRef.current = next;
            setRecommendation(next);
          } else if (recommendationRef.current.inputKey !== inputKey) {
            api.design(sent, NO_LOCKS).then((baseline) => {
              if (!live) return;
              const next = { inputKey, values: baseline.values };
              recommendationRef.current = next;
              setRecommendation(next);
            }).catch(() => {});
          }
        },
        (e: Error) => live && setState((s) => ({ id, key, design: s.id === id ? s.design : null, error: e.message })),
      );
    }, 250);
    return () => {
      live = false;
      clearTimeout(t);
    };
  }, [sent, locked, key, inputKey, id]);

  // ours: another customer's design (or error) must not flash while this one loads
  const design = state.id === id ? state.design : null;
  const error = state.id === id ? state.error : null;
  const busy = state.key !== key || state.id !== id;
  const editCustomer = (patch: Partial<Customer>) =>
    update((w) => ({ ...w, customers: w.customers.map((c) => (c.id === customer.id ? { ...c, ...patch } : c)) }));
  const edit = (label: string, next: Draft) => {
    setHistory((h) => [...h, { id, draft, label, before: design?.values ?? null }]);
    setDrafts((d) => ({ ...d, [id]: next }));
  };
  const steps = history.filter((h) => h.id === id);
  const last = steps.at(-1);
  const undo = () => {
    if (!last) return;
    setHistory((h) => h.filter((x) => x !== last));
    setDrafts((d) => ({ ...d, [id]: last.draft }));
  };
  const save = () => {
    editCustomer({ inputs, locked });
    setDrafts((d) => Object.fromEntries(Object.entries(d).filter(([k]) => k !== id)));
    setHistory((h) => h.filter((x) => x.id !== id));
  };
  const setInput = (name: string, v: InputValue) => {
    if (name === "roof_max_modules") editCustomer({ roofCapacityConfirmed: false });
    const was = inputs[name] ?? null;
    edit(`${FIELD_COPY[name]?.label ?? name}: ${show(name, was)} → ${show(name, v)}`, { inputs: { ...inputs, [name]: v }, locked });
  };
  const setSize = (t: Target, v: number | null) => {
    const rest = Object.fromEntries(Object.entries(locked).filter(([k]) => k !== t));
    const backToRecommendation = v === null || (recommendation.inputKey === inputKey && recommendation.values?.[t] === v);
    edit(backToRecommendation ? `${LABEL[t]} back to the recommendation` : `${LABEL[t]} set to ${size(v!, UNIT[t])}`, {
      inputs,
      locked: backToRecommendation ? rest : { ...rest, [t]: v! },
    });
  };
  // ours: pitch mode (iemko). /pitch drives this page from outside (same origin only). With `because` it is a
  // planner change (diff bar + undo); without, the draft is simply replaced, like opening a project.
  const onPitch = useEffectEvent((p: PitchPlan) => {
    const next = { inputs: p.inputs, locked: p.locked ?? {} };
    if (p.because) return edit(p.because, next);
    setHistory((h) => h.filter((x) => x.id !== id));
    setDrafts((d) => ({ ...d, [id]: next }));
  });
  useEffect(() => {
    const onMessage = (e: MessageEvent) => {
      if (e.origin === window.location.origin && isPitchPlan(e.data)) onPitch(e.data);
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);
  const open = (cid: string) => {
    setPreview(null);
    setSelected(null);
    setOffered({});
    update((w) => ({ ...w, active: cid }));
  };
  // ours: switching planner keeps "Mine" meaningful: if the open customer isn't theirs, open their first one
  const switchMe = (me: string) => {
    const mine = ws.customers.find((c) => c.owner === me);
    const move = !!mine && customer.owner !== me;
    if (move) {
      setPreview(null);
      setSelected(null);
      setOffered({});
    }
    update((w) => ({ ...w, me, active: move ? mine.id : w.active }));
  };
  const load = (row: HoldoutRow) => {
    setSelected(null);
    setOffered({});
    setPreview({ id: row.project_id, inputs: row.inputs });
  };

  const name = preview ? "Real project" : customer.name || "Unnamed customer";
  const offer: Offer | null =
    design && !busy && !error
      ? {
          v: 2,
          customer: name,
          planner: preview ? ws.me : customer.owner,
          inputs: sent,
          options: [
            { label: "Recommended", values: design.values },
            ...TARGETS.flatMap((t) => {
              const a = design.alternatives[t];
              return a?.validated && (offered[t] ?? a.flags.length === 0) ? [{ label: altLabel(t, a.value), values: a.values }] : [];
            }),
          ],
          ...(design.modules && design.values.pv_kwp > 0 && { moduleWp: Math.round((design.values.pv_kwp * 1000) / design.modules) }), // ours:
          economics: { savings_eur: design.economics.savings_eur, payback_years: design.economics.payback_years }, // ours:
          ...(!preview && customer.location && { location: { lat: customer.location.lat, lng: customer.location.lng } }), // ours: real 3D for the homeowner
          ...(modelUrl && { modelUrl }), // Faris: LoD2 house in the homeowner view
          ...(design.economics.solar_share_of_demand !== undefined && { economics: { savings_eur: design.economics.savings_eur, payback_years: design.economics.payback_years, solar_share_of_demand: design.economics.solar_share_of_demand } }),
        }
      : null;

  return (
    <div className="xl:grid xl:grid-cols-[248px_minmax(0,1fr)]">
      <Sidebar ws={ws} list={list} scope={scope} setScope={setScope} activeId={preview ? null : customer.id} onOpen={open} onSwitchMe={switchMe} query={query} setQuery={setQuery} />
      <div className="flex min-h-dvh min-w-0 flex-col">
        <Header width={WIDTH}>
          <span className="xl:hidden">
            <Logo product={false} />
          </span>
          {/* Below xl the sidebar is gone; a native select switches customers. */}
          <Select // ours: custom control
            aria-label="Customer"
            className="max-w-44 xl:hidden"
            value={preview ? "" : customer.id}
            onChange={(v) => v && open(v)}
            options={[...(preview ? [{ value: "", label: "Real project" }] : []), ...ws.customers.map((c) => ({ value: c.id, label: c.name }))]}
          />
          <nav aria-label="Project" className="hidden gap-1 text-sm md:flex">
            {[["design", "Design"], ["inputs", "Inputs"], ["evidence", "Evidence"]].map(([href, label]) => (
              <a key={href} href={`#${href}`} onClick={() => flash(href)} className={`${pill} ${pillLook.ghost}`}>
                {label}
              </a>
            ))}
          </nav>
          <div className="ml-auto flex flex-wrap items-center gap-2">
            <SaveState preview={!!preview} dirty={dirty} busy={busy} onSave={save} />
            <Share offer={offer} /> {/* ours: one share entry (QR + copy + open) replaces his preview/share chevron pair and our QR button */}
          </div>
        </Header>

        <main className={`mx-auto w-full flex-1 space-y-6 px-4 py-6 sm:px-6 ${WIDTH}`}>
          <div className="space-y-1">
            <h1 className="sr-only">Design for {name}</h1>
            <p className="text-xs text-quiet">
              {preview ? `Real project ${preview.id.slice(0, 8)} · preview, not saved` : `Customer of ${customer.owner}`}
            </p>
            {preview ? (
              <p className="text-3xl font-semibold tracking-tight text-ink">Real project</p>
            ) : (
              <input
                aria-label="Customer name"
                value={customer.name}
                onChange={(e) => editCustomer({ name: e.target.value })}
                className="-mx-1.5 w-full max-w-xl rounded-lg bg-transparent px-1.5 text-3xl font-semibold tracking-tight text-ink hover:bg-sand focus-visible:outline-2 focus-visible:outline-blue-600"
              />
            )}
            {!preview && customer.location?.address && (
              <p className="flex items-center gap-1.5 text-sm text-quiet">
                <Icon name="pin" className="size-3.5 text-blue-600" />
                {customer.location.address}
              </p>
            )}
            <p className="max-w-[65ch] text-sm">
              A first system design from the home&apos;s data, sized the way installers planned similar real projects.
              Check it, adjust it, then share the options with the homeowner.
            </p>
          </div>
          <ErrorNote error={metaError ?? error} />
          {error && design && <p className="text-sm text-amber-900">The last successful proposal is shown for reference. It has not updated to the current inputs and cannot be shared.</p>}
          {(meta?.synthetic || design?.source === "demo") && (
            <p className="text-sm text-amber-800">Running on synthetic data: numbers are for the demo only.</p>
          )}

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[340px_minmax(0,1fr)]">
            <div className="space-y-6">
              <section id="inputs" className="scroll-mt-20 space-y-2 rounded-2xl" aria-labelledby="inputs-h">
                <h2 id="inputs-h" className="text-sm font-semibold text-ink">
                  Project inputs
                </h2>
                {meta ? (
                  <InputsPanel meta={meta} inputs={inputs} saved={saved.inputs} set={setInput} />
                ) : (
                  !metaError && <Skeleton className="h-80" />
                )}
                <p className="text-xs text-muted">Empty fields are unknown; the model does not guess them.</p>
              </section>
              <AskNext design={design} set={setInput} /> {/* ours: */}
              {!preview && <Location key={customer.id} value={customer.location ?? null} onChange={(location) => {
                const changed = customer.location && (!location || locationKey(customer.location.lat, customer.location.lng) !== locationKey(location.lat, location.lng));
                if (changed && customer.roofCapacityConfirmed) setInput("roof_max_modules", null);
                editCustomer({ location: location ?? undefined, ...(changed ? { realHouse: undefined, roofLayout: undefined, roofCapacityConfirmed: false } : {}) });
              }} />}
              <div id="evidence" className="scroll-mt-20 rounded-2xl">
                <Evidence onLoad={load} /> {/* ours: replaces his <Reality onLoad={load} /> (compares with the installer's usual design) */}
              </div>
            </div>

            <section id="design" className="min-w-0 scroll-mt-20 space-y-4 rounded-2xl" aria-labelledby="design-h">
              <h2 id="design-h" className="sr-only">Design</h2>
              <Card className="overflow-hidden">
                <RealHouse
                  key={`${id}-${customer.location ? locationKey(customer.location.lat, customer.location.lng) : "none"}`}
                  location={preview ? null : customer.location ?? null}
                  asset={preview ? undefined : customer.realHouse}
                  layout={preview ? undefined : customer.roofLayout}
                  proposedPanels={design?.modules ?? 0}
                  existingPv={Number(inputs.existing_pv_kwp ?? 0) > 0}
                  onAsset={(realHouse) => editCustomer({ realHouse })}
                  onLayout={(roofLayout) => {
                    if (customer.roofCapacityConfirmed) setInput("roof_max_modules", null);
                    editCustomer({ roofLayout, roofCapacityConfirmed: false });
                  }}
                  onCapacity={(n) => { setInput("roof_max_modules", n); editCustomer({ roofCapacityConfirmed: true }); }}
                  fallback={design ? (
                    <House
                      values={design.values}
                      modules={design.modules} // ours:
                      hasEv={inputs.has_ev === true}
                      existing={existingOf(inputs)}
                      description={describe(design.values, design.modules)} // ours: modules
                      modelUrl={modelUrl}
                      selected={selected}
                      onSelect={setSelected}
                    />
                  ) : (
                    !error && <Skeleton className="h-full rounded-none" />
                  )}
                />
                {design && <Economics design={design} />}
              </Card>

              {last && design && (
                <Changed step={last} now={busy ? null : design.values} onUndo={undo} />
              )}

              <section aria-labelledby="proposed" className="space-y-2">
                <div className="flex items-baseline justify-between gap-3">
                  <h2 id="proposed" className="text-sm font-semibold text-ink">Proposed system</h2>
                  <p className="text-xs text-muted">kWp = solar peak power · kWh = storage · kW = power</p>
                </div>
                {design ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {TARGETS.map((t) => (
                      <SystemCard
                        key={t}
                        t={t}
                        design={design}
                        locked={locked[t]}
                        recommendation={recommendation.inputKey === inputKey ? recommendation.values?.[t] : undefined}
                        selected={selected === t}
                        onSelect={() => setSelected(selected === t ? null : t)}
                        onSet={(v) => setSize(t, v)}
                      />
                    ))}
                  </div>
                ) : (
                  !error && <Skeleton className="h-48" />
                )}
                {design && general(design.flags).length > 0 && (
                  <ul className="space-y-1 text-sm text-amber-800">
                    {general(design.flags).map((f) => (
                      <li key={f}>Needs review: {f}</li>
                    ))}
                  </ul>
                )}
              </section>

              {design && (
                <Card className="p-4 text-sm">
                  <h2 className="mb-3 text-sm font-semibold text-ink">How similar projects were planned</h2>
                  <CheckList items={design.explanation.map(plain).slice(0, 4)} />
                </Card>
              )}
              <PartsList parts={design?.parts} /> {/* ours: */}

              {design && (
                <OfferOptions design={design} offered={offered} setOffered={setOffered} />
              )}
            </section>
          </div>
        </main>
        <Footer width={WIDTH}>
          Built for the Reonic challenge at thinc! München 2026. Every size is a proposal for a planner to check, not a
          quote.
        </Footer>
      </div>
    </div>
  );
}

const existingOf = (i: Inputs) => ({
  pv_kwp: typeof i.existing_pv_kwp === "number" ? i.existing_pv_kwp : 0,
  battery_kwh: typeof i.existing_battery_kwh === "number" ? i.existing_battery_kwh : 0,
  wallbox: i.has_existing_wallbox === true,
});

function show(name: string, v: InputValue) {
  if (v === null || v === "") return "unknown";
  if (typeof v === "boolean") return v ? "yes" : "no";
  if (typeof v === "string") return CHOICE_LABEL[v] ?? v;
  const c = FIELD_COPY[name];
  return `${num(v * (c?.scale ?? 1), 2)}${c?.unit ? ` ${c.unit}` : ""}`;
}

// The API words its explanation for engineers; the planner screen drops the model's certainty, which reads as a promise.
const plain = (line: string) => line.replace(/ \(model \d+% sure to include\)/, "").replace(/ \(set by planner\)/, " (your setting)");

// A warning names the part it is about; those land on the part's card, the rest are listed under the cards.
const PART_WORDS: Record<Target, RegExp> = { pv_kwp: /\b(pv|solar)\b/i, battery_kwh: /battery/i, heat_pump_kw: /heat pump/i, wallbox_kw: /wallbox/i };
const flagsFor = (t: Target, flags: string[]) => flags.filter((f) => PART_WORDS[t].test(f));
const general = (flags: string[]) => flags.filter((f) => !TARGETS.some((t) => PART_WORDS[t].test(f)));

function SaveState({ preview, dirty, busy, onSave }: { preview: boolean; dirty: boolean; busy: boolean; onSave: () => void }) {
  return (
    <>
      <span aria-live="polite" className="text-xs text-quiet">
        {busy ? "Updating design…" : preview ? "Preview, not saved" : dirty ? "Unsaved changes" : "All changes saved"}
      </span>
      {dirty && (
        <Button variant="secondary" onClick={onSave}>
          Save
        </Button>
      )}
    </>
  );
}

function Changed({ step, now, onUndo }: { step: Step; now: Values | null; onUndo: () => void }) {
  const diff = now && step.before ? TARGETS.filter((t) => now[t] !== step.before![t]) : [];
  return (
    <div role="status" className="fade-in flex flex-wrap items-start gap-x-4 gap-y-2 rounded-2xl border border-zinc-200 bg-sand-2 p-4 text-sm">
      <div className="min-w-0 flex-1 space-y-1">
        <p className="font-medium text-ink">What changed? {step.label}</p>
        <p>
          {now === null
            ? "Updating the design…"
            : diff.length === 0
              ? "The proposed system stays the same."
              : diff.map((t) => `${LABEL[t]} ${sized(t, step.before![t])} → ${sized(t, now[t])}`).join(" · ")}
        </p>
      </div>
      <Button variant="secondary" onClick={onUndo}>
        Undo
      </Button>
    </div>
  );
}

const sized = (t: Target, v: number) => (v > 0 ? size(v, UNIT[t]) : "not included");

const STEP: Record<Target, number> = { pv_kwp: 0.45, battery_kwh: 0.5, heat_pump_kw: 1, wallbox_kw: 0.1 };

// Keep partial numeric typing local; reset it when Undo, a pitch step or a customer change supplies a new value.
// ours: review fix. A typed draft is only shown while the value it was typed against is still current; once it is
// committed (blur/Enter) it is dropped, so "Reset to recommendation" (1 -> back to 0) shows 0, not the stale "1".
const COMMITTED = Symbol("committed");
function useNumericDraft(value: number | null, scale = 1) {
  const text = value === null ? "" : String(+(value * scale).toFixed(6));
  const [draft, setDraft] = useState<{ source: number | null | typeof COMMITTED; scale: number; text: string }>({ source: value, scale, text });
  return [Object.is(draft.source, value) && draft.scale === scale ? draft.text : text,
    (next: string) => setDraft({ source: value, scale, text: next }),
    () => setDraft({ source: COMMITTED, scale, text: "" })] as const;
}

function SystemCard({ t, design, locked, recommendation, selected, onSelect, onSet }: {
  t: Target;
  design: Design;
  locked: number | undefined;
  recommendation: number | undefined;
  selected: boolean;
  onSelect: () => void;
  onSet: (v: number | null) => void;
}) {
  const v = design.values[t];
  const [sizeDraft, setSizeDraft, commitSizeDraft] = useNumericDraft(v);
  const p = design.probability[t];
  const edited = locked !== undefined && (recommendation === undefined || locked !== recommendation);
  const warnings = flagsFor(t, design.flags);
  // Similar homes split on this part: worth a planner's second look. Not shown as a number on purpose.
  const unsure = !edited && p > 0.3 && p < 0.7;
  const review = warnings.length > 0 || unsure;
  const id = `size-${t}`;
  return (
    <Card className={`space-y-3 p-4 ${selected ? "outline-2 outline-blue-600" : ""}`}>
      <div className="flex items-start justify-between gap-2">
        <button
          type="button"
          aria-pressed={selected}
          onClick={onSelect}
          className="flex items-center gap-2 rounded-md text-left font-medium text-ink focus-visible:outline-2 focus-visible:outline-blue-600"
        >
          {v > 0 ? <CheckDot /> : <MinusDot />}
          {LABEL[t]}
          <span className="sr-only">(show on the house)</span>
        </button>
        <div className="flex flex-wrap justify-end gap-1">
          <Status>{edited ? "Edited" : v > 0 ? "Recommended" : "Not included"}</Status>
          {edited && v === 0 && <Status>Not included</Status>}
          {review && <Status warn>Needs review</Status>}
        </div>
      </div>
      <p key={v} className="fade-in text-2xl font-semibold tracking-tight text-ink tabular-nums">{v > 0 ? `${num(v)} ${UNIT[t]}` : "Not included"}</p>
      {/* ours: review fix, the count comes from the engine (its module watts), not an assumed 450 W / 5 kWh product */}
      {t === "pv_kwp" && v > 0 && design.modules ? <p className="text-sm text-quiet">{design.modules}× solar module</p> : null}
      <PartRange t={t} design={design} /> {/* ours: */}
      <div className="flex items-center gap-2">
        <label htmlFor={id} className="text-xs whitespace-nowrap text-quiet">
          Your size
        </label>
        <input
          id={id}
          type="number"
          inputMode="decimal"
          min={0}
          step={STEP[t]}
          value={sizeDraft}
          onChange={(e) => setSizeDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") e.currentTarget.blur(); }}
          onBlur={() => {
            const next = Number(sizeDraft);
            if (sizeDraft !== "" && Number.isFinite(next) && next >= 0 && next !== v) onSet(next);
            commitSizeDraft();
          }}
          className={`${inputClass} w-24`}
        />
        <span className="text-xs text-muted">{UNIT[t]} · 0 = not included</span>
      </div>
      {edited && (
        <Button variant="ghost" className="-ml-2" onClick={() => onSet(null)}>
          Reset to recommendation
        </Button>
      )}
      {(selected || review) && (
        <div className="space-y-1 border-t border-zinc-200 pt-3 text-xs">
          {warnings.map((w) => (
            <p key={w} className="text-amber-800">{w}</p>
          ))}
          {unsure && <p className="text-amber-800">Similar homes were split on this part; check it with the customer.</p>}
          {selected && <p className="text-muted">{NOT_SUPPLIED[t]}: not supplied by the model.</p>}
        </div>
      )}
    </Card>
  );
}

function Status({ warn, children }: { warn?: boolean; children: string }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${warn ? "bg-amber-50 text-amber-900 ring-amber-300" : "bg-sand text-quiet ring-zinc-200"}`}>
      {children}
    </span>
  );
}

function OfferOptions({ design, offered, setOffered }: {
  design: Design;
  offered: Partial<Record<Target, boolean>>;
  setOffered: (o: Partial<Record<Target, boolean>>) => void;
}) {
  const alts = TARGETS.flatMap((t) => (design.alternatives[t] ? [[t, design.alternatives[t]!] as const] : []));
  return (
    <Card className="space-y-3 p-4 text-sm">
      <h2 className="text-sm font-semibold text-ink">Options for the homeowner</h2>
      <p className="text-xs text-muted">
        The homeowner sees your design as the recommendation and can compare only the setups ticked here.
      </p>
      <fieldset className="space-y-2">
        <legend className="sr-only">Alternatives to offer</legend>
        {alts.map(([t, a]) => (
          <label key={t} className="flex items-start gap-2">
            <Checkbox // ours: custom control
              className="mt-0.5"
              disabled={!a.validated}
              checked={a.validated && (offered[t] ?? a.flags.length === 0)}
              onChange={(e) => setOffered({ ...offered, [t]: e.target.checked })}
            />
            <span>
              <span className="text-ink">{altLabel(t, a.value)}</span>
              {a.flags.length > 0 && <span className="block text-xs text-amber-800">Needs review: {a.flags[0]}</span>}
            </span>
          </label>
        ))}
        {alts.length === 0 && <p className="text-xs text-quiet">No alternatives: every part is set by you.</p>}
      </fieldset>
    </Card>
  );
}

function Sidebar({ ws, list, scope, setScope, activeId, onOpen, onSwitchMe, query, setQuery }: {
  ws: Workspace;
  list: Customer[];
  scope: "mine" | "team";
  setScope: (s: "mine" | "team") => void;
  activeId: string | null;
  onOpen: (id: string) => void;
  onSwitchMe: (me: string) => void; // ours:
  query: string;
  setQuery: (q: string) => void;
}) {
  return (
    // The outer cell carries the sand down the whole page; the aside itself stays in view.
    <div className="hidden border-r border-zinc-200 bg-sand xl:block">
    <aside aria-label="Workspace" className="sticky top-0 flex h-dvh flex-col gap-4 p-4">
      <div className="px-1 py-1.5">
        <Logo product={false} />
      </div>
      <div className="relative">
        <Icon name="search" className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-quiet" />
        <input
          type="search"
          aria-label="Search customers"
          placeholder="Search customers"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className={`${inputClass} pl-8`}
        />
      </div>
      <Link href="/new-customer" className="group flex items-center gap-3 rounded-xl bg-white p-3 text-left ring-1 ring-zinc-200 transition-colors hover:bg-sand-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600">
        <span aria-hidden className="grid size-9 shrink-0 place-items-center rounded-full bg-ink text-xl leading-none text-paper transition-transform duration-200 group-hover:rotate-90">+</span>
        <span className="min-w-0"><span className="block text-sm font-semibold text-ink">Add a customer</span><span className="mt-0.5 block text-xs text-quiet">Create a project and pick its home</span></span>
        <span aria-hidden className="ml-auto text-lg text-quiet transition-transform duration-200 group-hover:translate-x-0.5">›</span>
      </Link>
      <Segmented
        name="scope"
        label="Show customers"
        value={scope}
        options={[
          { value: "mine", label: "Mine" },
          { value: "team", label: "Team" },
        ]}
        onChange={setScope}
      />
      <nav aria-label="Customers" className="-mx-1 min-h-0 flex-1 overflow-y-auto px-1">
        <ul className="space-y-0.5">
          {list.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                aria-current={c.id === activeId ? "page" : undefined}
                onClick={() => onOpen(c.id)}
                className="w-full rounded-lg px-2.5 py-2 text-left transition-colors hover:bg-sand-2 focus-visible:outline-2 focus-visible:outline-blue-600 aria-[current=page]:bg-white aria-[current=page]:ring-1 aria-[current=page]:ring-zinc-200"
              >
                <span className="flex items-center gap-2.5">
                <Avatar name={c.name || "Unnamed customer"} />
                <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium text-ink">{c.name || "Unnamed customer"}</span>
                <span className="block truncate text-xs text-quiet">
                  {scope === "team" && `${c.owner.split(" ")[0]} · `}
                  {typeof c.inputs.annual_consumption_kwh === "number" ? `${num(c.inputs.annual_consumption_kwh, 0)} kWh/yr` : "Use unknown"}
                  {" · "}
                  {CHOICE_LABEL[String(c.inputs.heating_type)] ?? "Heating unknown"}
                </span>
                </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
        {list.length === 0 && (
          <p className="px-2.5 text-xs text-quiet">{query ? `No customer matches “${query}”.` : "No customers yet."}</p>
        )}
      </nav>
      <label className="block space-y-1 text-xs text-quiet">
        <span>Signed in as</span>
        <span className="flex items-center gap-2">
          <Avatar name={ws.me} size={7} />
          <Select // ours: custom control
            value={ws.me}
            onChange={onSwitchMe}
            options={TEAM.map((t) => ({ value: t, label: t }))}
          />
        </span>
      </label>
    </aside>
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

function FieldLabel({ name, htmlFor, edited, children }: { name: string; htmlFor?: string; edited?: boolean; children: string }) {
  const Tag = htmlFor ? "label" : "div";
  return (
    <Tag htmlFor={htmlFor} aria-hidden={htmlFor ? undefined : true} className="flex items-center gap-2 text-sm text-ink">
      {FIELD_ICON[name] && <Icon name={FIELD_ICON[name]} />}
      {children}
      {edited && <span className="text-xs text-quiet">(edited)</span>}
    </Tag>
  );
}

// Grouped like the spec: one native <details> per topic, existing equipment kept apart from what is proposed.
function InputsPanel({ meta, inputs, saved, set }: {
  meta: Meta;
  inputs: Inputs;
  saved: Inputs;
  set: (name: string, v: InputValue) => void;
}) {
  const byName = new Map(meta.fields.map((f) => [f.name, f]));
  return (
    <Card className="divide-y divide-zinc-200">
      {FIELD_GROUPS.map((g, i) => {
        const fields = Object.keys(g.fields).flatMap((n) => (byName.has(n) ? [byName.get(n)!] : []));
        if (fields.length === 0) return null;
        const edited = fields.filter((f) => (inputs[f.name] ?? null) !== (saved[f.name] ?? null)).length;
        return (
          <details key={g.title} open={i < 2} className="group details-fade p-4"> {/* ours: fade the body in on expand */}
            <summary className="flex cursor-pointer items-center justify-between gap-2 text-sm font-medium text-ink">
              <span>
                {g.title}
                {g.existing && <span className="ml-2 text-xs font-normal text-quiet">already in the home</span>}
              </span>
              {edited > 0 && <span className="text-xs font-normal text-quiet">{edited} edited</span>}
            </summary>
            <div className="mt-3 space-y-3">
              {fields.map((f) => (
                <FieldInput
                  key={f.name}
                  field={f}
                  value={inputs[f.name] ?? null}
                  edited={(inputs[f.name] ?? null) !== (saved[f.name] ?? null)}
                  set={(v) => set(f.name, v)}
                />
              ))}
            </div>
          </details>
        );
      })}
    </Card>
  );
}

function FieldInput({ field, value, edited, set }: { field: Field; value: InputValue; edited: boolean; set: (v: InputValue) => void }) {
  const copy = FIELD_COPY[field.name];
  // Some fields read better scaled (a 0.03 price increase shows as 3 % per yr); the API keeps the raw value.
  const scale = copy.scale ?? 1;
  const id = `field-${field.name}`;
  const [numberDraft, setNumberDraft, commitNumberDraft] = useNumericDraft(typeof value === "number" ? value : null, scale);
  if (field.kind === "bool") {
    return (
      <div className="space-y-1">
        <FieldLabel name={field.name} edited={edited}>{copy.label}</FieldLabel>
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
        <FieldLabel name={field.name} htmlFor={id} edited={edited}>{copy.label}</FieldLabel>
        {/* "Unknown" stays: a real project can leave this empty. */}
        <Select // ours: custom control
          id={id}
          value={typeof value === "string" ? value : ""}
          onChange={(v) => set(v || null)}
          options={[{ value: "", label: "Unknown" }, ...field.choices.map((c) => ({ value: c, label: CHOICE_LABEL[c] ?? c }))]}
        />
      </div>
    );
  }
  return (
    <div className="space-y-1">
      <FieldLabel name={field.name} htmlFor={id} edited={edited}>{copy.label}</FieldLabel>
      <div className="flex items-center gap-2">
        <input
          id={id}
          type="number"
          inputMode="decimal"
          min={0}
          step={copy.step ?? "any"}
          placeholder="Unknown"
          className={inputClass}
          value={numberDraft}
          onChange={(e) => setNumberDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") e.currentTarget.blur(); }}
          onBlur={() => {
            // ours: review fix, only a real change becomes an edit (tabbing through a field no longer adds "4500 -> 4500")
            const next = numberDraft === "" ? null : Number(numberDraft) / scale;
            if (next === null ? value !== null : Number.isFinite(next) && next !== value) set(next);
            commitNumberDraft();
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
      <div key={`${e.cost_eur}-${e.savings_eur}`} className="fade-in grid grid-cols-3 gap-4"> {/* ours: numbers fade in when the design updates */}
        <Stat icon="wallet" label="Investment (estimate)" value={eur(e.cost_eur)} />
        <Stat icon="trend" label="Savings per year (estimate)" value={e.savings_eur === null ? "n/a" : eur(e.savings_eur)} />
        <Stat icon="clock" label="Payback (estimate)" value={years(e.payback_years)} sub="PV + battery" />
      </div>
      <p className="mt-3 text-xs text-muted">
        Estimates for the planner only, never shown to the homeowner. Rough assumptions: list prices, today&apos;s electricity price, a simple yield model. Heat pump fuel savings are not
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

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- ours: replaced by components/Evidence.tsx
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
        <>
          <p className="text-lg leading-snug font-semibold tracking-tight">
            Across {report.n_test} projects the model did{" "}
            {report.model.whole_design_within_tolerance >= report.baseline.whole_design_within_tolerance ? "better" : "worse"}{" "}
            than the rule of thumb at reproducing the installer&apos;s recorded design:{" "}
            {pct(report.model.whole_design_within_tolerance)} against {pct(report.baseline.whole_design_within_tolerance)}.
          </p>
          <p className="text-xs">
            A whole-design match means every part agrees with what the installer recorded for a project the model never saw.
            It is not the chance that this home&apos;s design is right.
          </p>
        </>
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


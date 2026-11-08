"use client";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, applyAnswer } from "@/lib/api";
import { isDemoForced, isPitchPlan } from "@/lib/pitch";
import { DEMO_INPUTS, deltas, describe, eur, HEATING_LABEL, homeOf, LABEL, num, pct, size, UNIT, withHome, years, type Home } from "@/lib/format";
import type { AskNext, Design, HoldoutRow, HomeInputs, Meta, Sizes, Source, Target } from "@/lib/types";
import { AskNextCard } from "./AskNextCard";
import { DiffBar, diffOf, type Diff } from "./DiffBar";
import { FlagList } from "./FlagList";
import { House } from "./House";
import { InputsCard, WIRE, type HomeKey } from "./InputsCard";
import { Reality } from "./Reality";
import { ShareDialog } from "./ShareDialog";
import { SystemCard } from "./SystemCard";
import { Button, Card, CheckList, ErrorNote, Footer, Header, Icon, Logo, PersonaChip, Stat } from "./ui";

const WIDTH = "max-w-[1500px]";

type Plan = { inputs: HomeInputs; locked: Partial<Sizes> };
type Shown = { key: string | null; design: Design | null; source: Source | null; error: string | null };

const BECAUSE: Record<HomeKey, (h: Home) => string> = {
  demandKwh: (h) => (h.demandKwh === null ? "the yearly electricity use is unknown" : `yearly electricity use is now ${num(h.demandKwh, 0)} kWh`),
  persons: (h) => (h.persons === null ? "the household size is unknown" : `the household is now ${h.persons} ${h.persons === 1 ? "person" : "people"}`),
  heatingType: (h) => `the current heating is now ${(HEATING_LABEL[h.heatingType] ?? h.heatingType).toLowerCase()}`,
  hasEv: (h) => (h.hasEv ? "there is now an electric car" : "there is no electric car"),
  evKm: (h) => (h.evKm === null ? "the car distance is unknown" : `the car now drives ${num(h.evKm, 0)} km a year`),
  roofModules: (h) => (h.roofModules === null ? "the roof size is unknown" : `the roof fits about ${h.roofModules} modules`),
};

export default function Planner() {
  const [meta, setMeta] = useState<{ data: Meta; source: Source } | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [plan, setPlan] = useState<Plan>({ inputs: DEMO_INPUTS, locked: {} });
  const [touched, setTouched] = useState<HomeKey[]>([]);
  const [source, setSource] = useState<string | null>(null);
  const [shown, setShown] = useState<Shown>({ key: null, design: null, source: null, error: null });
  const [diff, setDiff] = useState<{ diff: Diff; before: Plan } | null>(null);
  const [shareOpen, setShareOpen] = useState(false);

  // Set by the user's change, read when its design arrives: what we had before, and why the user changed it.
  const pending = useRef<{ before: Plan; design: Design | null; because: string } | null>(null);
  const last = useRef<Design | null>(null);

  useEffect(() => {
    api.meta().then(
      (m) => {
        setMeta(m);
        // The engine knows which installer styles exist; start on a real one.
        const first = m.data.installers[0];
        if (first) setPlan((p) => (m.data.installers.includes(p.inputs.installerId) ? p : { ...p, inputs: { ...p.inputs, installerId: first } }));
      },
      (e: Error) => setMetaError(e.message),
    );
  }, []);

  const key = useMemo(() => JSON.stringify(plan), [plan]);
  useEffect(() => {
    let live = true;
    const id = setTimeout(() => {
      api.design(plan.inputs, plan.locked, last.current?.sizes).then(
        ({ data, source }) => {
          if (!live) return;
          last.current = data;
          setShown({ key, design: data, source, error: null });
          const p = pending.current;
          pending.current = null;
          if (p?.design) {
            const d = deltas(p.design.metrics, data.metrics);
            const next = diffOf(p.design.sizes, data.sizes, d.price, d.autarkyPts, p.because);
            setDiff(next && { diff: next, before: p.before });
          }
        },
        (e: Error) => live && setShown((s) => ({ ...s, key, error: e.message })),
      );
    }, 250);
    return () => {
      live = false;
      clearTimeout(id);
    };
  }, [plan, key]);

  const { design } = shown;
  const busy = shown.key !== key;
  const home = homeOf(plan.inputs);

  /** Every user change goes through here so the diff bar knows what it was before and why it changed. */
  const commit = useCallback(
    (because: string, next: Plan) => {
      pending.current = { before: pending.current?.before ?? plan, design: pending.current?.design ?? last.current, because };
      setDiff(null);
      setPlan(next);
    },
    [plan],
  );

  const setHome = (patch: Partial<Home>, k: HomeKey) => {
    // What the planner typed is reported to the engine as "entered"; everything else it labels default or estimated.
    const base = withHome(plan.inputs, patch);
    const inputs = { ...base, provenance: { ...base.provenance, [WIRE[k]]: { source: "entered" as const, confidence: 1 } } };
    setTouched((t) => (t.includes(k) ? t : [...t, k]));
    commit(BECAUSE[k](homeOf(inputs)), { ...plan, inputs });
  };
  /** Clicking an answer writes it into the inputs as entered, which redesigns and shows the diff bar. */
  const answer = (q: AskNext, value: number | boolean, label: string) => {
    const k = (Object.keys(WIRE) as HomeKey[]).find((x) => WIRE[x] === q.field);
    if (k) setTouched((t) => (t.includes(k) ? t : [...t, k]));
    commit(`you answered "${q.question}" with ${/^(Yes|No)$/.test(label) ? label.toLowerCase() : label}`, { ...plan, inputs: applyAnswer(plan.inputs, q.field, value) });
  };
  const setSize = (t: Target, v: number) => commit(`you set the ${LABEL[t].toLowerCase()} to ${size(v, UNIT[t])}`, { ...plan, locked: { ...plan.locked, [t]: v } });
  const toggleLock = (t: Target) => {
    if (!design) return;
    const locked = { ...plan.locked };
    if (t in locked) delete locked[t];
    else locked[t] = design.sizes[t];
    commit(t in plan.locked ? `you unpinned the ${LABEL[t].toLowerCase()}` : `you pinned the ${LABEL[t].toLowerCase()}`, { ...plan, locked });
  };
  // Pitch mode: /pitch drives this page from outside (same origin only). With `because` it is a planner change
  // (diff bar); without, a fresh start like loading a project.
  const commitRef = useRef(commit);
  useEffect(() => {
    commitRef.current = commit;
  });
  useEffect(() => {
    const onMessage = (e: MessageEvent) => {
      if (e.origin !== window.location.origin || !isPitchPlan(e.data)) return;
      const next = { inputs: e.data.inputs, locked: e.data.locked ?? {} };
      if (e.data.because) return commitRef.current(e.data.because, next);
      pending.current = null;
      setDiff(null);
      setTouched([]);
      setSource(null);
      setPlan(next);
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  const undo = () => {
    if (!diff) return;
    pending.current = null;
    setPlan(diff.before);
    setDiff(null);
  };
  const load = (row: HoldoutRow) => {
    pending.current = null;
    setDiff(null);
    setTouched([]);
    setPlan({ inputs: row.inputs, locked: {} });
    setSource(row.projectId);
  };

  const demo = shown.source === "demo" || meta?.source === "demo";
  const m = design?.metrics;
  const shareBtn = (cls: string) => (
    <Button className={cls} disabled={!meta || !design || busy} onClick={() => setShareOpen(true)}>
      Share with customer <Icon name="arrow" className="size-4 text-current" />
    </Button>
  );

  return (
    <div className="flex min-h-dvh flex-col">
      <Header width={WIDTH}>
        <Logo />
        <PersonaChip who="planner" />
        <div className="ml-auto flex items-center gap-3">
          <span aria-live="polite" className="text-xs text-muted">
            {busy ? "Updating…" : ""}
          </span>
          {shareBtn("hidden lg:inline-flex")}
        </div>
      </Header>

      <main className={`mx-auto w-full flex-1 space-y-6 px-4 py-8 pb-28 sm:px-6 lg:pb-8 ${WIDTH}`}>
        <div className="max-w-3xl space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            Plan the system <span className="text-reonic">an expert would</span>
          </h1>
          <p className="max-w-[65ch] text-base">
            Describe the home. The model proposes solar, battery, heat pump and wallbox sizes the way experienced Reonic planners
            did on real projects. Pin what you have already decided.
          </p>
        </div>
        <ErrorNote error={metaError ?? shown.error} />
        {demo && (
          <p className="text-sm text-amber-900">
            <strong className="font-semibold">Demo data.</strong>{" "}
            {isDemoForced() ? (
              "Presentation mode: the numbers come from a toy model, not from the trained engine."
            ) : (
              <>
                The engine is not reachable, so the numbers come from a toy model. Start it with <code>npm run engine:dev</code>.
              </>
            )}
          </p>
        )}
        {!demo && meta?.data.synthetic && <p className="text-sm text-amber-900">Running on synthetic data: numbers are for the demo only.</p>}

        {/* Mobile order: inputs, house, system, proof. From lg the house column spans both rows. */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[320px_minmax(0,1fr)] lg:grid-rows-[auto_1fr]">
          <section className="space-y-2 lg:col-start-1" aria-labelledby="home">
            <h2 id="home" className="text-sm font-semibold text-ink">
              The home
            </h2>
            {meta ? (
              <InputsCard
                meta={meta.data}
                inputs={plan.inputs}
                home={home}
                provenance={design?.provenance}
                touched={touched}
                setHome={setHome}
                setInstaller={(id) => commit("the installer style changed", { ...plan, inputs: { ...plan.inputs, installerId: id } })}
              />
            ) : (
              <Skeleton className="h-80" />
            )}
            {design && <AskNextCard items={design.askNext} onAnswer={answer} />}
            <p className="text-xs text-muted">
              {source ? `Other inputs come from project ${source.slice(0, 8)}.` : "Other inputs use typical values."}
            </p>
          </section>

          <section className="min-w-0 space-y-4 lg:col-start-2 lg:row-span-2 lg:row-start-1" aria-label="Design">
            <Card className="overflow-hidden">
              <div className="relative h-[320px] bg-gradient-to-b from-sand-2 to-sand sm:h-[520px]">
                {design && <House values={design.sizes} hasEv={plan.inputs.ev?.has === true} description={describe(design.sizes)} />}
                <p className="pointer-events-none absolute top-3 left-4 text-xs text-quiet">Drag to turn</p>
              </div>
              {design && meta ? (
                <div className="border-t border-zinc-200">
                  <SystemCard design={design} meta={meta.data} locked={plan.locked} busy={busy} onSet={setSize} onToggleLock={toggleLock} />
                </div>
              ) : (
                <Skeleton className="m-4 h-40" />
              )}
              <div className="border-t border-zinc-200 p-4">
                {design ? (
                  <>
                    <div className={`grid grid-cols-2 gap-4 sm:grid-cols-4 ${busy ? "opacity-60" : ""}`}>
                      <Stat icon="wallet" label="Investment" value={m?.priceEur == null ? "n/a" : eur(m.priceEur)} />
                      <Stat icon="trend" label="Savings per year" value={m?.savingsEurYear == null ? "n/a" : eur(m.savingsEurYear)} />
                      <Stat icon="clock" label="Payback" value={years(m?.paybackYears ?? null)} />
                      <Stat icon="zap" label="Self-sufficiency" value={m?.autarky == null ? "n/a" : pct(m.autarky)} sub="autarky" />
                    </div>
                    <p className="mt-3 text-xs text-muted">
                      Rough assumptions: list prices, today&apos;s electricity price, a simple yield model. Heat pump fuel savings are
                      not included.
                    </p>
                  </>
                ) : (
                  <Skeleton className="h-20" />
                )}
              </div>
            </Card>

            {diff && <DiffBar diff={diff.diff} onUndo={undo} onDismiss={() => setDiff(null)} />}

            {design && (
              <>
                <FlagList flags={design.flags} />
                {design.reasons.length > 0 && (
                  <Card className="p-4 text-sm">
                    <h2 className="mb-3 text-sm font-semibold text-ink">Why this design</h2>
                    <CheckList items={design.reasons.slice(0, 4).map((r) => r.text)} />
                  </Card>
                )}
              </>
            )}
          </section>

          <div className="lg:col-start-1 lg:self-start">
            <Reality onLoad={load} />
          </div>
        </div>
      </main>

      {/* Phone: the summary and the one action stay in reach. */}
      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-zinc-200 bg-paper px-4 py-3 lg:hidden">
        <div className="mx-auto flex max-w-xl items-center gap-3">
          <p className="min-w-0 flex-1 text-sm" aria-live="polite">
            <span className="block truncate font-semibold text-ink tabular-nums">
              {m?.priceEur == null ? "Designing…" : eur(m.priceEur)}
              {m?.autarky != null && <span className="font-normal text-quiet"> · {pct(m.autarky)} self-sufficient</span>}
            </span>
            {m?.savingsEurYear != null && <span className="block truncate text-xs text-muted">saves about {eur(m.savingsEurYear)} a year</span>}
          </p>
          {shareBtn("shrink-0")}
        </div>
      </div>

      <ShareDialog open={shareOpen} onClose={() => setShareOpen(false)} meta={meta?.data ?? null} sizes={design?.sizes ?? null} inputs={plan.inputs} />
      <div className="pb-16 lg:pb-0">
        <Footer width={WIDTH}>
          Built for the Reonic challenge at thinc! München 2026. Every size is a proposal for a planner to check, not a quote.{" "}
          <Link href="/eval" className="underline underline-offset-2">Full evaluation</Link>
        </Footer>
      </div>
    </div>
  );
}

function Skeleton({ className }: { className: string }) {
  return <div className={`animate-pulse rounded-2xl bg-sand ${className}`} />;
}

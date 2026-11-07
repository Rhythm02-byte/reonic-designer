"use client";
// The homeowner's view of an offer: plain words, only the options the planner allowed, every number from the engine.
import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { api } from "@/lib/api";

import { CHOICE_NOTE, describe, eur, HOME_NAME, num, panels, pct, years } from "@/lib/format";
import { haptic } from "@/lib/haptics";
import type { Offer } from "@/lib/offer";
import { decodeOffer } from "@/lib/offer";
import { TARGETS } from "@/lib/types";
import type { Design, HomeInputs, Metrics, Sizes, Source, Target } from "@/lib/types";
import { BatteryCurve } from "./BatteryCurve";
import { House } from "./House";
import { Button, Card, CheckDot, ErrorNote, Footer, Header, Logo, MinusDot, PersonaChip, Segmented } from "./ui";

const WIDTH = "max-w-5xl";

function optionLabel(t: Target, v: number) {
  if (v === 0) return "None";
  return t === "pvKwp" ? `${panels(v)} panels` : `${num(v)} ${t === "batteryKwh" ? "kWh" : "kW"}`;
}

function explain(t: Target, v: number, inputs: HomeInputs) {
  if (v === 0) return CHOICE_NOTE.none[t];
  const heating = inputs.heating?.type;
  const from = heating && heating !== "Unknown" && heating !== "Heatpump" ? heating.toLowerCase() : "your current";
  return {
    pvKwp: `${panels(v)} panels on your roof. Together they peak at ${num(v)} kWp (kilowatt-peak, the most they make in full sun).`,
    batteryKwh: `Stores ${num(v)} kWh (kilowatt-hours) of daytime solar power, so you can use it in the evening.`,
    heatPumpKw: `Heats your home and water with electricity instead of ${from} heating. ${num(v)} kW is its heating power.`,
    wallboxKw: `Charges your electric car at home. At ${num(v)} kW (kilowatts) ${v > 11 ? "it charges about twice as fast, if your car supports it" : "a typical car is full overnight"}.`,
  }[t];
}

const same = (a: Sizes, b: Sizes) => TARGETS.every((t) => a[t] === b[t]);

/** The recommendation pinned at the engine: metrics, curves and checks around exactly this system. */
function useBase(offer: Offer) {
  const [state, setState] = useState<{ design?: Design; source?: Source; error?: string }>({});
  useEffect(() => {
    let live = true;
    api.designPinned(offer.inputs, offer.recommended).then(
      (r) => live && setState({ design: r.data, source: r.source }),
      (e: Error) => live && setState({ error: e.message }),
    );
    return () => {
      live = false;
    };
  }, [offer]);
  return state;
}

/** Metrics for the homeowner's own mix, from /simulate. */
function useChoice(inputs: HomeInputs, choice: Sizes) {
  const key = JSON.stringify(choice);
  const [state, setState] = useState<{ key?: string; metrics?: Metrics | null; error?: string }>({});
  useEffect(() => {
    let live = true;
    api.simulate(inputs, choice).then(
      (r) => live && setState({ key, metrics: r.data }),
      (e: Error) => live && setState((s) => ({ ...s, key, error: e.message })),
    );
    return () => {
      live = false;
    };
    // `choice` is represented by `key`
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputs, key]);
  return { ...state, busy: state.key !== key };
}

const subscribe = (cb: () => void) => {
  window.addEventListener("hashchange", cb);
  return () => window.removeEventListener("hashchange", cb);
};

export default function OfferPage() {
  // The offer travels in the URL hash. null on the server, where there is no hash.
  const hash = useSyncExternalStore(subscribe, () => window.location.hash.slice(1), () => null);
  const offer = useMemo(() => (hash === null ? undefined : decodeOffer(hash)), [hash]);
  return (
    <div className="flex min-h-dvh flex-col">
      <Header width={WIDTH}>
        <Logo />
        <PersonaChip who="homeowner" />
      </Header>
      <main className={`mx-auto w-full flex-1 px-4 py-8 pb-28 sm:px-6 lg:pb-8 ${WIDTH}`}>
        {offer === undefined && <div className="h-96 animate-pulse rounded-2xl bg-sand" />}
        {offer === null && (
          <ErrorNote error="This offer link is incomplete or damaged. Please ask your installer to send it again." />
        )}
        {offer && <OfferView key={hash} offer={offer} />}
      </main>
      <div className="pb-16 lg:pb-0">
        <Footer width={WIDTH}>
          This link carries your home&apos;s details in the address itself. Share it only with people you trust.
        </Footer>
      </div>
    </div>
  );
}

function OfferView({ offer }: { offer: Offer }) {
  const { inputs, recommended, options } = offer;
  const [choice, setChoice] = useState<Sizes>(recommended);
  const base = useBase(offer);
  const changed = !same(choice, recommended);
  const mine = useChoice(inputs, choice);
  const adjustable = TARGETS.some((t) => options[t].length > 1);
  const recMetrics = base.design?.metrics ?? null;
  const myMetrics = changed ? (mine.metrics ?? null) : recMetrics;
  const myBusy = changed ? mine.busy : !base.design;
  const curve = base.design?.curves?.battery;

  const pick = (t: Target, v: number) => {
    haptic("nudge");
    setChoice((c) => ({ ...c, [t]: v }));
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
        Your home energy offer, <span className="text-reonic">your way</span>
      </h1>
      {base.source === "demo" && (
        <p className="text-sm text-amber-900">
          <strong className="font-semibold">Demo data.</strong> The engine is not reachable, so these numbers come from a toy model.
        </p>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-6">
          <Card className="overflow-hidden">
            <div className="h-[280px] bg-gradient-to-b from-sand-2 to-sand sm:h-[400px]">
              <House
                values={choice}
                hasEv={inputs.ev?.has === true}
                description={describe(choice)}
                labels={{ pvKwp: `${panels(choice.pvKwp)} solar panels`, batteryKwh: `Battery ${num(choice.batteryKwh)} kWh`, heatPumpKw: HOME_NAME.heatPumpKw, wallboxKw: HOME_NAME.wallboxKw }}
              />
            </div>
          </Card>

          <section aria-labelledby="choose" className="space-y-3">
            <h2 id="choose" className="text-lg font-semibold text-ink">
              Try a different setup
            </h2>
            {!adjustable && <p className="text-sm">Your installer has fixed this offer. Ask them if you&apos;d like options.</p>}
            {TARGETS.map((t) => (
              <Card key={t} className="space-y-2 p-4">
                <div className="flex items-baseline justify-between gap-3">
                  <h3 className="flex items-center gap-2 font-medium text-ink">
                    {choice[t] > 0 ? <CheckDot className="size-5" /> : <MinusDot className="size-5" />}
                    {HOME_NAME[t]}
                    <span className="sr-only">{choice[t] > 0 ? "(included)" : "(not included)"}</span>
                  </h3>
                  {options[t].length === 1 && <span className="text-xs text-muted">As offered</span>}
                </div>
                <p className="text-base">{explain(t, choice[t], inputs)}</p>
                {options[t].length > 1 && (
                  <Segmented
                    name={`opt-${t}`}
                    label={HOME_NAME[t]}
                    value={choice[t]}
                    options={options[t].map((v) => ({ value: v, label: optionLabel(t, v) + (v === recommended[t] ? " ★" : "") }))}
                    onChange={(v) => pick(t, v)}
                  />
                )}
              </Card>
            ))}
            {adjustable && <p className="text-xs text-muted">★ = what your installer recommends</p>}
          </section>

          {curve && (
            <Card className="space-y-3 p-4" aria-labelledby="why-battery" role="region">
              <h2 id="why-battery" className="text-lg font-semibold text-ink">Why this battery size</h2>
              <p className="text-sm">
                A bigger battery covers more of your evening use, but each extra kWh adds less than the one before. This shows
                what the model expects for your home.
              </p>
              <BatteryCurve points={curve} chosenKwh={choice.batteryKwh} bestKwh={base.design?.physics?.economicKwh ?? null} />
            </Card>
          )}
        </div>

        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start" aria-label="Cost and savings">
          <ErrorNote error={base.error ?? mine.error ?? null} />
          <div aria-live="polite" className="grid grid-cols-2 gap-3">
            <Variant title="Recommended" m={recMetrics} active={!changed} busy={!base.design} />
            <Variant title="Your choice" m={myMetrics} active={changed} busy={myBusy} />
          </div>
          {changed && (
            <Button variant="secondary" onClick={() => setChoice(recommended)}>
              Back to the recommendation
            </Button>
          )}
          <p className="text-xs text-muted">
            Rough assumptions: today&apos;s electricity price, list prices and a simple solar model. Savings cover electricity only;
            a heat pump&apos;s fuel savings are not included.
          </p>
        </aside>
      </div>

      <section aria-labelledby="quote" className="relative overflow-hidden rounded-2xl bg-linear-to-br from-aubergine to-aubergine-2 px-6 py-10 text-paper sm:px-10">
        <div aria-hidden className="grain pointer-events-none absolute inset-0 opacity-30 mix-blend-overlay" />
        <h2 id="quote" className="relative max-w-xl text-2xl font-semibold tracking-tight sm:text-3xl">
          Your installer&apos;s final quote is what counts.
        </h2>
        <p className="relative mt-3 max-w-[60ch] text-base text-zinc-300">
          Tell them which setup you picked: this page forgets your choice when you close it.
        </p>
      </section>

      {/* Phone: the price of what you are looking at stays in view. */}
      <div className="fixed inset-x-0 bottom-0 z-20 border-t border-zinc-200 bg-paper px-4 py-3 lg:hidden">
        <p className={`mx-auto max-w-xl text-sm ${myBusy ? "opacity-60" : ""}`} aria-live="polite">
          <span className="font-semibold text-ink tabular-nums">{changed ? "Your choice" : "Recommended"}: {myMetrics?.priceEur == null ? "n/a" : eur(myMetrics.priceEur)}</span>
          {myMetrics?.savingsEurYear != null && <span className="text-quiet"> · saves about {eur(myMetrics.savingsEurYear)} a year</span>}
        </p>
      </div>
    </div>
  );
}

function Variant({ title, m, active, busy }: { title: string; m: Metrics | null; active: boolean; busy?: boolean }) {
  return (
    // An outline, not a ring: Card already sets a hairline border and the two colours would fight.
    <Card className={`p-4 ${active ? "outline-2 outline-blue-600" : ""} ${busy ? "opacity-60" : ""}`}>
      <div className="text-xs font-medium text-muted">
        {title}
        {active && <span className="sr-only"> (shown on the house)</span>}
      </div>
      {m ? (
        <>
          <div className="mt-1 text-xl font-semibold tracking-tight text-ink tabular-nums">{m.priceEur == null ? "n/a" : eur(m.priceEur)}</div>
          <p className="mt-2 text-xs">{m.savingsEurYear === null ? "Savings unknown" : `Saves about ${eur(m.savingsEurYear)} a year`}</p>
          {m.autarky !== null && <p className="text-xs">{pct(m.autarky)} of your power from the sun and battery</p>}
          {m.paybackYears !== null && <p className="text-xs">Pays back in about {years(m.paybackYears)}</p>}
        </>
      ) : busy ? (
        <div className="mt-2 h-16 animate-pulse rounded-lg bg-sand" />
      ) : (
        <p className="mt-2 text-xs">Not available</p>
      )}
    </Card>
  );
}

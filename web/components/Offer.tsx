"use client";
// The homeowner's view of an offer: plain words, only the options the planner allowed, every number from the API.
import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { api, TARGETS, type Economics, type Inputs, type Target, type Validation, type Values } from "@/lib/api";
import { CHOICE_LABEL, decodeOffer, describe, eur, num, type Offer, panels } from "@/lib/copy";
import { House } from "./House";
import { Button, Card, ErrorNote, Logo, PersonaChip, Segmented } from "./ui";

const NAME: Record<Target, string> = { pv_kwp: "Solar panels", battery_kwh: "Home battery", heat_pump_kw: "Heat pump", wallbox_kw: "Wallbox" };

function optionLabel(t: Target, v: number) {
  if (v === 0) return "None";
  return t === "pv_kwp" ? `${panels(v)} panels` : `${num(v)} ${t === "battery_kwh" ? "kWh" : "kW"}`;
}

function explain(t: Target, v: number, inputs: Inputs) {
  if (v === 0) {
    return {
      pv_kwp: "No solar panels in this setup.",
      battery_kwh: "No battery: solar power you don't use right away goes to the grid.",
      heat_pump_kw: "Your current heating stays as it is.",
      wallbox_kw: "No wallbox: the car charges from a normal socket or public chargers.",
    }[t];
  }
  const heating = typeof inputs.heating_type === "string" ? (CHOICE_LABEL[inputs.heating_type] ?? "current").toLowerCase() : "current";
  return {
    pv_kwp: `${panels(v)} panels on your roof. Together they peak at ${num(v)} kWp (kilowatt-peak, the most they make in full sun).`,
    battery_kwh: `Stores ${num(v)} kWh (kilowatt-hours) of daytime solar power, so you can use it in the evening.`,
    heat_pump_kw: `Heats your home and water with electricity instead of ${heating === "current" ? "your current" : heating} heating. ${num(v)} kW is its heating power.`,
    wallbox_kw: `Charges your electric car at home. At ${num(v)} kW (kilowatts) ${v > 11 ? "it charges about twice as fast, if your car supports it" : "a typical car is full overnight"}.`,
  }[t];
}

function useValidation(inputs: Inputs, values: Values) {
  const key = JSON.stringify(values);
  const [state, setState] = useState<{ key?: string; data?: Validation; error?: string }>({});
  useEffect(() => {
    let live = true;
    api.validate(inputs, values).then(
      (data) => live && setState({ key, data }),
      (e: Error) => live && setState((s) => ({ ...s, key, error: e.message })),
    );
    return () => {
      live = false;
    };
  }, [inputs, values, key]);
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
    <div className="min-h-dvh">
      <header className="border-b border-zinc-200/70 bg-paper">
        <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-3 sm:px-6">
          <Logo />
          <PersonaChip who="homeowner" />
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
        {offer === undefined && <div className="h-96 animate-pulse rounded-2xl bg-sand" />}
        {offer === null && (
          <ErrorNote error="This offer link is incomplete or damaged. Please ask your installer to send it again." />
        )}
        {offer && <OfferView key={hash} offer={offer} />}
      </main>
    </div>
  );
}

function OfferView({ offer }: { offer: Offer }) {
  const { inputs, recommended, options } = offer;
  const [choice, setChoice] = useState<Values>(recommended);
  const rec = useValidation(inputs, recommended);
  const mine = useValidation(inputs, choice);
  const changed = TARGETS.some((t) => choice[t] !== recommended[t]);
  const adjustable = TARGETS.some((t) => options[t].length > 1);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
        Your home energy offer, <span className="font-serif font-normal italic">your way</span>
      </h1>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-6">
          <Card className="overflow-hidden">
            <div className="h-[280px] bg-gradient-to-b from-sand-2 to-sand sm:h-[400px]">
              <House
                values={choice}
                hasEv={inputs.has_ev === true}
                description={describe(choice)}
                labels={{ pv_kwp: `${panels(choice.pv_kwp)} solar panels`, battery_kwh: `Battery ${num(choice.battery_kwh)} kWh`, heat_pump_kw: NAME.heat_pump_kw, wallbox_kw: NAME.wallbox_kw }}
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
                  <h3 className="font-medium text-ink">{NAME[t]}</h3>
                  {options[t].length === 1 && <span className="text-xs text-muted">As offered</span>}
                </div>
                <p className="text-sm">{explain(t, choice[t], inputs)}</p>
                {options[t].length > 1 && (
                  <Segmented
                    name={`opt-${t}`}
                    label={NAME[t]}
                    value={choice[t]}
                    options={options[t].map((v) => ({
                      value: v,
                      label: optionLabel(t, v) + (v === recommended[t] ? " ★" : ""),
                    }))}
                    onChange={(v) => setChoice((c) => ({ ...c, [t]: v }))}
                  />
                )}
              </Card>
            ))}
            {adjustable && <p className="text-xs text-muted">★ = what your installer recommends</p>}
          </section>
        </div>

        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start" aria-label="Cost and savings">
          <ErrorNote error={rec.error ?? mine.error ?? null} />
          <div aria-live="polite" className="grid grid-cols-2 gap-3">
            <Variant title="Recommended" econ={rec.data?.economics} active={!changed} />
            <Variant title="Your choice" econ={mine.data?.economics} active={changed} busy={mine.busy} />
          </div>
          {changed && (
            <Button variant="secondary" onClick={() => setChoice(recommended)}>
              Back to the recommendation
            </Button>
          )}
          <p className="text-xs text-muted">
            Rough assumptions: today&apos;s electricity price, list prices and a simple solar model. Savings cover electricity only;
            a heat pump&apos;s fuel savings are not included. Your installer&apos;s final quote is what counts.
          </p>
        </aside>
      </div>
    </div>
  );
}

function Variant({ title, econ, active, busy }: { title: string; econ?: Economics; active: boolean; busy?: boolean }) {
  return (
    // An outline, not a ring: Card already sets ring-1 ring-zinc-200 and the two ring colours would fight.
    <Card className={`p-4 ${active ? "outline-2 outline-emerald-500" : ""} ${busy ? "opacity-60" : ""}`}>
      <div className="text-xs font-medium text-muted">{title}</div>
      {econ ? (
        <>
          <div className="mt-1 text-xl font-semibold tracking-tight text-ink tabular-nums">{eur(econ.cost_eur)}</div>
          <p className="mt-2 text-xs">
            {econ.savings_eur === null ? "Savings unknown" : `Saves about ${eur(econ.savings_eur)} a year`}
          </p>
        </>
      ) : (
        <div className="mt-2 h-16 animate-pulse rounded-lg bg-sand" />
      )}
    </Card>
  );
}

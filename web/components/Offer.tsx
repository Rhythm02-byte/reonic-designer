"use client";
// The homeowner's view of an offer: plain words, only the options the planner allowed, every number from the API.
import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { api, TARGETS, type Economics, type Inputs, type Target, type Validation, type Values } from "@/lib/api";
import { CHOICE_LABEL, decodeOffer, describe, eur, num, type Offer, panels, pct } from "@/lib/copy";
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

/** Compared with the recommendation, in plain words. Honest in both directions: bigger is not sold as better. */
function verdict(rec: Economics, mine: Economics, changed: Target[]): string[] {
  if (!changed.length) return ["This is the setup your installer recommends."];
  const dc = mine.cost_eur - rec.cost_eur;
  const out = [`It costs ${eur(Math.abs(dc))} ${dc >= 0 ? "more" : "less"} upfront.`];
  if (mine.savings_eur !== null && rec.savings_eur !== null) {
    const ds = mine.savings_eur - rec.savings_eur;
    if (Math.abs(ds) < 20) out.push("Your yearly electricity savings stay about the same.");
    else out.push(`You'd save about ${eur(Math.abs(ds))} ${ds > 0 ? "more" : "less"} on electricity each year.`);
    if (dc > 0 && ds >= 20) {
      const y = dc / ds;
      out.push(
        y > 20
          ? `The extra would take about ${Math.round(y)} years to pay for itself, likely longer than the equipment lasts.`
          : `The extra pays for itself in about ${num(y, 0)} years.`,
      );
    } else if (dc > 0) out.push("The extra cost doesn't come back through lower electricity bills.");
    else if (dc < 0 && ds <= -20) {
      out.push(`You save money now, but after about ${num(-dc / -ds, 0)} years the recommended setup comes out ahead.`);
    }
  }
  if (changed.some((t) => t === "wallbox_kw" || t === "heat_pump_kw")) {
    out.push("A wallbox or heat pump has benefits these electricity savings don't count, such as lower fuel costs or charging at home.");
  }
  return out;
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
  const changed = TARGETS.filter((t) => choice[t] !== recommended[t]);
  const adjustable = TARGETS.filter((t) => options[t].length > 1);
  const included = TARGETS.filter((t) => recommended[t] > 0);

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Your home energy offer, <span className="font-serif font-normal italic">your way</span>
        </h1>
        <p className="mt-2 max-w-2xl text-body">
          Your installer recommends{" "}
          {included.length
            ? included.map((t) => `${NAME[t].toLowerCase()} (${optionLabel(t, recommended[t])})`).join(", ")
            : "keeping your home as it is"}
          . Try the options below and see what changes before you decide.
        </p>
      </section>

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
            {adjustable.length === 0 && <p className="text-sm">Your installer has fixed this offer. Ask them if you&apos;d like options.</p>}
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
            {adjustable.length > 0 && <p className="text-xs text-muted">★ = what your installer recommends</p>}
          </section>
        </div>

        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start" aria-label="Variants">
          <ErrorNote error={rec.error ?? mine.error ?? null} />
          <div className="grid grid-cols-2 gap-3">
            <Variant title="Recommended" econ={rec.data?.economics} active={!changed.length} />
            <Variant title="Your choice" econ={mine.data?.economics} active={changed.length > 0} busy={mine.busy} />
          </div>
          <Card className="p-4">
            <h2 className="text-sm font-semibold text-ink">What changes</h2>
            <div aria-live="polite" className="mt-1 space-y-1.5 text-sm">
              {rec.data && mine.data && !mine.busy ? (
                verdict(rec.data.economics, mine.data.economics, changed).map((l) => <p key={l}>{l}</p>)
              ) : (
                <p className="text-muted">Calculating…</p>
              )}
            </div>
            {changed.length > 0 && (
              <Button variant="secondary" className="mt-3" onClick={() => setChoice(recommended)}>
                Back to the recommendation
              </Button>
            )}
          </Card>
          {mine.data && mine.data.flags.length > 0 && changed.length > 0 && (
            <div className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900 ring-1 ring-amber-200">
              <div className="font-medium">Worth asking your installer about</div>
              <p className="mt-1">This setup is unusual for homes like yours. Your installer can tell you whether it makes sense.</p>
            </div>
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
          <dl className="mt-2 space-y-1 text-xs">
            <div>
              <dt className="sr-only">Savings</dt>
              <dd>{econ.savings_eur === null ? "Savings unknown" : `Saves about ${eur(econ.savings_eur)} a year`}</dd>
            </div>
            <div>
              <dt className="sr-only">Payback</dt>
              <dd>{econ.payback_years === null ? "No payback without solar" : `Solar pays back in about ${num(econ.payback_years, 0)} years`}</dd>
            </div>
            {econ.self_use_share !== null && econ.pv_yield_kwh > 0 && (
              <div>
                <dt className="sr-only">Own solar power used</dt>
                <dd>You use {pct(econ.self_use_share)} of your solar power yourself</dd>
              </div>
            )}
          </dl>
        </>
      ) : (
        <div className="mt-2 h-16 animate-pulse rounded-lg bg-sand" />
      )}
    </Card>
  );
}

"use client";
// The homeowner's view of an offer: plain words, only the whole options the planner approved, no prices.
import { useMemo, useState, useSyncExternalStore } from "react";
import { TARGETS, type Target, type Values } from "@/lib/api";
import { decodeOffer, describe, eur, num, type Offer, panels, years } from "@/lib/copy";
import { House } from "./House";
import { OfferParts } from "./PartsList"; // ours:
import { Card, CheckDot, ErrorNote, Footer, Header, Icon, Logo, MinusDot, PersonaChip, pill, pillLook } from "./ui";

const WIDTH = "max-w-5xl";

const NAME: Record<Target, string> = { pv_kwp: "Solar panels", battery_kwh: "Home battery", heat_pump_kw: "Heat pump", wallbox_kw: "Wallbox" };

function optionLabel(t: Target, v: number, wp?: number) { // ours: wp = the engine's module watts
  if (v === 0) return "Not included";
  return t === "pv_kwp" ? `${panels(v, wp)} panels` : `${num(v)} ${t === "battery_kwh" ? "kWh" : "kW"}`;
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
      <main className={`mx-auto w-full flex-1 px-4 py-8 sm:px-6 ${WIDTH}`}>
        {offer === undefined && <div className="h-96 animate-pulse rounded-2xl bg-sand" />}
        {offer === null && (
          <ErrorNote error="This offer link is incomplete or damaged. Please ask your installer to send it again." />
        )}
        {offer && <OfferView key={hash} offer={offer} />}
      </main>
      <Footer width={WIDTH}>
        {/* ours: one short line */}
        This link holds your home&apos;s details. Share it only with people you trust.
      </Footer>
    </div>
  );
}

function OfferView({ offer }: { offer: Offer }) {
  const { inputs, options, customer, planner, economics } = offer;
  const [i, setI] = useState(0);
  const choice = options[i].values;
  const subject = `Question about my home energy proposal (${options[i].label})`;
  const body = `Hello ${planner},

I looked at the proposal for ${customer} and I am interested in the option "${options[i].label}". Could we talk about it?

This is a request, not an order.`;
  // ours: minimal view, one line per part, savings inline, definitions and the full parts list collapsed
  const showEstimate = i === 0 && economics && (economics.savings_eur !== null || economics.payback_years !== null);

  return (
    <div className="space-y-5">
      <div className="space-y-1">
        <p className="text-sm text-quiet">Prepared by {planner} for {customer}</p>
        <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Your home energy <span className="text-reonic">proposal</span>
        </h1>
        {/* ours: review fix, the estimate belongs to the recommended setup only */}
        {showEstimate && (
          <p className="pt-1 text-base text-ink tabular-nums">
            {economics.savings_eur !== null && <><span className="font-semibold">{eur(economics.savings_eur)}/yr</span> <span className="text-quiet">est. savings</span></>}
            {economics.savings_eur !== null && economics.payback_years !== null && <span className="text-quiet"> · </span>}
            {economics.payback_years !== null && <><span className="font-semibold">{years(economics.payback_years)}</span> <span className="text-quiet">est. payback</span></>}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-4">
          <Card className="overflow-hidden">
            <div className="h-[260px] bg-gradient-to-b from-sand-2 to-sand sm:h-[400px]">
              <House
                values={choice}
                modules={panels(choice.pv_kwp, offer.moduleWp)} // ours:
                hasEv={inputs.has_ev === true}
                existing={{
                  pv_kwp: typeof inputs.existing_pv_kwp === "number" ? inputs.existing_pv_kwp : 0,
                  battery_kwh: typeof inputs.existing_battery_kwh === "number" ? inputs.existing_battery_kwh : 0,
                  wallbox: inputs.has_existing_wallbox === true,
                }}
                description={describe(choice, panels(choice.pv_kwp, offer.moduleWp))} // ours: wp
                labels={{ pv_kwp: `${panels(choice.pv_kwp, offer.moduleWp)} solar panels`, battery_kwh: `Battery ${num(choice.battery_kwh)} kWh`, heat_pump_kw: NAME.heat_pump_kw, wallbox_kw: NAME.wallbox_kw }}
              />
            </div>
          </Card>

          <ul aria-live="polite" aria-label={`In "${options[i].label}"`} className="divide-y divide-zinc-200 rounded-2xl border border-zinc-200 bg-white">
            {TARGETS.map((t) => (
              <li key={t} className={`flex items-center gap-3 px-4 py-3 ${choice[t] > 0 ? "text-ink" : "text-quiet"}`}>
                {choice[t] > 0 ? <CheckDot className="size-5" /> : <MinusDot className="size-5" />}
                <span className="font-medium">{NAME[t]}</span>
                <span className="ml-auto text-right text-sm tabular-nums">
                  {choice[t] > 0 ? optionLabel(t, choice[t], offer.moduleWp) : "Not included"}
                </span>
              </li>
            ))}
          </ul>

          <details className="group rounded-2xl border border-zinc-200 px-4 py-3 text-sm">
            <summary className="cursor-pointer font-medium text-ink focus-visible:outline-2 focus-visible:outline-blue-600">What do these mean?</summary>
            <p className="mt-2 text-quiet">
              kWp: most solar power the panels make in full sun. kWh: energy a battery stores. kW: power. First proposal; your installer checks roof and wiring on site and sends prices in a written quote.
            </p>
          </details>
          <details className="group rounded-2xl border border-zinc-200 px-4 py-3 text-sm">
            <summary className="cursor-pointer font-medium text-ink focus-visible:outline-2 focus-visible:outline-blue-600">Exact parts</summary>
            <div className="mt-3"><OfferParts inputs={inputs} values={choice} /></div> {/* ours: */}
          </details>
        </div>

        <aside className="space-y-4 lg:sticky lg:top-20 lg:self-start" aria-label="Options">
          {options.length > 1 && (
            <fieldset className="space-y-2">
              <legend className="mb-2 text-lg font-semibold text-ink">Options</legend>
              {options.map((o, k) => (
                <label
                  key={k}
                  className="flex cursor-pointer gap-3 rounded-2xl border border-zinc-200 bg-white p-3 has-checked:outline-2 has-checked:outline-blue-600 has-focus-visible:outline-2 has-focus-visible:outline-blue-600"
                >
                  <input type="radio" name="option" className="mt-1 size-4 accent-blue-600" checked={i === k} onChange={() => setI(k)} />
                  <span className="space-y-0.5">
                    <span className="block font-medium text-ink">
                      {o.label}
                      {k === 0 && o.label !== "Recommended" && <span className="ml-2 rounded-full whitespace-nowrap bg-sand px-2 py-0.5 text-xs font-medium text-quiet">Recommended</span>}
                    </span>
                    <span className="block text-sm text-quiet">{summary(o.values, offer.moduleWp)}</span>
                  </span>
                </label>
              ))}
            </fieldset>
          )}
          <a
            href={`mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`}
            className={`${pill} ${pillLook.primary} w-full justify-center`}
          >
            Ask {planner} about this option <Icon name="arrow" className="size-4" />
          </a>
        </aside>
      </div>
    </div>
  );
}

const summary = (v: Values, wp?: number) => { // ours: wp
  const parts = TARGETS.filter((t) => v[t] > 0).map((t) => `${NAME[t]} ${optionLabel(t, v[t], wp)}`);
  return parts.length ? parts.join(" · ") : "No new equipment";
};

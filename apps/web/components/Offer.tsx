"use client";
// The homeowner's view of an offer: plain words, only the whole options the planner approved, no prices.
import { useMemo, useState, useSyncExternalStore } from "react";
import { TARGETS, type Inputs, type Target, type Values } from "@/lib/api";
import { CHOICE_LABEL, decodeOffer, describe, eur, num, type Offer, panels, years } from "@/lib/copy";
import { House } from "./House";
import { OfferParts } from "./PartsList"; // ours:
import { Button, Card, CheckDot, ErrorNote, Footer, Header, Icon, Logo, MinusDot, PersonaChip, pill, pillLook } from "./ui";

const WIDTH = "max-w-5xl";

const NAME: Record<Target, string> = { pv_kwp: "Solar panels", battery_kwh: "Home battery", heat_pump_kw: "Heat pump", wallbox_kw: "Wallbox" };

function optionLabel(t: Target, v: number, wp?: number) { // ours: wp = the engine's module watts
  if (v === 0) return "Not included";
  return t === "pv_kwp" ? `${panels(v, wp)} panels` : `${num(v)} ${t === "battery_kwh" ? "kWh" : "kW"}`;
}

function explain(t: Target, v: number, inputs: Inputs, wp?: number) { // ours: wp
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
    pv_kwp: `${panels(v, wp)} panels on your roof. Together they peak at ${num(v)} kWp (kilowatt-peak, the most they make in full sun).`,
    battery_kwh: `Stores ${num(v)} kWh (kilowatt-hours) of daytime solar power, so you can use it in the evening.`,
    heat_pump_kw: `Heats your home and water with electricity instead of ${heating === "current" ? "your current" : heating} heating. ${num(v)} kW is its heating power.`,
    wallbox_kw: `Charges your electric car at home. At ${num(v)} kW (kilowatts) ${v > 11 ? "it charges about twice as fast, if your car supports it" : "a typical car is full overnight"}.`,
  }[t];
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
        This link carries your home&apos;s details in the address itself. Share it only with people you trust.
      </Footer>
    </div>
  );
}

function OfferView({ offer }: { offer: Offer }) {
  const { inputs, options, customer, planner, economics } = offer;
  const [i, setI] = useState(0);
  const choice = options[i].values;
  const rec = options[0].values;
  const included = TARGETS.filter((t) => choice[t] > 0);
  const changes = TARGETS.filter((t) => choice[t] !== rec[t]);
  const subject = `Question about my home energy proposal (${options[i].label})`;
  const body = `Hello ${planner},\n\nI looked at the proposal for ${customer} and I am interested in the option "${options[i].label}". Could we talk about it?\n\nThis is a request, not an order.`;

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <p className="text-sm text-quiet">
          Prepared by {planner} for {customer}
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
          Your home energy <span className="text-reonic">proposal</span>
        </h1>
      </div>

      {/* ours: review fix, the estimate belongs to the recommended setup only */}
      {i === 0 && economics && (economics.savings_eur !== null || economics.payback_years !== null) && (
        <Card className="grid grid-cols-2 gap-4 p-4 sm:max-w-sm">
          <div>
            <p className="text-xs text-muted">Estimated savings</p>
            <p className="text-lg font-semibold tracking-tight text-ink tabular-nums">
              {economics.savings_eur === null ? "n/a" : `${eur(economics.savings_eur)}/yr`}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted">Estimated payback</p>
            <p className="text-lg font-semibold tracking-tight text-ink tabular-nums">{years(economics.payback_years)}</p>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <Card className="overflow-hidden">
            <div className="h-[280px] bg-gradient-to-b from-sand-2 to-sand sm:h-[400px]">
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

          <section aria-labelledby="parts" className="space-y-3">
            <h2 id="parts" className="text-lg font-semibold text-ink">
              {i === 0 ? "What your installer recommends" : `What is in "${options[i].label}"`}
            </h2>
            <div aria-live="polite" className="space-y-3">
              {TARGETS.map((t) => (
                <Card key={t} className="space-y-1 p-4">
                  <h3 className="flex items-center gap-2 font-medium text-ink">
                    {choice[t] > 0 ? <CheckDot className="size-5" /> : <MinusDot className="size-5" />}
                    {NAME[t]}
                    <span className="text-sm font-normal text-quiet">{choice[t] > 0 ? "Included" : "Not included"}</span>
                  </h3>
                  <p className="text-base">{explain(t, choice[t], inputs, offer.moduleWp)}</p>
                </Card>
              ))}
            </div>
          </section>
          <OfferParts inputs={inputs} values={choice} /> {/* ours: */}
        </div>

        <aside className="space-y-4 lg:sticky lg:top-20 lg:self-start" aria-label="Options">
          {options.length > 1 ? (
            <fieldset className="space-y-2">
              <legend className="mb-2 text-lg font-semibold text-ink">Options from your installer</legend>
              {options.map((o, k) => (
                <label
                  key={k}
                  className="flex cursor-pointer gap-3 rounded-2xl border border-zinc-200 bg-white p-4 has-checked:outline-2 has-checked:outline-blue-600 has-focus-visible:outline-2 has-focus-visible:outline-blue-600"
                >
                  <input type="radio" name="option" className="mt-1 size-4 accent-blue-600" checked={i === k} onChange={() => setI(k)} />
                  <span className="space-y-0.5">
                    <span className="block font-medium text-ink">
                      {o.label}
                      {k === 0 && <span className="ml-2 rounded-full whitespace-nowrap bg-sand px-2 py-0.5 text-xs font-medium text-quiet">Installer&apos;s recommendation</span>}
                    </span>
                    <span className="block text-sm">{summary(o.values, offer.moduleWp)}</span>
                  </span>
                </label>
              ))}
            </fieldset>
          ) : (
            <p className="text-sm">Your installer offers one setup. Ask them if you&apos;d like to compare options.</p>
          )}
          {i > 0 && (
            <div className="space-y-3 rounded-2xl bg-sand-2 p-4 text-sm">
              <p className="font-medium text-ink">Compared with the recommendation</p>
              <ul className="space-y-1">
                {changes.map((t) => (
                  <li key={t}>
                    {NAME[t]}: {optionLabel(t, rec[t], offer.moduleWp)} → {optionLabel(t, choice[t], offer.moduleWp)}
                  </li>
                ))}
              </ul>
              <Button variant="secondary" onClick={() => setI(0)}>
                Back to recommended option
              </Button>
            </div>
          )}
          <p className="text-sm">
            Selected option: <span className="font-medium text-ink">{options[i].label}</span>. Choosing it here is not an
            order and signs nothing.
          </p>
          <a
            href={`mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`}
            className={`${pill} ${pillLook.primary} w-full justify-center`}
          >
            Ask {planner} about this option <Icon name="arrow" className="size-4" />
          </a>
        </aside>
      </div>

      <section aria-labelledby="notes" className="space-y-2 rounded-2xl border border-zinc-200 p-5 text-sm">
        <h2 id="notes" className="text-lg font-semibold text-ink">
          Good to know
        </h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>This is a first proposal based on what you told your installer. They check your roof and wiring on site.</li>
          <li>Prices and savings follow in your installer&apos;s written quote; this page shows none on purpose.</li>
          {included.length === 0 && <li>This option adds no new equipment.</li>}
          <li>kWp is the most solar power the panels make in full sun, kWh is how much energy a battery stores, kW is power.</li>
        </ul>
      </section>
    </div>
  );
}

const summary = (v: Values, wp?: number) => { // ours: wp
  const parts = TARGETS.filter((t) => v[t] > 0).map((t) => `${NAME[t]} ${optionLabel(t, v[t], wp)}`);
  return parts.length ? parts.join(" · ") : "No new equipment";
};

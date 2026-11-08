"use client";
// The homeowner's view of an offer: plain words, only the whole options the planner approved, no prices.
import { useMemo, useState, useSyncExternalStore } from "react";
import { TARGETS, type Inputs, type Target, type Values } from "@/lib/api";
import { decodeOffer, describe, eur, num, type Offer, panels, years } from "@/lib/copy";
import { House } from "./House";
import { RealHouse } from "./RealHouse";
import { OfferParts } from "./PartsList"; // ours:
import { Avatar, Card, CheckDot, ErrorNote, Footer, Header, Icon, Logo, MinusDot, PersonaChip, pill, pillLook, Radio } from "./ui";

const WIDTH = "max-w-[1440px]";

const NAME: Record<Target, string> = { pv_kwp: "Solar panels", battery_kwh: "Home battery", heat_pump_kw: "Heat pump", wallbox_kw: "Wallbox" };

function optionLabel(t: Target, v: number, wp?: number) { // ours: wp = the engine's module watts
  if (v === 0) return "Not included";
  return t === "pv_kwp" ? `${panels(v, wp)} panels` : `${num(v)} ${t === "battery_kwh" ? "kWh" : "kW"}`;
}

// These are explanations of the offered equipment and known inputs, not claims of a proven optimum.
function recommendationReasons(inputs: Inputs, rec: Values, moduleWp?: number) {
  const reasons: { title: string; text: string }[] = [];
  const consumption = typeof inputs.annual_consumption_kwh === "number" && inputs.annual_consumption_kwh > 0 ? inputs.annual_consumption_kwh : null;
  if (rec.pv_kwp > 0) {
    reasons.push({
      title: "Power for your everyday needs",
      text: `${panels(rec.pv_kwp, moduleWp)} solar panels are proposed${consumption ? ` for a home using about ${num(consumption, 0)} kWh of electricity per year` : " for your home"}. They can generate electricity for you to use at home.`,
    });
  }
  if (rec.battery_kwh > 0) {
    reasons.push({ title: "More of your solar power, when you need it", text: `The ${num(rec.battery_kwh)} kWh battery can store solar electricity made during the day for use later. How much you use depends on your daily routine and the weather.` });
  }
  if (rec.heat_pump_kw > 0) {
    const area = typeof inputs.heated_area_m2 === "number" && inputs.heated_area_m2 > 0 ? inputs.heated_area_m2 : null;
    reasons.push({ title: "Heating included in the plan", text: `The proposed heat pump brings heating into the same energy plan${area ? ` for your ${num(area, 0)} m² heated space` : " for your home"}. Your installer still needs to check your home's heat requirements on site.` });
  }
  if (rec.wallbox_kw > 0) {
    reasons.push({ title: "A convenient place to charge", text: `The ${num(rec.wallbox_kw)} kW home charger gives you a dedicated place to charge${inputs.has_ev === true ? " your electric car" : " an electric car"}. Your installer will check your car and electrical connection.` });
  }
  if (!reasons.length) reasons.push({ title: "A starting point for your conversation", text: "This recommendation does not add new equipment. Ask your installer how it fits your home's needs and which alternatives are available." });
  return reasons;
}

const subscribe = (cb: () => void) => {
  window.addEventListener("hashchange", cb);
  return () => window.removeEventListener("hashchange", cb);
};

// ours: demo recipient, first.last@rhythm.com (no real planner addresses in the link)
const demoMail = (name: string) => `${name.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim().split(/\s+/).join(".").replace(/[^a-z.]/g, "")}@rhythm.com`;

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
  const [asked, setAsked] = useState(false); // ours: mailto fallback note
  const choice = options[i].values;
  const reasons = recommendationReasons(inputs, options[0].values, offer.moduleWp);
  const subject = `Question about my home energy proposal (${options[i].label})`;
  const body = `Hello ${planner},

I looked at the proposal for ${customer} and I am interested in the option "${options[i].label}". Could we talk about it?

This is a request, not an order.`;
  // ours: minimal view, one line per part, savings inline, definitions and the full parts list collapsed
  const showEstimate = i === 0 && economics && (economics.savings_eur !== null || economics.payback_years !== null);

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-5 pb-2 sm:flex-row sm:items-end">
        <div className="max-w-3xl space-y-3"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-quiet">A more personal energy plan</p>
        <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-5xl">A brighter future, built around your home.</h1>
        <p className="max-w-xl text-base leading-relaxed text-quiet">Explore your energy proposal and find the setup that feels right for you.</p></div>
        <p className="flex shrink-0 items-center gap-2 text-sm text-quiet"><Avatar name={planner} size={7} /><span>Prepared for <span className="font-medium text-ink">{customer}</span><br />by {planner}</span></p>
        {/* ours: review fix, the estimate belongs to the recommended setup only */}
        {showEstimate && (
          <p className="pt-1 text-base text-ink tabular-nums">
            {economics.savings_eur !== null && <><span className="font-semibold">{eur(economics.savings_eur)}/yr</span> <span className="text-quiet">est. savings</span></>}
            {economics.savings_eur !== null && economics.payback_years !== null && <span className="text-quiet"> · </span>}
            {economics.payback_years !== null && <><span className="font-semibold">{years(economics.payback_years)}</span> <span className="text-quiet">est. payback</span></>}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_390px] xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="space-y-4">
          <Card className="overflow-hidden">
            <div className="h-[340px] bg-gradient-to-b from-sand-2 to-sand sm:h-[460px] xl:h-[550px]">
              {offer.location ? ( // ours: same Stylised / Real 3D toggle as the planner; stylised stays the default and the fallback
                <RealHouse location={{ address: "", ...offer.location }} proposedPanels={panels(choice.pv_kwp, offer.moduleWp)} existingPv={(typeof inputs.existing_pv_kwp === "number" && inputs.existing_pv_kwp > 0)}
                  fallback={
              <House
                    autoRotate
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
                  }
                  onAsset={() => {}} onLayout={() => {}} onCapacity={() => {}} />
              ) : (
              <House
                autoRotate
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
              )}
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

        <aside className="space-y-5 rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6 lg:sticky lg:top-20 lg:self-start" aria-label="Options">
          {options.length > 1 && (
            <fieldset className="space-y-2">
              <legend className="mb-2 text-lg font-semibold text-ink">Make it yours</legend>
              <p className="mb-4 text-sm text-quiet">Explore the setups your installer has prepared for your home.</p>
              {options.map((o, k) => (
                <label
                  key={k}
                  className="flex cursor-pointer gap-3 rounded-2xl border border-zinc-200 bg-white p-3 has-checked:outline-2 has-checked:outline-blue-600 has-focus-visible:outline-2 has-focus-visible:outline-blue-600"
                >
                  <Radio /* ours: custom control */ name="option" className="mt-1" checked={i === k} onChange={() => setI(k)} />
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
          {/* ours: mailto alone does nothing without a mail app; the message is also copied, and we say so */}
          <a
            href={`mailto:${demoMail(planner)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`}
            onClick={() => { navigator.clipboard?.writeText(`${subject}

${body}`).then(() => setAsked(true), () => setAsked(true)); }}
            className={`${pill} ${pillLook.primary} w-full justify-center`}
          >
            Talk to {planner} about this option <Icon name="arrow" className="size-4" />
          </a>
          <p aria-live="polite" className="min-h-4 text-xs text-quiet">{asked ? `Message copied: if no email window opened, paste it into a message to ${planner}.` : ""}</p>
        </aside>
      </div>
      <section aria-labelledby="why-recommended" className="grid gap-6 rounded-2xl border border-zinc-200 bg-white p-6 sm:p-8 lg:grid-cols-[minmax(220px,0.8fr)_2fr] lg:gap-12">
        <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-quiet">Made for your home</p><h2 id="why-recommended" className="mt-2 text-2xl font-semibold tracking-tight text-ink">Why this recommendation?</h2><p className="mt-3 text-sm leading-relaxed text-quiet">See how the recommended setup can support your home and the details behind it.</p>{i > 0 && <p className="mt-3 text-xs font-medium text-quiet">These reasons describe the recommendation, not the alternative currently selected.</p>}</div>
        <div><div className="grid gap-x-8 gap-y-5 sm:grid-cols-2">{reasons.map((reason) => <div key={reason.title} className="border-t border-zinc-200 pt-3"><h3 className="font-semibold text-ink">{reason.title}</h3><p className="mt-1 text-sm leading-relaxed text-quiet">{reason.text}</p></div>)}</div><p className="mt-6 text-xs leading-relaxed text-quiet">This is a starting recommendation based on the information available and similar past projects, with any adjustments made by your installer. Estimates use rough assumptions. It is not a guarantee of the best outcome; the roof, wiring, heating needs and final quote need an on-site check.</p></div>
      </section>
    </div>
  );
}

const summary = (v: Values, wp?: number) => { // ours: wp
  const parts = TARGETS.filter((t) => v[t] > 0).map((t) => `${NAME[t]} ${optionLabel(t, v[t], wp)}`);
  return parts.length ? parts.join(" · ") : "No new equipment";
};

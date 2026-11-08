"use client";
// The homeowner's view of an offer: plain words, only the whole options the planner approved, no prices.
import { useMemo, useState, useSyncExternalStore } from "react";
import { TARGETS, type Inputs, type Target, type Values } from "@/lib/api";
import { CHOICE_LABEL, decodeOffer, describe, eur, num, type Offer, panels, pct, years } from "@/lib/copy";
import { House } from "./House";
import { RealHouse } from "./RealHouse";
import { Avatar, Button, Card, CheckDot, ErrorNote, Footer, Header, Icon, type IconName, Logo, MinusDot, PersonaChip, pill, pillLook, Radio } from "./ui";

const WIDTH = "max-w-[1440px]";

const NAME: Record<Target, string> = { pv_kwp: "Solar panels", battery_kwh: "Home battery", heat_pump_kw: "Heat pump", wallbox_kw: "Wallbox" };
const PRODUCT_ICON: Record<Target, IconName> = { pv_kwp: "sun", battery_kwh: "battery", heat_pump_kw: "fan", wallbox_kw: "plug" };

const PRODUCT_INFO: Record<Target, string> = {
  pv_kwp: "Solar panels turn daylight into electricity for your home. Any electricity you do not use can be stored or fed into the grid.",
  battery_kwh: "A home battery stores solar electricity made during the day so you can use more of it later, for example in the evening.",
  heat_pump_kw: "A heat pump uses electricity to move heat from the air, ground or water into your home. It typically supplies several units of heat for each unit of electricity it uses.",
  wallbox_kw: "A wallbox is a dedicated, safely installed home charger for an electric car. It can be coordinated with solar production when compatible equipment is chosen.",
};

type PriceRange = { low: number; high: number };
function estimatedPrice(t: Target, size: number): PriceRange | null {
  if (size <= 0) return null;
  // Installed-price planning ranges, intentionally broad: a site survey and written quote decide the final price.
  if (t === "pv_kwp") return { low: size * 1300, high: size * 1800 };
  if (t === "battery_kwh") return { low: size * 300, high: size * 700 };
  if (t === "heat_pump_kw") return { low: 20000, high: 50000 };
  return { low: 1200, high: 3500 };
}

function optionLabel(t: Target, v: number, wp?: number) { // ours: wp = the engine module watts, same count as the planner
  if (v === 0) return "Not included";
  return t === "pv_kwp" ? `${panels(v, wp)} panels` : `${num(v)} ${t === "battery_kwh" ? "kWh" : "kW"}`;
}

function explain(t: Target, v: number, inputs: Inputs, wp?: number) {
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

// These are explanations of the offered equipment and known inputs, not claims of a proven optimum.
function recommendationReasons(inputs: Inputs, rec: Values, solarShare?: number | null, wp?: number) {
  const reasons: { title: string; text: string }[] = [];
  const consumption = typeof inputs.annual_consumption_kwh === "number" && inputs.annual_consumption_kwh > 0 ? inputs.annual_consumption_kwh : null;
  if (rec.pv_kwp > 0) {
    reasons.push({
      title: "Power for your everyday needs",
      text: `${panels(rec.pv_kwp, wp)} solar panels are proposed${consumption ? ` for a home using about ${num(consumption, 0)} kWh of electricity per year` : " for your home"}. ${solarShare != null ? `The estimate suggests solar could cover about ${pct(solarShare)} of your total electricity demand, including any modelled car or heating use.` : "They can generate electricity for you to use at home."}`,
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

// ours: demo recipient, first.last@rhythm.com (no real planner addresses in the link)
const demoMail = (name: string) => `${name.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim().split(/\s+/).join(".").replace(/[^a-z.]/g, "")}@rhythm.com`;

function OfferView({ offer }: { offer: Offer }) {
  const { inputs, options, customer, planner, economics, modelUrl, moduleWp: wp } = offer;
  const [i, setI] = useState(0);
  const [asked, setAsked] = useState(false); // ours: mailto fallback note
  const [info, setInfo] = useState<Target | null>(null);
  const choice = options[i].values;
  const rec = options[0].values;
  const included = TARGETS.filter((t) => choice[t] > 0);
  const changes = TARGETS.filter((t) => choice[t] !== rec[t]);
  const reasons = recommendationReasons(inputs, rec, economics?.solar_share_of_demand, wp);
  const subject = `Question about my home energy proposal (${options[i].label})`;
  const body = `Hello ${planner},\n\nI looked at the proposal for ${customer} and I am interested in the option "${options[i].label}". Could we talk about it?\n\nThis is a request, not an order.`;

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-5 pb-2 sm:flex-row sm:items-end">
        <div className="max-w-3xl space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-quiet">A more personal energy plan</p>
          <h1 className="text-3xl font-semibold tracking-tight text-ink sm:text-5xl">A brighter future, built around your home.</h1>
          <p className="max-w-xl text-base leading-relaxed text-quiet">Explore your energy proposal, see what is included, and find the setup that feels right for you.</p>
        </div>
        <p className="flex shrink-0 items-center gap-2 text-sm text-quiet"><Avatar name={planner} size={7} /><span>Prepared for <span className="font-medium text-ink">{customer}</span><br />by {planner}</span></p>
      </div>
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_390px] xl:grid-cols-[minmax(0,1fr)_420px]">
          <div className="relative overflow-hidden rounded-2xl bg-sand">
            <div className="h-[340px] sm:h-[460px] xl:h-[550px]">
              {offer.location ? ( // ours: Stylised (his LoD2 / standard house) or Real 3D, same toggle as the planner
                <RealHouse location={{ address: "", ...offer.location }} proposedPanels={panels(choice.pv_kwp, wp)} existingPv={typeof inputs.existing_pv_kwp === "number" && inputs.existing_pv_kwp > 0}
                  fallback={
                  <House
                    autoRotate
                    values={choice}
                    hasEv={inputs.has_ev === true}
                    existing={{
                      pv_kwp: typeof inputs.existing_pv_kwp === "number" ? inputs.existing_pv_kwp : 0,
                      battery_kwh: typeof inputs.existing_battery_kwh === "number" ? inputs.existing_battery_kwh : 0,
                      wallbox: inputs.has_existing_wallbox === true,
                    }}
                    description={describe(choice, panels(choice.pv_kwp, wp))} // ours: wp
                    modules={panels(choice.pv_kwp, wp)} // ours: same count as the planner
                    labels={{ pv_kwp: `${panels(choice.pv_kwp, wp)} solar panels`, battery_kwh: `Battery ${num(choice.battery_kwh)} kWh`, heat_pump_kw: NAME.heat_pump_kw, wallbox_kw: NAME.wallbox_kw }}
                    modelUrl={modelUrl}
                  />
                  }
                  onAsset={() => {}} onLayout={() => {}} onCapacity={() => {}} />
              ) : (
              <House
                autoRotate
                values={choice}
                hasEv={inputs.has_ev === true}
                existing={{
                  pv_kwp: typeof inputs.existing_pv_kwp === "number" ? inputs.existing_pv_kwp : 0,
                  battery_kwh: typeof inputs.existing_battery_kwh === "number" ? inputs.existing_battery_kwh : 0,
                  wallbox: inputs.has_existing_wallbox === true,
                }}
                description={describe(choice, panels(choice.pv_kwp, wp))} // ours: wp
                modules={panels(choice.pv_kwp, wp)} // ours: same count as the planner
                labels={{ pv_kwp: `${panels(choice.pv_kwp, wp)} solar panels`, battery_kwh: `Battery ${num(choice.battery_kwh)} kWh`, heat_pump_kw: NAME.heat_pump_kw, wallbox_kw: NAME.wallbox_kw }}
                modelUrl={modelUrl}
              />
              )}
            </div>
            <div className="pointer-events-none absolute inset-x-5 top-5 flex items-start justify-between gap-3 sm:inset-x-7 sm:top-7">
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-quiet">Your home, imagined</p><p className="mt-1 text-sm text-quiet">{options[i].label}</p></div>
              <span className="rounded-full bg-paper px-3 py-1.5 text-xs font-medium text-quiet">Interactive 3D</span>
            </div>
            <p className="pointer-events-none absolute bottom-5 left-5 rounded-full bg-paper px-3 py-1.5 text-xs text-quiet sm:left-7">Drag to explore your home</p>
          </div>
        <aside className="space-y-5 rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6 lg:self-stretch" aria-label="Options">
          {options.length > 1 ? (
            <fieldset className="space-y-2">
              <legend className="mb-1 text-xl font-semibold tracking-tight text-ink">Make it yours</legend>
              <p className="mb-4 text-sm leading-relaxed text-quiet">Explore the setups your installer has prepared for your home.</p>
              {options.map((o, k) => (
                <label
                  key={k}
                  className="flex cursor-pointer gap-3 rounded-xl border border-zinc-200 bg-sand-2 p-4 transition-colors hover:bg-sand has-checked:border-ink has-checked:bg-white has-checked:ring-1 has-checked:ring-ink has-focus-visible:outline-2 has-focus-visible:outline-blue-600"
                >
                  <Radio /* ours: custom control */ name="option" className="mt-1" checked={i === k} onChange={() => setI(k)} />
                  <span className="space-y-0.5">
                    <span className="block font-medium text-ink">
                      {o.label}
                      {k === 0 && <span className="ml-2 rounded-full whitespace-nowrap bg-sand px-2 py-0.5 text-xs font-medium text-quiet">Installer&apos;s recommendation</span>}
                    </span>
                    <span className="block text-sm">{summary(o.values, wp)}</span>
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
                    {NAME[t]}: {optionLabel(t, rec[t], wp)} → {optionLabel(t, choice[t], wp)}
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
          {/* ours: demo recipient; mailto alone does nothing without a mail app, so the message is also copied */}
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
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-quiet">Made for your home</p>
          <h2 id="why-recommended" className="mt-2 text-2xl font-semibold tracking-tight text-ink">Why this recommendation?</h2>
          <p className="mt-3 max-w-sm text-sm leading-relaxed text-quiet">A closer look at how the recommended setup can support your home and the details behind it.</p>
          {i > 0 && <p className="mt-3 text-xs font-medium text-quiet">These reasons describe the recommended option, not the alternative currently selected.</p>}
        </div>
        <div>
          <div className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
            {reasons.map((reason) => <div key={reason.title} className="border-t border-zinc-200 pt-3"><h3 className="font-semibold text-ink">{reason.title}</h3><p className="mt-1 text-sm leading-relaxed text-quiet">{reason.text}</p></div>)}
          </div>
          <p className="mt-6 text-xs leading-relaxed text-quiet">This is a starting recommendation based on the information available and similar past projects, with any adjustments made by your installer. Estimates use rough assumptions. It is not a guarantee of the best outcome; the roof, wiring, heating needs and final quote need an on-site check.</p>
        </div>
      </section>
      {economics && (economics.savings_eur !== null || economics.payback_years !== null) && (
        <section aria-label="Estimated savings for the recommended option" className="flex flex-col gap-5 rounded-2xl bg-[#e5efe2] p-6 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <div className="max-w-lg"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-quiet">A look ahead</p><h2 className="mt-2 text-xl font-semibold tracking-tight text-ink">The recommendation, in perspective.</h2><p className="mt-1 text-sm text-quiet">Rough estimates for the recommended option, based on your usage and today&apos;s electricity price. Not a guarantee.</p></div>
          <div className="flex gap-8 sm:gap-12">
            {economics.savings_eur !== null && <div><p className="text-xs text-quiet">Estimated savings / year</p><p className="mt-1 text-2xl font-semibold tracking-tight text-ink tabular-nums">{eur(economics.savings_eur)}</p></div>}
            {economics.payback_years !== null && <div><p className="text-xs text-quiet">Estimated payback</p><p className="mt-1 text-2xl font-semibold tracking-tight text-ink tabular-nums">{years(economics.payback_years)}</p></div>}
          </div>
        </section>
      )}
      <div className="mx-auto max-w-5xl pt-5">
          <section aria-labelledby="parts" className="space-y-3">
            <h2 id="parts" className="text-lg font-semibold text-ink">
              {i === 0 ? "What your installer recommends" : `What is in "${options[i].label}"`}
            </h2>
            <div aria-live="polite" className="space-y-3">
              {TARGETS.map((t) => (
                <Card key={t} className="space-y-2 p-4">
                  <h3 className="flex items-center gap-2 font-medium text-ink">
                    {choice[t] > 0 ? <CheckDot className="size-5" /> : <MinusDot className="size-5" />}
                    <Icon name={PRODUCT_ICON[t]} className="size-4 text-blue-600" />
                    {NAME[t]}
                    <span className="text-sm font-normal text-quiet">{choice[t] > 0 ? "Included" : "Not included"}</span>
                    <span className="relative ml-auto">
                      <button
                        type="button"
                        aria-label={`Learn about ${NAME[t]}`}
                        aria-expanded={info === t}
                        onClick={() => setInfo((current) => current === t ? null : t)}
                        onMouseEnter={() => setInfo(t)}
                        onMouseLeave={() => setInfo((current) => current === t ? null : current)}
                        onFocus={() => setInfo(t)}
                        onBlur={() => setInfo((current) => current === t ? null : current)}
                        className="grid size-5 place-items-center rounded-full border border-zinc-300 text-xs font-semibold text-quiet hover:bg-sand focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                      >
                        i
                      </button>
                      {info === t && (
                        <span role="tooltip" className="absolute top-7 right-0 z-10 w-64 rounded-lg bg-ink p-3 text-xs leading-relaxed text-paper shadow-sm">
                          {PRODUCT_INFO[t]}
                        </span>
                      )}
                    </span>
                  </h3>
                  <p className="text-base">{explain(t, choice[t], inputs, wp)}</p>
                  {estimatedPrice(t, choice[t]) && (() => {
                    const price = estimatedPrice(t, choice[t])!;
                    return <p className="text-sm text-quiet">Estimated installed price: <span className="font-medium text-ink">{eur(price.low)}–{eur(price.high)}</span></p>;
                  })()}
                </Card>
              ))}
            </div>
          </section>
      </div>

      <section aria-labelledby="notes" className="mx-auto max-w-5xl space-y-2 rounded-2xl border border-zinc-200 p-5 text-sm">
        <h2 id="notes" className="text-lg font-semibold text-ink">
          Good to know
        </h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>This is a first proposal based on what you told your installer. They check your roof and wiring on site.</li>
          <li>Price ranges include typical installation and are before grants, site work or any electrical upgrade. Your installer&apos;s written quote is the final price.</li>
          {included.length === 0 && <li>This option adds no new equipment.</li>}
          <li>kWp is the most solar power the panels make in full sun, kWh is how much energy a battery stores, kW is power.</li>
        </ul>
        <p className="text-xs text-muted">
          German planning ranges based on consumer guidance for{" "}
          <a className="underline decoration-zinc-300 underline-offset-2 hover:text-ink" href="https://www.verbraucherzentrale.de/wissen/energie/erneuerbare-energien/was-kostet-eine-photovoltaikanlage-49155" target="_blank" rel="noreferrer">solar</a>,{" "}
          <a className="underline decoration-zinc-300 underline-offset-2 hover:text-ink" href="https://www.verbraucherzentrale.de/wissen/energie/erneuerbare-energien/lohnen-sich-batteriespeicher-fuer-photovoltaikanlagen-24589" target="_blank" rel="noreferrer">batteries</a>,{" "}
          <a className="underline decoration-zinc-300 underline-offset-2 hover:text-ink" href="https://www.verbraucherzentrale.de/wissen/energie/heizen-und-warmwasser/waermepumpe-alles-was-sie-wissen-muessen-5439" target="_blank" rel="noreferrer">heat pumps</a> and{" "}
          <a className="underline decoration-zinc-300 underline-offset-2 hover:text-ink" href="https://www.adac.de/rund-ums-fahrzeug/elektromobilitaet/laden/wallbox-kosten/" target="_blank" rel="noreferrer">wallboxes</a>.
        </p>
      </section>
    </div>
  );
}

const summary = (v: Values, wp?: number) => {
  const parts = TARGETS.filter((t) => v[t] > 0).map((t) => `${NAME[t]} ${optionLabel(t, v[t], wp)}`);
  return parts.length ? parts.join(" · ") : "No new equipment";
};

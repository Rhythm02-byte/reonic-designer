// The pitch, slide by slide. Content slides are drawn on a 1920×1080 canvas; live slides show the real app.
// Every number on a content slide is a real aggregate (eval/results/latest.json, docs/PITCH.md) and says what it was
// measured on. Live slides run on the engine, or with ?demo=1 on the labelled toy model in lib/pitchDemo.ts.
import type { ReactNode } from "react";
import type { Inputs, Values } from "@/lib/api";
import { DEMO_INPUTS } from "@/lib/copy";

export type Plan = { inputs: Inputs; locked?: Partial<Values>; because?: string };
/** `focus`: a selector in the live page to scroll into view after the step (the audience sees the result). */
export type Step = { label: string; hint: string; plan?: Plan; focus?: string };
export type Frame = "planner" | "offer";

type Base = { id: string; title: string; notes: string };
export type ContentSlide = Base & { kind: "content"; body: () => ReactNode };
export type LiveSlide = Base & { kind: "live"; frame: Frame; steps: Step[] };
export type Slide = ContentSlide | LiveSlide;

// -- the demo home (Faris's flat planner inputs) ----------------------------------------------------------------
/** A new request: consumption unknown (the engine assumes the 4,500 kWh placeholder) and the roof unknown, as in many real projects. */
export const HOME: Inputs = { ...DEMO_INPUTS, annual_consumption_kwh: null, has_ev: false, ev_km_per_year: null };
const ANSWERED: Inputs = { ...HOME, annual_consumption_kwh: 5200 };
export const WITH_EV: Inputs = { ...ANSWERED, has_ev: true, ev_km_per_year: 12000 };

// -- building blocks --------------------------------------------------------------------------------------------
function Canvas({ children, tone = "paper", n }: { children: ReactNode; tone?: "paper" | "sand" | "dark"; n?: number }) {
  const bg = tone === "dark" ? "bg-aubergine text-paper" : tone === "sand" ? "bg-sand text-ink" : "bg-paper text-ink";
  return (
    <div className={`relative flex h-full w-full flex-col gap-12 px-32 pt-32 pb-40 ${bg}`}>
      {children}
      {n !== undefined && (
        <p className={`absolute right-32 bottom-16 text-[24px] tabular-nums ${tone === "dark" ? "text-zinc-300" : "text-quiet"}`}>{n}</p>
      )}
    </div>
  );
}
const H2 = ({ children }: { children: ReactNode }) => <h2 className="text-[72px] leading-[1.1] font-semibold tracking-[-0.02em]">{children}</h2>;
const Source = ({ children }: { children: ReactNode }) => <p className="absolute bottom-16 left-32 w-[1400px] text-[24px] text-quiet">{children}</p>;
const Eyebrow = ({ children, dark }: { children: ReactNode; dark?: boolean }) => (
  <p className={`text-[24px] font-semibold tracking-[0.06em] uppercase ${dark ? "text-orange-300" : "text-quiet"}`}>{children}</p>
);
const Card = ({ children, className = "" }: { children: ReactNode; className?: string }) => (
  <div className={`flex flex-col gap-4 rounded-3xl border border-zinc-200 bg-paper p-10 ${className}`}>{children}</div>
);
const Body = ({ children, className = "" }: { children: ReactNode; className?: string }) => (
  <p className={`text-[32px] leading-[1.4] text-body ${className}`}>{children}</p>
);

function Table({ head, rows, highlight }: { head: string[]; rows: string[][]; highlight: number }) {
  return (
    <table className="w-full text-[32px] tabular-nums">
      <thead>
        <tr className="border-b border-zinc-300 text-left text-quiet">
          {head.map((h, i) => (
            <th key={h} className={`py-4 font-semibold ${i ? "text-right" : ""}`}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, j) => (
          <tr key={r[0]} className={`border-b border-zinc-200 ${j === highlight ? "bg-sand font-semibold text-ink" : "text-body"}`}>
            {r.map((c, i) => (
              <td key={i} className={`px-3 py-5 ${i ? "text-right" : ""}`}>{c}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// -- the deck ---------------------------------------------------------------------------------------------------
export const SLIDES: Slide[] = [
  {
    kind: "content",
    id: "cover",
    title: "Designs like your best planner",
    notes: "Ein Satz: eine KI, die wie eure beste Planerin auslegt und sagt, was sie nicht weiß. Teamnamen nennen. ~10 s.",
    body: () => (
      <Canvas>
        <div className="flex flex-1 flex-col justify-center gap-12">
          <div className="bg-reonic h-3 w-48 rounded-full" />
          <Eyebrow>Reonic challenge · thinc! München 2026</Eyebrow>
          <h1 className="w-[1500px] text-[120px] leading-[1.05] font-semibold tracking-[-0.03em]">
            Designs like your <span className="text-reonic">best planner.</span>
          </h1>
          <p className="w-[1400px] text-[44px] leading-[1.3] text-body">
            A complete PV, battery, heat pump and wallbox design in under a second, checked against real experts, and honest about
            what it doesn’t know.
          </p>
        </div>
        <Source>Rhythm · Home Energy Designer · [Team names]</Source>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "problem",
    title: "The planner’s problem",
    notes:
      "Bei Installateur 1 dauerte es im Median 8,2 Tage von der Anfrage bis zum Angebot. Das ist Durchlaufzeit, keine Arbeitszeit. Jede Anlage wird von Hand ausgelegt, das erste glaubwürdige Angebot gewinnt oft, und Hausbesitzer haben Angst, überverkauft zu werden. ~20 s.",
    body: () => (
      <Canvas n={2}>
        <H2>The planner’s problem</H2>
        <div className="flex flex-1 items-center gap-24">
          <div className="flex w-[720px] flex-col gap-4">
            <p className="text-[200px] leading-none font-semibold tracking-[-0.04em]">8.2 days</p>
            <Body className="text-quiet">Median time from request to offer at installer 1 (n=257). Elapsed time, not planner hours.</Body>
          </div>
          <div className="flex flex-1 flex-col gap-8">
            {[
              ["Every home is designed by hand", "PV, battery, heat pump and wallbox are sized one project at a time before an offer can go out."],
              ["The first credible offer often wins", "And homeowners fear being oversold, so the offer has to explain itself."],
            ].map(([h, t]) => (
              <div key={h} className="flex flex-col gap-2 border-t border-zinc-200 pt-6">
                <h3 className="text-[44px] leading-[1.2] font-semibold">{h}</h3>
                <Body>{t}</Body>
              </div>
            ))}
          </div>
        </div>
        <Source>Source: Reonic export, installer 1; challenge brief p. 5</Source>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "data",
    title: "What the data really holds",
    notes:
      "Die „Wir haben wirklich reingeschaut“-Folie. Das Expertendesign gibt es nur als Stückliste, wir rekonstruieren alle Größen. Fast gleiche Häuser bekommen 5,4 bis 12,6 kWp, weil Dach und Budget fehlen: eine Grenze für jedes Modell. Speicher folgen dem Paket (0,93 kWh pro kWp), nicht dem Haushalt. ~20 s.",
    body: () => (
      <Canvas tone="sand" n={3}>
        <H2>What the data really holds</H2>
        <div className="grid grid-cols-2 gap-8">
          {[
            ["1,619", "signed projects, 2 installers. The design is only a parts list, so we rebuild every size from it."],
            ["5.4–12.6 kWp", "for near-identical homes (p10–p90, n=216). Roof size and budget aren’t in the data."],
            ["0.93 kWh per kWp", "battery to PV in every segment. Batteries follow the package, not the household."],
            ["~25%", "of installer 2’s offers have no PV, and their consumption is a 4,500 kWh placeholder."],
          ].map(([big, t]) => (
            <Card key={big} className="p-9">
              <p className="text-[72px] leading-[1.1] font-semibold tracking-[-0.02em]">{big}</p>
              <Body>{t}</Body>
            </Card>
          ))}
        </div>
        <Source>Source: Reonic export, aggregates only</Source>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "how",
    title: "How it designs a home",
    notes:
      "Ein Durchlauf von links nach rechts: gelernte Installateurs-Policy plus ähnliche Häuser, stündliche Simulation, Regeln und Katalog, dann das Design mit Bandbreiten, Gründen, Warnungen und der nächsten Frage. Reihenfolge nach Physik: Wärmepumpe, PV, Speicher. Kein LLM legt etwas aus. Danach direkt in die Live-Demo. ~20 s.",
    body: () => (
      <Canvas n={4}>
        <H2>How it designs a home</H2>
        <div className="flex items-stretch gap-4">
          {[
            ["Home facts", "Demand, EV, heating, roof type, existing PV"],
            ["Learned policy", "Gradient boosting chain plus similar past homes"],
            ["Hourly simulation", "PV yield, load, battery, EV, heat pump, 20-year money"],
            ["Rules + catalogue", "Hard limits, then snap to sizes the installer sells"],
          ].map(([h, t]) => (
            <div key={h} className="flex flex-1 items-center gap-4">
              <div className="flex h-full flex-1 flex-col gap-3 rounded-[20px] border border-zinc-200 bg-sand p-6">
                <h3 className="text-[32px] leading-[1.2] font-semibold">{h}</h3>
                <p className="text-[24px] leading-[1.4] text-body">{t}</p>
              </div>
              <span aria-hidden className="text-[40px] text-quiet">→</span>
            </div>
          ))}
          <div className="flex flex-1 flex-col gap-3 rounded-[20px] bg-ink p-6">
            <h3 className="text-[32px] leading-[1.2] font-semibold text-paper">Design</h3>
            <p className="text-[24px] leading-[1.4] text-zinc-300">Sizes with ranges, reasons, flags, and what to ask next</p>
          </div>
        </div>
        <div className="flex gap-12">
          {[
            ["Coupled, not four guesses", "Heat pump, then PV, then battery: each step sees the one before, so a planner’s change flows through."],
            ["No LLM in the decision", "Models trained on Reonic’s data size the system. An LLM may only phrase text, and everything works without one."],
          ].map(([h, t]) => (
            <div key={h} className="flex flex-1 flex-col gap-2 border-t border-zinc-200 pt-6">
              <h3 className="text-[32px] font-semibold">{h}</h3>
              <p className="text-[28px] leading-[1.4] text-body">{t}</p>
            </div>
          ))}
        </div>
      </Canvas>
    ),
  },
  {
    kind: "live",
    id: "planner",
    frame: "planner",
    title: "Live: the planner",
    notes:
      "Ihr bedient die echte Seite. Mit → (oder dem Presenter) springt die Demo zum nächsten Schritt, ihr könnt aber jederzeit selbst klicken und tippen. 1) Neue Anfrage: 4.500 kWh sehen nach Platzhalter aus, das Dach ist unbekannt, siehe „Ask next“. 2) Echten Verbrauch beantworten, der Diff-Balken erklärt, was sich bewegt. 3) E-Auto kommt: Wallbox erscheint. 4) Planer setzt den Speicher auf 20 kWh: Warnung. 5) Reality check: unter Evidence ein zurückgehaltenes Projekt laden und mit dem Experten vergleichen (Modell kennt es nicht). ~90 s.",
    steps: [
      {
        label: "New request",
        hint: "Consumption and roof are unknown. The design is there anyway; see “Ask next”.",
        plan: { inputs: HOME },
        focus: "top",
      },
      {
        label: "Real consumption",
        hint: "The planner answers the first question. The diff bar says what moved and why.",
        plan: { inputs: ANSWERED, because: "you answered “What does the home really use per year?” with 5,200 kWh" },
        focus: "[role=status]",
      },
      {
        label: "EV next year",
        hint: "The family is buying an electric car: a wallbox appears.",
        plan: { inputs: WITH_EV, because: "there is now an electric car" },
        focus: "[role=status]",
      },
      {
        label: "Battery 20 kWh",
        hint: "The planner overrides the battery. The override wins, and a flag explains the risk.",
        plan: { inputs: WITH_EV, locked: { battery_kwh: 20 }, because: "you set the battery to 20 kWh" },
        focus: "#design",
      },
      {
        label: "Reality check",
        hint: "Open “Evidence”, load a held-out project and compare our design with the expert’s.",
        focus: "#reality",
      },
    ],
  },
  {
    kind: "live",
    id: "offer",
    frame: "offer",
    title: "Live: the homeowner’s link",
    notes:
      "Das ist der Link, den der Planer teilt. Der Hausbesitzer sieht das Angebot in einfachen Worten, Bandbreiten statt Scheingenauigkeit, und kann nur zwischen den Optionen wechseln, die der Planer freigegeben hat, z. B. Speicher ja/nein. Einmal umschalten, dann zurück zu den Folien. ~20 s.",
    steps: [
      { label: "The offer", hint: "Plain words, the house, and only the options the planner allowed. Try switching the battery." },
    ],
  },
  {
    kind: "content",
    id: "proof",
    title: "Measured against experts",
    notes:
      "Trainiert auf Angeboten bis September 2025, Modell auf Q4 2025 gewählt, dann auf 325 Projekten aus 2026 bewertet (nie zur Modellwahl genutzt; jede Auswertung zählt das Lab mit). Die harte Baseline ist der Median des Installateurs selbst. Bei PV-Größe 17 Punkte besser, bei Speicher und Gesamtdesign gleichauf; 1 Punkt ist bei dieser Stichprobe Rauschen. Größenbandbreiten decken 85,5 % der PV-Entscheidungen der Experten ab (Ziel 80 %). ~25 s.",
    body: () => (
      <Canvas n={7}>
        <H2>Measured against experts on unseen projects</H2>
        <Table
          head={["Designer", "Expert Match", "Whole design", "PV ±20%", "Battery ±25%"]}
          rows={[
            ["Rule of thumb", "55.0", "14.8%", "32.9%", "40.0%"],
            ["Installer’s own median", "61.1", "20.6%", "42.5%", "47.4%"],
            ["Ours", "61.0", "20.9%", "59.7%", "47.4%"],
          ]}
          highlight={2}
        />
        <div className="bg-reonic flex flex-col gap-2 rounded-3xl px-12 py-10 text-ink">
          <p className="text-[44px] leading-[1.2] font-semibold">+17 points on PV size against the installer’s own median.</p>
          <p className="text-[32px] leading-[1.4]">Level with it on battery and on the whole design.</p>
        </div>
        <Source>Test: 325 projects from 2026, held out from training and model choice; every look is counted in /lab</Source>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "reading",
    title: "Where we win, and where we tie",
    notes:
      "PV hängt vom Haus ab, also lernt das Modell es und gewinnt klar. Der Speicher nicht: Experten verkaufen ~0,93 kWh pro kWp, egal welcher Haushalt. Das wirtschaftliche Optimum unseres Simulators trifft den Experten nur in 23 % der Fälle. Also übernehmen wir die Gewohnheit und zeigen die Wirtschaftlichkeit daneben als zweite Meinung. ~15 s.",
    body: () => (
      <Canvas tone="sand" n={8}>
        <H2>Where we win, and where we tie</H2>
        <div className="flex flex-1 gap-8">
          <Card className="flex-1 p-12">
            <Eyebrow>PV size · we win</Eyebrow>
            <p className="text-[120px] leading-none font-semibold tracking-[-0.03em]">59.7%</p>
            <Body>within 20% of the expert, against 42.5% for the installer’s median. PV depends on the home, so a model can learn it.</Body>
          </Card>
          <Card className="flex-1 p-12">
            <Eyebrow>Battery · we tie, and that’s a finding</Eyebrow>
            <p className="text-[120px] leading-none font-semibold tracking-[-0.03em]">23%</p>
            <Body>
              is how often the economic optimum matches the expert. Batteries are sized by habit, so we copy the habit and show the
              economics beside it.
            </Body>
          </Card>
        </div>
        <Source>PV: 2026 test, n=325 · Battery optimum: validation, n=232</Source>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "asknext",
    title: "It knows which question to ask next",
    notes:
      "Unser Alleinstellungsmerkmal. Die größte Schwäche der Daten wird zum Arbeitsschritt: Die Engine sagt, welche ein, zwei Fragen für dieses Haus am meisten ändern. Gemessen: Die Dachfrage hebt das Gesamtdesign von 20,9 % auf 32,9 % (Obergrenze, gedeckelt auf die Modulzahl des Experten). Echter Verbrauch statt Platzhalter: 11,1 % auf 20,9 %. ~25 s.",
    body: () => (
      <Canvas n={9}>
        <H2>It knows which question to ask next</H2>
        <Body className="w-[1500px]">
          The engine ranks missing inputs by how much they would change the design. We measured what each answer is worth on the 2026 test.
        </Body>
        <Table
          head={["Question answered", "Whole design right", "PV within ±20%"]}
          rows={[
            ["How many modules fit the roof?*", "20.9% → 32.9%", "59.7% → 82.5%"],
            ["Real yearly consumption", "11.1% → 20.9%", "46.5% → 59.7%"],
            ["Is there an EV?", "20.0% → 20.9%", "60.6% → 59.7%"],
          ]}
          highlight={0}
        />
        <p className="text-[44px] leading-[1.2] font-semibold">One question about the roof is worth more than any model we could train.</p>
        <Source>*Upper bound: the cap is the expert’s own module count · 2026 test, n=325</Source>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "impact",
    title: "What it’s worth",
    notes:
      "Drei Gewinner. Planer: Entwurf in unter einer Sekunde, Bearbeiten nur bei Ausnahmen, Warnungen vor dem Versand. Installateur: Junioren planen wie die eigenen Senioren. Hausbesitzer: ein Link, der das Angebot erklärt. Keine erfundene Stunden-Ersparnis: Die echten Stunden pro Auslegung fehlen uns noch. ~20 s.",
    body: () => (
      <Canvas tone="sand" n={10}>
        <H2>What it’s worth</H2>
        <div className="flex flex-1 gap-8">
          {[
            ["Planner", "A full first draft in under a second. Edit by exception, and see the flags before the offer goes out."],
            ["Installer", "Juniors design the way the installer’s seniors do, learned from its own history. More offers out, sooner."],
            ["Homeowner", "A link that explains the offer in plain words, with ranges instead of fake precision, and only the options the planner allowed."],
          ].map(([h, t]) => (
            <Card key={h} className="flex-1">
              <h3 className="text-[44px] leading-[1.2] font-semibold">{h}</h3>
              <Body>{t}</Body>
            </Card>
          ))}
        </div>
        <Source>A design takes under a second on a laptop · Hours saved per offer: [ask Reonic]</Source>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "limits",
    title: "What we can’t claim yet",
    notes:
      "Ehrlich abschließen: zwei Installateure, Wärmepumpen sind selten, also physikbasiert ausgelegt. Dachgröße fehlt und treibt den PV-Fehler, deshalb fragen wir danach. Grobe Physik. Als Nächstes: Stückliste in den Produkten des Installateurs, aus Planer-Overrides lernen, Dachkapazität als Standardfrage. Mit dem Einzeiler enden. Danke. ~15 s.",
    body: () => (
      <Canvas n={11}>
        <H2>What we can’t claim yet, and what’s next</H2>
        <div className="flex flex-1 gap-16">
          <div className="flex flex-[3] flex-col gap-6">
            <Eyebrow>Limits</Eyebrow>
            {[
              ["Two installers only.", "Heat pumps are about 2% of designs, so heat pump sizing comes from physics, not learning."],
              ["No roof size in the data.", "It’s the biggest source of PV error, so we ask for it instead of guessing."],
              ["Rough physics.", "One weather site; prices are 2026 ranges, and some costs are placeholders."],
            ].map(([b, t]) => (
              <p key={b} className="border-t border-zinc-200 pt-5 text-[32px] leading-[1.4] text-body">
                <b className="font-semibold text-ink">{b}</b> {t}
              </p>
            ))}
          </div>
          <div className="flex flex-[2] flex-col gap-6 rounded-3xl bg-ink p-12 text-paper">
            <Eyebrow dark>Next</Eyebrow>
            {["Parts list in the installer’s own products", "Learn each installer’s style from planner overrides", "Roof capacity as a standard intake question"].map((t) => (
              <p key={t} className="text-[32px] leading-[1.4]">{t}</p>
            ))}
          </div>
        </div>
      </Canvas>
    ),
  },
];

// The pitch, slide by slide. Content slides are drawn on a 1920×1080 canvas; live slides show the real app.
// Every number on a content slide is a real aggregate (eval/results/latest.json, docs/PITCH.md) and says what it was measured on.
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
const Source = ({ children }: { children: ReactNode }) => <p className="absolute bottom-16 left-32 w-[1400px] text-[24px] text-quiet">{children}</p>;


// -- the deck ---------------------------------------------------------------------------------------------------
// Story: hook, unsolvable problem, turn, how, live demo (planner, offer), honest proof, value, close. About 220 s in total.
export const SLIDES: Slide[] = [
  {
    kind: "content",
    id: "hook",
    title: "Eight days for an offer",
    notes:
      "Hook, ~10 s. Kurz warten lassen, dann: „Eine Familie will Solar. Sie wartet 8,2 Tage auf ein Angebot, im Median bei Installateur 1 (Durchlaufzeit, nicht Arbeitszeit). Am anderen Ende sitzt eine Planerin mit Dutzenden Anfragen.“ Teamnamen nennen: Rhythm and his dancers. Produkt: Rhythm.",
    body: () => (
      <Canvas>
        <div className="flex flex-1 flex-col justify-center gap-12">
          <div className="bg-reonic h-3 w-48 rounded-full" />
          <h1 className="w-[1600px] text-[160px] leading-[1.02] font-semibold tracking-[-0.03em]">
            A family waits <span className="text-reonic">8.2 days</span> for an offer.
          </h1>
          <p className="text-[40px] text-quiet">Median at installer 1, request to offer (n=257). Elapsed time, not planner hours.</p>
        </div>
        <Source>Rhythm and his dancers · Rhythm, the home energy designer · Reonic challenge, thinc! München 2026</Source>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "problem",
    title: "Why prediction alone fails",
    notes:
      "Problem, ~20 s. „Wir haben 1.619 echte Projekte angeschaut. Fast gleiche Häuser bekommen von Experten zwischen 5,4 und 12,6 kWp (p10 bis p90, n=216). Warum? Dachfläche und Budget stehen nicht in den Daten. Also kann ‚einfach vorhersagen‘ nicht funktionieren: Selbst das beste Modell rät.“",
    body: () => (
      <Canvas tone="sand" n={2}>
        <div className="flex flex-1 flex-col justify-center gap-10">
          <p className="text-[48px] text-quiet">Near-identical homes. Expert designs:</p>
          <p className="text-[260px] leading-none font-semibold tracking-[-0.04em]">5.4–12.6 kWp</p>
          <p className="w-[1500px] text-[64px] leading-[1.15] font-semibold">Roof and budget aren’t in the data. Guessing can’t fix that.</p>
        </div>
        <Source>p10–p90, 216 near-identical homes (4–5 MWh, no EV), 1,619 signed projects · Reonic export, aggregates only</Source>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "turn",
    title: "A designer that asks",
    notes:
      "Wendepunkt, ~15 s. Langsam sprechen: „Also haben wir einen Designer gebaut, der weiß, was er nicht weiß, und fragt.“ Kein LLM legt aus; ein Sprachmodell darf nur formulieren.",
    body: () => (
      <Canvas tone="dark" n={3}>
        <div className="flex flex-1 items-center">
          <h2 className="w-[1550px] text-[120px] leading-[1.08] font-semibold tracking-[-0.03em]">
            So we built a designer that knows what it doesn’t know, <span className="text-orange-300">and asks.</span>
          </h2>
        </div>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "how",
    title: "How it works",
    notes:
      "Wie, ~15 s. Von links nach rechts: ein paar Fakten zum Haus, gelernte Installateurs-Gewohnheit plus stündliche Simulation, dann ein Entwurf mit Bandbreiten, und die Frage, die am meisten ändert. Kein LLM legt aus; alles läuft ohne API-Key. Danach direkt in die Live-Demo.",
    body: () => (
      <Canvas n={4}>
        <div className="flex flex-1 items-center gap-6">
          {[
            ["A few facts", "about the home"],
            ["Learned + simulated", "installer habit, hourly physics"],
            ["A design with ranges", "and reasons"],
          ].map(([h, t]) => (
            <div key={h} className="flex flex-1 items-center gap-6">
              <div className="flex h-[360px] flex-1 flex-col justify-center gap-4 rounded-3xl border border-zinc-200 bg-sand p-10">
                <h3 className="text-[56px] leading-[1.1] font-semibold">{h}</h3>
                <p className="text-[36px] leading-[1.3] text-body">{t}</p>
              </div>
              <span aria-hidden className="text-[64px] text-quiet">→</span>
            </div>
          ))}
          <div className="bg-reonic flex h-[360px] flex-1 flex-col justify-center gap-4 rounded-3xl p-10 text-ink">
            <h3 className="text-[56px] leading-[1.1] font-semibold">The next question</h3>
            <p className="text-[36px] leading-[1.3]">the one that changes it most</p>
          </div>
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
      "Ihr bedient die echte Seite. Mit → (oder dem Presenter) springt die Demo zum nächsten Schritt, ihr könnt aber jederzeit selbst klicken und tippen. 1) Neue Anfrage: 4.500 kWh sehen nach Platzhalter aus, das Dach ist unbekannt, siehe „Ask next“. 2) Echten Verbrauch beantworten, der Diff-Balken erklärt, was sich bewegt. 3) E-Auto kommt: Wallbox erscheint. 4) Planer setzt den Speicher auf 20 kWh: Warnung. 5) Reality check: unter Evidence ein zurückgehaltenes Projekt laden und mit dem Experten vergleichen (Modell kennt es nicht). ~90 s. Absturzsicher: Falls die Engine ausfällt, D drücken für Offline-Demodaten (die Folien laufen weiter).",
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
      "Das ist der Link, den der Planer teilt. Der Hausbesitzer sieht das Angebot in einfachen Worten, Bandbreiten statt Scheingenauigkeit, und kann nur zwischen den Optionen wechseln, die der Planer freigegeben hat, z. B. Speicher ja/nein. Einmal umschalten, dann zurück zu den Folien. ~20 s. Absturzsicher: Falls die Engine ausfällt, D drücken für Offline-Demodaten.",
    steps: [
      { label: "The offer", hint: "Plain words, the house, and only the options the planner allowed. Try switching the battery." },
    ],
  },
  {
    kind: "content",
    id: "proof",
    title: "Honest proof",
    notes:
      "Beweis, ~20 s, ehrlich. Test: 325 Projekte aus 2026, nie zur Modellwahl benutzt. „Bei der PV-Größe sind wir 17 Punkte besser als die Gewohnheit des Installateurs selbst (59,7 gegen 42,5 Prozent innerhalb ±20 %). Beim ganzen Design gleichauf: 20,9 gegen 20,6 Prozent, das sagen wir offen. Und eine einzige Frage, die nach dem Dach, ist bis zu 12 Punkte wert: das ist eine Obergrenze.“",
    body: () => (
      <Canvas tone="sand" n={7}>
        <div className="flex flex-1 items-stretch gap-8">
          {[
            ["+17 pts", "PV size vs the installer’s own habit", false],
            ["22.2 vs 20.6%", "Whole design: slightly ahead, within noise", false],
            ["up to +11 pts", "from one roof question (upper bound)", true],
          ].map(([big, t, hot]) => (
            <div
              key={String(big)}
              className={`flex flex-1 flex-col justify-center gap-6 rounded-3xl p-12 ${hot ? "bg-reonic text-ink" : "border border-zinc-200 bg-paper"}`}
            >
              <p className="text-[110px] leading-none font-semibold tracking-[-0.03em]">{big}</p>
              <p className="text-[44px] leading-[1.2]">{t}</p>
            </div>
          ))}
        </div>
        <Source>2026 test, n=325, held out from training and model choice. Roof gain is an upper bound (cap = expert’s own module count).</Source>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "value",
    title: "Who wins",
    notes:
      "Wert, ~20 s. „Planer: ein vollständiger Entwurf in unter einer Sekunde, Warnungen vor dem Versand. Installateur: Junioren planen wie die eigenen Senioren. Hausbesitzer: ein Link, der das Angebot erklärt. Wie viele Stunden das pro Angebot spart, wissen wir nicht, das müssen wir von Reonic erfahren. Wir erfinden keine Zahl.“",
    body: () => (
      <Canvas n={8}>
        <div className="flex flex-1 gap-8">
          {[
            ["Planner", "A first draft in under a second."],
            ["Installer", "Juniors design like seniors."],
            ["Homeowner", "An offer that explains itself."],
          ].map(([h, t]) => (
            <div key={h} className="flex flex-1 flex-col justify-center gap-6 rounded-3xl border border-zinc-200 bg-sand p-12">
              <h3 className="text-[48px] leading-[1.2] font-semibold text-quiet">{h}</h3>
              <p className="text-[72px] leading-[1.1] font-semibold tracking-[-0.02em]">{t}</p>
            </div>
          ))}
        </div>
        <Source>Hours saved per offer: ask Reonic. We have no measured figure and won’t invent one. Draft time: a laptop, same input.</Source>
      </Canvas>
    ),
  },
  {
    kind: "content",
    id: "close",
    title: "Rhythm and his dancers",
    notes:
      "Schluss mit Energie, ~10 s. „Gute Planer raten nicht, sie fragen. Rhythm fragt für sie.“ Pause. „Wir sind Rhythm and his dancers. Danke.“ Bei Fragen: docs/PITCH.md, Abschnitt Jury-Fragen. Grenzen ehrlich nennen: zwei Installateure, Dachgröße fehlt, Stückliste vorläufig.",
    body: () => (
      <Canvas tone="dark">
        <div className="flex flex-1 flex-col justify-center gap-16">
          <div className="bg-reonic h-3 w-48 rounded-full" />
          <h2 className="w-[1600px] text-[140px] leading-[1.05] font-semibold tracking-[-0.03em]">
            Great planners don’t guess. <span className="text-orange-300">They ask.</span>
          </h2>
          <p className="text-[56px] font-semibold">Rhythm and his dancers</p>
        </div>
      </Canvas>
    ),
  },
];

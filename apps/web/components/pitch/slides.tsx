// The pitch, slide by slide. Content slides are drawn on a 1920×1080 canvas; live slides show the real app.
// Every number on a content slide is a real aggregate and names its source:
// - eval: eval/results/latest.json (generated 2026-11-08 06:35 UTC), blocks `served.test` and `oracle.fields`
// - data: the engine's own ETL (services/engine/engine/etl) over the Reonic export, aggregates only, recomputed 2026-11-08
import { motion, MotionConfig } from "motion/react";
import type { ReactNode } from "react";
import type { Inputs, Values } from "@/lib/api";
import { DEMO_INPUTS } from "@/lib/copy";
import { Icon, type IconName } from "../ui";

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

// -- the measured numbers, in one place -------------------------------------------------------------------------
const DATA = {
  daysToOffer: 8.2, // installer 1 (23c108b7), median request -> offer, n=260 with both dates
  projects: 1593, // projects with an expert design (parts list); 1,619 in the export
  cohort: { n: 215, p10: 6.3, p50: 9.45, p90: 12.4 }, // primary option, 4,000-5,000 kWh (not 4,500), no EV, no existing PV, PV > 0
};
const EVAL = {
  n: 325,
  rows: [
    { label: "PV size within ±20%", rule: 32.9, habit: 42.5, ours: 59.7 },
    { label: "Whole design right", rule: 14.8, habit: 20.6, ours: 22.2 },
  ],
  roof: { from: 22.2, to: 33.2 }, // oracle.fields.roof, UPPER BOUND: the cap is the expert's own module count
};

// -- building blocks --------------------------------------------------------------------------------------------
const EASE = [0.22, 1, 0.36, 1] as const;

/** Fades and lifts its children in, `delay` seconds after the slide appears. */
function Rise({ children, delay = 0, className = "" }: { children: ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 28 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay, ease: EASE }}
    >
      {children}
    </motion.div>
  );
}

function Canvas({ children, tone = "paper", n }: { children: ReactNode; tone?: "paper" | "sand" | "dark"; n?: number }) {
  const bg = tone === "dark" ? "bg-aubergine text-paper" : tone === "sand" ? "bg-sand text-ink" : "bg-paper text-ink";
  return (
    <MotionConfig reducedMotion="user">
      <div className={`relative flex h-full w-full flex-col gap-12 px-32 pt-28 pb-40 ${bg}`}>
        {children}
        {n !== undefined && (
          <p className={`absolute right-32 bottom-16 text-[24px] tabular-nums ${tone === "dark" ? "text-zinc-300" : "text-quiet"}`}>{n}</p>
        )}
      </div>
    </MotionConfig>
  );
}
const Source = ({ children, dark }: { children: ReactNode; dark?: boolean }) => (
  <p className={`absolute bottom-16 left-32 w-[1450px] text-[22px] leading-[1.4] ${dark ? "text-zinc-300" : "text-quiet"}`}>{children}</p>
);
const Eyebrow = ({ children, dark }: { children: ReactNode; dark?: boolean }) => (
  <p className={`text-[26px] font-semibold tracking-[0.08em] uppercase ${dark ? "text-[#a9dcc0]" : "text-quiet"}`}>{children}</p>
);
/** The sage-to-mint word on the dark slides (light stops: ink-dark background, so the light end reads). */
const Mint = ({ children }: { children: ReactNode }) => (
  <span className="bg-[linear-gradient(90deg,#d3e6c4,#8fd2c8)] bg-clip-text text-transparent forced-colors:text-[CanvasText]">{children}</span>
);

function RhythmMark({ className = "size-24" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden>
      <rect width="24" height="24" rx="7" fill="currentColor" />
      <g stroke="var(--color-aubergine)" strokeWidth={2.5} strokeLinecap="round">
        {[["M7.5 17v-2", 0.2], ["M12 17v-6", 0.35], ["M16.5 17V7", 0.5]].map(([d, delay]) => (
          <motion.path key={d as string} d={d as string} initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.5, delay: delay as number }} />
        ))}
      </g>
    </svg>
  );
}

// -- slide bodies -----------------------------------------------------------------------------------------------
function Hook() {
  const DAYS = 9;
  const at = (DATA.daysToOffer / DAYS) * 100;
  return (
    <Canvas>
      <div className="flex flex-1 flex-col justify-center gap-16">
        <Rise>
          <Eyebrow>Reonic challenge · thinc! München 2026</Eyebrow>
        </Rise>
        <Rise delay={0.1}>
          <h1 className="w-[1600px] text-[136px] leading-[1.02] font-semibold tracking-[-0.035em]">
            A family waits <span className="text-reonic">8.2 days</span> for a solar offer.
          </h1>
        </Rise>
        {/* the wait, drawn: one tick per day, the line runs to the median offer day */}
        <Rise delay={0.3} className="w-[1500px]">
          <div className="relative h-24">
            <div className="absolute top-1/2 h-2 w-full -translate-y-1/2 rounded-full bg-zinc-200" />
            <motion.div
              className="absolute top-1/2 h-2 -translate-y-1/2 rounded-full bg-ink"
              initial={{ width: 0 }}
              animate={{ width: `${at}%` }}
              transition={{ duration: 1.6, delay: 0.5, ease: EASE }}
            />
            {Array.from({ length: DAYS + 1 }, (_, d) => (
              <div key={d} className="absolute top-1/2 h-6 w-0.5 -translate-y-1/2 bg-zinc-300" style={{ left: `${(d / DAYS) * 100}%` }} />
            ))}
            <div className="absolute top-1/2 left-0 size-8 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-ink bg-paper" />
            <motion.div
              className="bg-reonic absolute top-1/2 size-12 -translate-x-1/2 -translate-y-1/2 rounded-full ring-4 ring-ink"
              style={{ left: `${at}%` }}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.4, delay: 2.0 }}
            />
          </div>
          <div className="relative mt-2 h-10 text-[28px] text-quiet">
            <span className="absolute left-0 -translate-x-1/2">Request</span>
            <span className="absolute -translate-x-1/2 font-semibold text-ink" style={{ left: `${at}%` }}>Offer</span>
          </div>
        </Rise>
      </div>
      <Source>Rhythm and his dancers · Rhythm, the home energy designer</Source>
    </Canvas>
  );
}

function Problem() {
  const { p10, p50, p90 } = DATA.cohort;
  const MAX = 16;
  const x = (v: number) => `${(v / MAX) * 100}%`;
  return (
    <Canvas tone="sand" n={2}>
      <Rise>
        <Eyebrow>What the data really holds</Eyebrow>
      </Rise>
      <Rise delay={0.1}>
        <h2 className="w-[1600px] text-[96px] leading-[1.05] font-semibold tracking-[-0.03em]">
          Same kind of home. Experts install up to <span className="text-reonic">twice the PV.</span>
        </h2>
      </Rise>
      {/* the spread, drawn on a kWp axis: the middle 80% of expert PV sizes for near-identical homes */}
      <Rise delay={0.3} className="mt-6 w-[1650px]">
        <div className="relative h-40">
          <div className="absolute top-1/2 h-1 w-full -translate-y-1/2 bg-zinc-300" />
          <motion.div
            className="bg-reonic absolute top-1/2 h-24 -translate-y-1/2 rounded-2xl ring-1 ring-ink/10"
            style={{ left: x(p10), originX: 0.5 }}
            initial={{ width: 0, marginLeft: `${((p90 - p10) / 2 / MAX) * 1650}px` }}
            animate={{ width: `${((p90 - p10) / MAX) * 100}%`, marginLeft: "0px" }}
            transition={{ duration: 1.1, delay: 0.6, ease: EASE }}
          />
          <motion.div
            className="absolute top-1/2 h-32 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ink"
            style={{ left: x(p50) }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.4 }}
          />
          {[p10, p90].map((v) => (
            <motion.p
              key={v}
              className="absolute -top-6 -translate-x-1/2 text-[44px] font-semibold tabular-nums"
              style={{ left: x(v) }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1.5 }}
            >
              {v.toFixed(1)}
            </motion.p>
          ))}
        </div>
        <div className="relative h-10 text-[26px] text-quiet tabular-nums">
          {[0, 4, 8, 12, 16].map((v) => (
            <span key={v} className="absolute -translate-x-1/2 whitespace-nowrap" style={{ left: x(v) }}>{v} kWp</span>
          ))}
        </div>
      </Rise>
      <Rise delay={1.8}>
        <p className="w-[1700px] text-[48px] leading-[1.25] font-semibold">
          Roof and budget aren’t in the data. <span className="text-quiet">No model can guess them.</span>
        </p>
      </Rise>
      <Source>Expert PV sizes for similar homes (middle 80%) · Reonic data</Source>
    </Canvas>
  );
}

function Turn() {
  return (
    <Canvas tone="dark" n={3}>
      <div className="flex flex-1 items-center gap-24">
        <Rise className="flex-[3]">
          <h2 className="text-[100px] leading-[1.08] font-semibold tracking-[-0.03em]">
            So we built a designer that knows what it doesn’t know, <Mint>and asks.</Mint>
          </h2>
        </Rise>
        {/* what that looks like in the product: the "Ask next" card, with the cohort's real range */}
        <Rise delay={0.5} className="flex-[2]">
          <div className="flex flex-col gap-6 rounded-[32px] bg-paper p-12 text-ink">
            <p className="flex items-center gap-3 text-[24px] font-semibold tracking-[0.08em] text-quiet uppercase">
              <Icon name="search" className="size-8 text-blue-600" /> Ask next
            </p>
            <p className="text-[48px] leading-[1.15] font-semibold">How many modules fit the roof?</p>
            <p className="text-[30px] leading-[1.35] text-body">PV for homes like this ranges 6–12 kWp. The roof decides it.</p>
            <div className="flex gap-4">
              {["12", "20", "30"].map((m, i) => (
                <motion.span
                  key={m}
                  className="rounded-full border border-zinc-200 bg-sand px-7 py-4 text-[28px] font-medium whitespace-nowrap"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 1.0 + i * 0.12 }}
                >
                  {m} modules
                </motion.span>
              ))}
            </div>
          </div>
        </Rise>
      </div>
    </Canvas>
  );
}

const STEPS: [IconName, string, string][] = [
  ["pin", "Home facts", "Demand, EV, heating, existing PV and storage"],
  ["users", "Installer habit", "Models trained on the installer’s past designs"],
  ["zap", "Hourly physics", "A full year of yield, battery and savings"],
  ["chart", "Rules + catalogue", "Hard limits, then sizes the installer sells"],
];

function How() {
  return (
    <Canvas n={4}>
      <Rise>
        <Eyebrow>How it works</Eyebrow>
      </Rise>
      <Rise delay={0.05}>
        <h2 className="w-[1600px] text-[80px] leading-[1.05] font-semibold tracking-[-0.03em]">From a few facts to a design, in under a second.</h2>
      </Rise>
      <div className="flex items-stretch gap-5">
        {STEPS.map(([icon, h, t], i) => (
          <Rise key={h} delay={0.25 + i * 0.15} className="flex flex-1 items-center gap-5">
            <div className="flex h-full flex-1 flex-col gap-4 rounded-3xl border border-zinc-200 bg-sand p-8">
              <div className="flex items-center justify-between">
                <Icon name={icon} className="size-14 text-blue-600" />
                <span className="text-[28px] font-semibold text-quiet tabular-nums">0{i + 1}</span>
              </div>
              <h3 className="text-[40px] leading-[1.15] font-semibold">{h}</h3>
              <p className="text-[28px] leading-[1.35] text-body">{t}</p>
            </div>
            {i < STEPS.length - 1 && <span aria-hidden className="text-[48px] text-quiet">→</span>}
          </Rise>
        ))}
      </div>
      <Rise delay={0.95}>
        <div className="flex items-center gap-10 rounded-3xl bg-ink px-12 py-7 text-paper">
          <p className="text-[44px] font-semibold">A complete design</p>
          <p className="flex-1 text-[30px] leading-[1.35] text-zinc-300">
            Every size with a range and a reason, plus the next question to ask.
          </p>
        </div>
      </Rise>
    </Canvas>
  );
}

function Proof() {
  const W = { rule: "bg-zinc-300", habit: "bg-zinc-500", ours: "bg-ink" } as const;
  return (
    <Canvas tone="sand" n={7}>
      <Rise>
        <h2 className="text-[80px] leading-[1.05] font-semibold tracking-[-0.03em]">Measured on {EVAL.n} projects it never saw.</h2>
      </Rise>
      <div className="flex flex-1 gap-14">
        {/* grouped bars: share of projects where the design matches the expert's within tolerance */}
        <div className="flex flex-[3] flex-col justify-center gap-9">
          <div className="flex gap-10 text-[26px] text-quiet">
            {([["rule", "Rule of thumb"], ["habit", "Installer’s own median"], ["ours", "Rhythm"]] as const).map(([k, l]) => (
              <span key={k} className={`flex items-center gap-3 ${k === "ours" ? "font-semibold text-ink" : ""}`}>
                <span className={`size-5 rounded-full ${W[k]}`} /> {l}
              </span>
            ))}
          </div>
          {EVAL.rows.map((r, i) => (
            <div key={r.label} className="flex flex-col gap-2">
              <p className="text-[30px] font-semibold">{r.label}</p>
              {(["rule", "habit", "ours"] as const).map((k, j) => (
                <div key={k} className="flex items-center gap-4">
                  <motion.div
                    className={`h-5 rounded-full ${W[k]}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${r[k] * 1.3}%` }}
                    transition={{ duration: 0.9, delay: 0.3 + i * 0.25 + j * 0.08, ease: EASE }}
                  />
                  <span className={`text-[24px] leading-none tabular-nums ${k === "ours" ? "font-semibold" : "text-quiet"}`}>{r[k].toFixed(1)}%</span>
                </div>
              ))}
            </div>
          ))}
        </div>
        <div className="flex flex-[2] flex-col justify-center gap-6">
          <Rise delay={1.3}>
            <div className="bg-reonic flex flex-col gap-4 rounded-3xl p-11 text-ink">
              <p className="text-[128px] leading-none font-semibold tracking-[-0.04em]">+17 pts</p>
              <p className="text-[36px] leading-[1.2] font-semibold">on PV size, against the installer’s own habit.</p>
              <p className="text-[26px] leading-[1.35]">On the whole design: on par.</p>
            </div>
          </Rise>
          <Rise delay={1.6}>
            <div className="flex flex-col gap-3 rounded-3xl border border-zinc-200 bg-paper p-9">
              <p className="text-[56px] leading-none font-semibold tracking-[-0.03em] tabular-nums">
                {EVAL.roof.from}% → {EVAL.roof.to}%
              </p>
              <p className="text-[26px] leading-[1.35] text-body">whole design right once the roof is known. That’s why it asks.</p>
            </div>
          </Rise>
        </div>
      </div>
      <Source>325 projects from 2026 the model never saw · Roof: best case</Source>
    </Canvas>
  );
}

const WINNERS: [IconName, string, string][] = [
  ["clock", "Planner", "A first draft in under a second."],
  ["users", "Installer", "Juniors design like seniors."],
  ["present", "Homeowner", "An offer that explains itself."],
];

function Value() {
  return (
    <Canvas n={8}>
      <Rise>
        <Eyebrow>Who wins</Eyebrow>
      </Rise>
      <div className="flex flex-1 gap-8">
        {WINNERS.map(([icon, h, big], i) => (
          <Rise key={h} delay={0.15 + i * 0.15} className="flex flex-1">
            <div className="flex flex-1 flex-col gap-8 rounded-3xl border border-zinc-200 bg-sand p-12">
              <div className="flex size-24 items-center justify-center rounded-full bg-paper ring-1 ring-zinc-200">
                <Icon name={icon} className="size-12 text-blue-600" />
              </div>
              <h3 className="text-[36px] font-semibold text-quiet">{h}</h3>
              <p className="mt-auto text-[64px] leading-[1.08] font-semibold tracking-[-0.02em]">{big}</p>
            </div>
          </Rise>
        ))}
      </div>
    </Canvas>
  );
}

function Close() {
  return (
    <Canvas tone="dark">
      <div className="flex flex-1 flex-col justify-center gap-14">
        <Rise className="text-paper">
          <RhythmMark className="size-28" />
        </Rise>
        <Rise delay={0.4}>
          <h2 className="w-[1600px] text-[140px] leading-[1.03] font-semibold tracking-[-0.035em]">
            Great planners don’t guess. <Mint>They ask.</Mint>
          </h2>
        </Rise>
        <Rise delay={0.9}>
          <p className="text-[52px] font-semibold">Rhythm and his dancers</p>
        </Rise>
      </div>
    </Canvas>
  );
}

// -- the deck ---------------------------------------------------------------------------------------------------
// Story: hook, unsolvable problem, turn, how, live demo (planner, offer), honest proof, value, close. About 220 s in total.
export const SLIDES: Slide[] = [
  {
    kind: "content",
    id: "hook",
    title: "Eight days for an offer",
    notes:
      "Hook, ~10 s. Die Linie laufen lassen, dann: „Eine Familie will Solar. Sie wartet 8,2 Tage auf ein Angebot, im Median bei Installateur 1 (Durchlaufzeit, nicht Arbeitszeit; n=260; nicht auf die Folie, nur bei Rückfrage). Am anderen Ende sitzt eine Planerin mit Dutzenden Anfragen.“ Teamnamen nennen: Rhythm and his dancers. Produkt: Rhythm.",
    body: () => <Hook />,
  },
  {
    kind: "content",
    id: "problem",
    title: "Why prediction alone fails",
    notes:
      "Problem, ~20 s. „Wir haben 1.593 echte Projekte mit Expertendesign angeschaut. Bei fast gleichen Häusern (4.000 bis 5.000 kWh, kein E-Auto, keine PV; n=215) installieren Experten zwischen 6,3 und 12,4 kWp, also fast das Doppelte. Warum? Dachfläche und Budget stehen nicht in den Daten. ‚Einfach vorhersagen‘ kann das nicht lösen.“ Nicht „Decke“ oder „Obergrenze für jedes Modell“ sagen, das ist nicht bewiesen.",
    body: () => <Problem />,
  },
  {
    kind: "content",
    id: "turn",
    title: "A designer that asks",
    notes:
      "Wendepunkt, ~15 s. Langsam sprechen: „Also haben wir einen Designer gebaut, der weiß, was er nicht weiß, und fragt.“ Auf die Karte zeigen: Genau so sieht das im Produkt aus. Kein Sprachmodell legt aus; es darf nur formulieren, alles läuft ohne API-Key.",
    body: () => <Turn />,
  },
  {
    kind: "content",
    id: "how",
    title: "How it works",
    notes:
      "Wie, ~15 s. Von links nach rechts: Fakten zum Haus, gelernte Gewohnheit des Installateurs, stündliche Simulation eines Jahres, Regeln und Katalog. Raus kommt ein komplettes Design mit Bandbreiten, Gründen, Warnungen und der Frage, die am meisten ändert. Danach direkt in die Live-Demo.",
    body: () => <How />,
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
        hint: "The proof is on the next slide: 325 unseen 2026 projects (details in /lab).",
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
      { label: "The offer", hint: "Plain words, the house, and only the options the planner allowed. Try the heat-pump option." },
    ],
  },
  {
    kind: "content",
    id: "proof",
    title: "Honest proof",
    notes:
      "Beweis, ~25 s, ehrlich. Test: 325 Projekte aus 2026, nie für Training oder Modellwahl benutzt (das Lab zählt jeden Blick darauf). „Bei der PV-Größe sind wir 17 Punkte besser als die Gewohnheit des Installateurs selbst: 59,7 gegen 42,5 Prozent innerhalb ±20 %. Beim ganzen Design gleichauf (22,2 gegen 20,6 Prozent, im Rauschen). Nur bei Rückfrage: Speicher 48,9 gegen 47,4 Prozent. Und wenn das Dach bekannt ist, steigt das Gesamtdesign auf bis zu 33,2 Prozent. Das ist eine Obergrenze, gemessen mit der Modulzahl des Experten, deshalb fragt Rhythm danach.“ Nicht „einmal bewertet“ sagen.",
    body: () => <Proof />,
  },
  {
    kind: "content",
    id: "value",
    title: "Who wins",
    notes:
      "Wert, ~20 s. „Planer: ein vollständiger Entwurf in unter einer Sekunde, Warnungen vor dem Versand. Installateur: Junioren planen wie die eigenen Senioren. Hausbesitzer: ein Link, der das Angebot erklärt. Bei Rückfrage: Wie viele Stunden das pro Angebot spart, wissen wir nicht, das müssen wir von Reonic erfahren. Wir erfinden keine Zahl.“",
    body: () => <Value />,
  },
  {
    kind: "content",
    id: "close",
    title: "Rhythm and his dancers",
    notes:
      "Schluss mit Energie, ~10 s. „Gute Planer raten nicht, sie fragen. Rhythm fragt für sie.“ Pause. „Wir sind Rhythm and his dancers. Danke.“ Bei Fragen: docs/PITCH.md, Abschnitt Jury-Fragen. Grenzen ehrlich nennen: zwei Installateure, Wärmepumpe in unter 1 % der Designs (13 von 1.593), Dachgröße fehlt, Stückliste vorläufig.",
    body: () => <Close />,
  },
];

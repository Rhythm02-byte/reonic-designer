"use client";
// /pitch: the website as a slide deck. Content slides are a scaled 1920×1080 canvas; live slides show the real
// planner and offer pages in same-origin iframes that stay fully usable. → / PageDown steps through the demo by
// sending the planner a prepared plan (lib/pitch.ts); anything clicked by hand in between simply stays.
// Keys: → Space PageDown next · ← PageUp back · N notes · O overview · H hide bar · F fullscreen · D demo data · ? help
import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { api } from "@/lib/api";
import { buildOptions, encodeOffer } from "@/lib/offer";
import type { PitchPlan } from "@/lib/pitch";
import type { Target } from "@/lib/types";
import { SLIDES, WITH_EV, type Frame, type LiveSlide, type Plan } from "./slides";

type Pos = { s: number; k: number };
const FRAMES: Frame[] = ["planner", "offer"];
const stepsOf = (i: number) => {
  const sl = SLIDES[i];
  return sl.kind === "live" ? sl.steps.length : 1;
};

function parseHash(): Pos {
  const m = /^#(\d+)(?:\.(\d+))?$/.exec(window.location.hash);
  if (!m) return { s: 0, k: 0 };
  const s = Math.min(Math.max(Number(m[1]) - 1, 0), SLIDES.length - 1);
  return { s, k: Math.min(Math.max(Number(m[2] ?? 1) - 1, 0), stepsOf(s) - 1) };
}

/** The plan a live step shows: its own, or the last earlier step's (a step may only be a hint). */
function planAt(sl: LiveSlide, k: number): { plan: Plan; own: boolean } | null {
  for (let i = k; i >= 0; i--) {
    const plan = sl.steps[i].plan;
    if (plan) return { plan, own: i === k };
  }
  return null;
}

const isTyping = (t: EventTarget | null) =>
  t instanceof HTMLElement && (t.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(t.tagName));

const mmss = (ms: number) => {
  const s = Math.max(0, Math.floor(ms / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

const noSubscribe = () => () => {};
const isBrowser = typeof window !== "undefined";

export default function Pitch() {
  // The server renders an empty stage; everything depends on the browser (URL, window size).
  const mounted = useSyncExternalStore(noSubscribe, () => true, () => false);
  const demo = useSyncExternalStore(noSubscribe, () => new URLSearchParams(window.location.search).get("demo") === "1", () => false);
  const [pos, setPos] = useState<Pos>(() => (isBrowser ? parseHash() : { s: 0, k: 0 }));
  const [panel, setPanel] = useState<"notes" | "overview" | "help" | null>(null);
  const [bar, setBar] = useState(true);
  const fitScale = () => (isBrowser ? Math.min(window.innerWidth / 1920, window.innerHeight / 1080) : 1);
  const [scale, setScale] = useState(fitScale);
  const [installer, setInstaller] = useState<string | null>(null);
  const [offerCode, setOfferCode] = useState<string | null>(null);
  // The talk timer starts with the first tick in the browser (no clock reads during render).
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [now, setNow] = useState(0);

  const frames = useRef<Record<Frame, HTMLIFrameElement | null>>({ planner: null, offer: null });
  const ready = useRef<Record<Frame, boolean>>({ planner: false, offer: false });
  const queued = useRef<PitchPlan | null>(null);
  const last = useRef<Pos>({ s: -1, k: -1 });

  // -- position, keyboard, scaling --------------------------------------------------------------------------------
  useEffect(() => {
    const fit = () => setScale(Math.min(window.innerWidth / 1920, window.innerHeight / 1080));
    // Typing a slide number into the URL (#7) or using browser back/forward jumps there.
    const onHash = () => setPos(parseHash());
    window.addEventListener("resize", fit);
    window.addEventListener("hashchange", onHash);
    const tick = setInterval(() => {
      const t = Date.now();
      setNow(t);
      setStartedAt((s) => s ?? t);
    }, 1000);
    return () => {
      window.removeEventListener("resize", fit);
      window.removeEventListener("hashchange", onHash);
      clearInterval(tick);
    };
  }, []);

  useEffect(() => {
    if (!mounted) return;
    const hash = `#${pos.s + 1}${stepsOf(pos.s) > 1 ? `.${pos.k + 1}` : ""}`;
    if (window.location.hash !== hash) window.history.replaceState(null, "", hash);
  }, [pos, mounted]);

  const next = useCallback(
    () =>
      setPos((p) => {
        if (p.k < stepsOf(p.s) - 1) return { s: p.s, k: p.k + 1 };
        return p.s < SLIDES.length - 1 ? { s: p.s + 1, k: 0 } : p;
      }),
    [],
  );
  const prev = useCallback(
    () =>
      setPos((p) => {
        if (p.k > 0) return { s: p.s, k: p.k - 1 };
        return p.s > 0 ? { s: p.s - 1, k: stepsOf(p.s - 1) - 1 } : p;
      }),
    [],
  );

  const toggleDemo = useCallback(() => {
    const url = new URL(window.location.href);
    if (url.searchParams.get("demo") === "1") url.searchParams.delete("demo");
    else url.searchParams.set("demo", "1");
    window.location.href = url.toString();
  }, []);

  const onKey = useCallback(
    (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey || isTyping(e.target)) return;
      const k = e.key;
      if (k === "ArrowRight" || k === "PageDown" || k === " ") next();
      else if (k === "ArrowLeft" || k === "PageUp") prev();
      else if (k === "Home") setPos({ s: 0, k: 0 });
      else if (k === "End") setPos({ s: SLIDES.length - 1, k: 0 });
      else if (k === "n" || k === "N") setPanel((x) => (x === "notes" ? null : "notes"));
      else if (k === "o" || k === "O") setPanel((x) => (x === "overview" ? null : "overview"));
      else if (k === "?") setPanel((x) => (x === "help" ? null : "help"));
      else if (k === "h" || k === "H") setBar((b) => !b);
      else if (k === "d" || k === "D") toggleDemo();
      else if (k === "f" || k === "F") {
        if (document.fullscreenElement) void document.exitFullscreen();
        else void document.documentElement.requestFullscreen().catch(() => {});
      } else if (k === "Escape") setPanel(null);
      else return;
      e.preventDefault();
    },
    [next, prev, toggleDemo],
  );
  useEffect(() => {
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onKey]);

  // -- live data: installer style and the homeowner link -----------------------------------------------------------
  useEffect(() => {
    if (!mounted) return;
    let live = true;
    (async () => {
      const { data: meta } = await api.meta();
      const id = meta.installers[0] ?? WITH_EV.installerId;
      const inputs = { ...WITH_EV, installerId: id };
      const { data: design } = await api.design(inputs, {});
      const catalogs = Object.fromEntries(meta.targets.map((t) => [t.name, t.catalog])) as Record<Target, number[]>;
      if (!live) return;
      setInstaller(id);
      setOfferCode(encodeOffer({ v: 2, inputs, recommended: design.sizes, options: buildOptions(design.sizes, catalogs) }));
    })().catch(() => live && setInstaller(WITH_EV.installerId));
    return () => {
      live = false;
    };
  }, [mounted]);

  // -- driving the planner -----------------------------------------------------------------------------------------
  const send = useCallback((msg: PitchPlan) => {
    const w = frames.current.planner?.contentWindow;
    if (ready.current.planner && w) w.postMessage(msg, window.location.origin);
    else queued.current = msg;
  }, []);

  useEffect(() => {
    if (!mounted || installer === null) return;
    const sl = SLIDES[pos.s];
    const from = last.current;
    last.current = pos;
    if (sl.kind !== "live" || sl.frame !== "planner") return;
    const focus = sl.steps[pos.k].focus;
    // Scroll the live page to where this step's result shows, once the new design has rendered.
    const scroll = focus
      ? setTimeout(() => {
          const win = frames.current.planner?.contentWindow;
          if (!win) return;
          if (focus === "top") win.scrollTo({ top: 0, behavior: "smooth" });
          else win.document.querySelector(focus)?.scrollIntoView({ behavior: "smooth", block: "center" });
        }, 900)
      : undefined;
    const at = planAt(sl, pos.k);
    if (!at) return () => clearTimeout(scroll);
    // Only a single step forward is a "planner change" with a diff bar; jumps and steps back just set the state.
    const forward = from.s === pos.s && from.k === pos.k - 1 && at.own;
    const { plan } = at;
    send({
      type: "pitch:plan",
      inputs: { ...plan.inputs, installerId: installer },
      locked: plan.locked,
      because: forward ? plan.because : undefined,
    });
    return () => clearTimeout(scroll);
  }, [pos, mounted, installer, send]);

  const onFrameLoad = (f: Frame) => {
    ready.current[f] = true;
    const win = frames.current[f]?.contentWindow;
    // A presenter remote sends PageDown/PageUp; those keep working while the focus is inside the app.
    win?.addEventListener("keydown", (e) => {
      const fwd = e.key === "PageDown" || (e.altKey && e.key === "ArrowRight");
      const back = e.key === "PageUp" || (e.altKey && e.key === "ArrowLeft");
      if (!fwd && !back) return;
      e.preventDefault();
      if (fwd) next();
      else prev();
    });
    if (f === "planner") {
      // Give the page a moment to hydrate and register its listener, then send what is waiting.
      setTimeout(() => {
        const msg = queued.current;
        queued.current = null;
        if (msg) frames.current.planner?.contentWindow?.postMessage(msg, window.location.origin);
      }, 600);
    }
  };

  if (!mounted) return <div className="fixed inset-0 bg-zinc-950" />;

  const slide = SLIDES[pos.s];
  const live = slide.kind === "live" ? slide : null;
  const q = demo ? "?demo=1" : "";
  const src: Record<Frame, string | null> = { planner: `/${q}`, offer: offerCode ? `/offer${q}#${offerCode}` : null };
  const nextTitle = SLIDES[pos.s + 1]?.title;

  return (
    <div className="fixed inset-0 overflow-hidden bg-zinc-950 font-sans">
      {/* Live frames stay mounted (and keep their state) for the whole pitch; only the current one is visible. */}
      <div className={`absolute inset-x-0 bottom-0 ${live && bar ? "top-[88px]" : "top-0"}`}>
        {FRAMES.map((f) =>
          src[f] ? (
            <iframe
              key={`${f}-${demo}`}
              ref={(el) => {
                frames.current[f] = el;
              }}
              src={src[f]!}
              title={f === "planner" ? "Planner (live)" : "Homeowner offer (live)"}
              onLoad={() => onFrameLoad(f)}
              className={`absolute inset-0 h-full w-full border-0 bg-paper ${live?.frame === f ? "" : "pointer-events-none invisible"}`}
            />
          ) : null,
        )}
      </div>

      {live ? (
        bar && <LiveBar slide={live} pos={pos} demo={demo} setStep={(k) => setPos({ s: pos.s, k })} onPrev={prev} onNext={next} onPanel={setPanel} />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center">
          <div
            style={{ width: 1920, height: 1080, transform: `scale(${scale})` }}
            className="shrink-0 overflow-hidden bg-paper"
            onClick={(e) => (e.clientX > window.innerWidth / 3 ? next() : prev())}
          >
            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={slide.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.18 }}
                className="h-full w-full"
              >
                {slide.kind === "content" && slide.body()}
              </motion.div>
            </AnimatePresence>
          </div>
          <div className="absolute inset-x-0 bottom-0 h-1 bg-black/10">
            <div className="h-full bg-ink/60 transition-[width]" style={{ width: `${((pos.s + 1) / SLIDES.length) * 100}%` }} />
          </div>
          <div className="group absolute right-0 bottom-0 flex items-center gap-1 p-3 opacity-0 transition-opacity hover:opacity-100">
            <NavButton label="Previous" onClick={prev}>‹</NavButton>
            <span className="rounded-full bg-ink/80 px-3 py-1 text-xs text-paper tabular-nums">
              {pos.s + 1} / {SLIDES.length} · ? keys
            </span>
            <NavButton label="Next" onClick={next}>›</NavButton>
          </div>
        </div>
      )}

      {panel === "notes" && (
        <div className="absolute inset-x-0 bottom-0 z-30 max-h-[45vh] overflow-auto border-t border-white/10 bg-zinc-900/95 px-8 py-5 text-zinc-100 backdrop-blur">
          <div className="mb-2 flex items-center gap-4 text-sm text-zinc-400">
            <span className="font-semibold text-zinc-100">
              {pos.s + 1}. {slide.title}
            </span>
            {live && <span>Step {pos.k + 1} of {live.steps.length}</span>}
            <span className="ml-auto tabular-nums">{mmss(now - (startedAt ?? now))}</span>
            <button className="underline underline-offset-2" onClick={() => setStartedAt(Date.now())}>
              Reset timer
            </button>
          </div>
          <p className="max-w-[110ch] text-lg leading-relaxed">{slide.notes}</p>
          {nextTitle && <p className="mt-3 text-sm text-zinc-400">Next: {nextTitle}</p>}
        </div>
      )}

      {panel === "overview" && (
        <div className="absolute inset-0 z-40 overflow-auto bg-zinc-950/90 p-10 backdrop-blur" onClick={() => setPanel(null)}>
          <div className="mx-auto grid max-w-6xl grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {SLIDES.map((s, i) => (
              <button
                key={s.id}
                onClick={() => {
                  setPos({ s: i, k: 0 });
                  setPanel(null);
                }}
                className={`flex aspect-video flex-col justify-between rounded-xl p-4 text-left ring-1 ${
                  i === pos.s ? "bg-paper text-ink ring-orange-400" : "bg-zinc-900 text-zinc-100 ring-white/10 hover:bg-zinc-800"
                }`}
              >
                <span className="text-xs tabular-nums opacity-70">
                  {i + 1} {s.kind === "live" ? "· LIVE" : ""}
                </span>
                <span className="text-base font-semibold">{s.title}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {panel === "help" && (
        <div className="absolute inset-0 z-40 flex items-center justify-center bg-zinc-950/80" onClick={() => setPanel(null)}>
          <div className="w-[min(560px,90vw)] rounded-2xl bg-paper p-8 text-ink">
            <h2 className="mb-4 text-xl font-semibold">Pitch keys</h2>
            <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
              {[
                ["→  Space  PageDown", "Next step or slide (PageDown also works inside the app)"],
                ["←  PageUp", "Back"],
                ["N", "Speaker notes and timer"],
                ["O", "Overview, jump to any slide"],
                ["H", "Hide the bar on live slides"],
                ["F", "Fullscreen"],
                ["D", `Demo data ${demo ? "off (use the engine)" : "on (no engine needed)"}`],
                ["Esc", "Close this"],
              ].map(([k, v]) => (
                <div key={k} className="contents">
                  <dt className="font-mono text-quiet">{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-4 text-xs text-muted">Click into the live app to use it; arrow keys then belong to the app. Click the bar to get them back.</p>
          </div>
        </div>
      )}
    </div>
  );
}

function NavButton({ label, onClick, children }: { label: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      aria-label={label}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className="grid size-8 place-items-center rounded-full bg-ink/80 text-lg leading-none text-paper hover:bg-ink"
    >
      {children}
    </button>
  );
}

function LiveBar({
  slide,
  pos,
  demo,
  setStep,
  onPrev,
  onNext,
  onPanel,
}: {
  slide: LiveSlide;
  pos: Pos;
  demo: boolean;
  setStep: (k: number) => void;
  onPrev: () => void;
  onNext: () => void;
  onPanel: (p: "notes" | "overview" | "help") => void;
}) {
  const step = slide.steps[pos.k];
  return (
    <div className="absolute inset-x-0 top-0 z-20 flex h-[88px] flex-col justify-center gap-1.5 border-b border-white/10 bg-aubergine px-5 text-paper">
      <div className="flex items-center gap-3">
        <span className="rounded-full bg-orange-300 px-2.5 py-0.5 text-[11px] font-bold tracking-wider text-ink uppercase">Live</span>
        <span className="text-sm font-semibold">
          {pos.s + 1}. {slide.title}
        </span>
        {slide.steps.length > 1 && (
          <ol className="ml-2 flex flex-wrap items-center gap-1.5" aria-label="Demo steps">
            {slide.steps.map((s, i) => (
              <li key={s.label}>
                <button
                  onClick={() => setStep(i)}
                  aria-current={i === pos.k ? "step" : undefined}
                  className={`rounded-full px-3 py-1 text-xs font-medium ring-1 transition-colors ${
                    i === pos.k ? "bg-paper text-ink ring-paper" : i < pos.k ? "text-zinc-200 ring-white/30 hover:bg-white/10" : "text-zinc-400 ring-white/15 hover:bg-white/10"
                  }`}
                >
                  {i + 1} · {s.label}
                </button>
              </li>
            ))}
          </ol>
        )}
        <div className="ml-auto flex items-center gap-2">
          {demo && <span className="rounded-full bg-amber-200 px-2.5 py-0.5 text-[11px] font-semibold text-amber-950">Demo data</span>}
          <BarButton onClick={() => onPanel("notes")}>Notes</BarButton>
          <BarButton onClick={() => onPanel("overview")}>Slides</BarButton>
          <BarButton onClick={() => onPanel("help")}>?</BarButton>
          <NavButton label="Previous" onClick={onPrev}>‹</NavButton>
          <NavButton label="Next" onClick={onNext}>›</NavButton>
        </div>
      </div>
      <p className="truncate text-sm text-zinc-300">{step.hint}</p>
    </div>
  );
}

function BarButton({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick} className="rounded-full px-3 py-1 text-xs font-medium text-zinc-200 ring-1 ring-white/20 hover:bg-white/10">
      {children}
    </button>
  );
}

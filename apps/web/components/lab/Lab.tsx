"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button, Card, ErrorNote, Header, Logo, Segmented } from "@/components/ui";
import { MODELS, fmt, latestWith, pts, scored, when, type Run, type Scores } from "@/lib/lab";

const WIDTH = "max-w-5xl";
const NOISE = 2; // points; one validation project is ~0.4 pt, repeated-split sd ~2 pt
const BRANCH_COLOURS = ["#2563eb", "#059669", "#d97706", "#7c3aed", "#db2777"];
type Metric = "ems" | "wholeDesign";
const RATE: Record<Metric, boolean> = { ems: false, wholeDesign: true };

export default function Lab({ runs, invalid, canRun }: { runs: Run[]; invalid: number; canRun: boolean }) {
  const [metric, setMetric] = useState<Metric>("wholeDesign");
  const series = scored(runs);
  const last = series.at(-1);
  const lastAll = [...runs].reverse().find((r) => r.kind === "all");

  return (
    <div className="flex min-h-dvh flex-col">
      <Header width={WIDTH}>
        <Link href="/" className="rounded-lg">
          <Logo />
        </Link>
        <span className="rounded-full bg-sand px-2.5 py-0.5 text-xs font-medium text-quiet ring-1 ring-zinc-200">Test Lab</span>
      </Header>
      <main className={`mx-auto w-full flex-1 space-y-6 px-4 py-8 sm:px-6 ${WIDTH}`}>
        {invalid > 0 && <p className="text-sm text-amber-900">{invalid} unreadable line(s) in the run history were skipped.</p>}
        <Headline series={series} />
        {canRun && <RunAll minutes={lastAll?.durationSec ? Math.max(1, Math.round(lastAll.durationSec / 60)) : null} />}
        {series.length > 0 && (
          <Card className="p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold tracking-tight text-ink">Over time, per branch</h2>
              <Segmented name="metric" label="Measure" value={metric} onChange={setMetric}
                options={[{ value: "wholeDesign", label: "Whole design" }, { value: "ems", label: "Closeness" }]} />
            </div>
            <Timeline runs={series} metric={metric} />
          </Card>
        )}
        {last && (
          <details className="group rounded-2xl border border-zinc-200 bg-white">
            <summary className="cursor-pointer list-none px-5 py-4 text-sm font-medium text-ink">
              Details: all numbers, honesty checks, 2026 exam <span className="text-muted group-open:hidden">▸</span>
            </summary>
            <div className="space-y-6 px-1 pb-1">
              <Compare run={last} />
              <Honesty runs={runs} />
              <History runs={runs} />
            </div>
          </details>
        )}
      </main>
    </div>
  );
}

function Headline({ series }: { series: Run[] }) {
  const last = series.at(-1), prev = series.at(-2);
  const ours = last?.validation?.models.ours, b0 = last?.validation?.models.B0;
  if (!ours) return <h1 className="text-3xl font-semibold tracking-tight text-ink">No test runs yet</h1>;
  const d = prev?.validation?.models.ours?.wholeDesign != null && ours.wholeDesign != null
    ? (ours.wholeDesign - prev.validation!.models.ours.wholeDesign!) * 100 : null;
  return (
    <section>
      <p className="text-sm text-muted" title="PV within ±20%, battery and heat pump within ±25%, wallbox yes/no: all four must match the expert">
        Homes where all four parts match the expert
      </p>
      <h1 className="mt-1 text-5xl font-semibold tracking-tight text-ink tabular-nums">
        <span className="text-reonic">{fmt(ours.wholeDesign, true)}</span>
      </h1>
      <p className="mt-2 text-base">
        {d == null ? "First run." : Math.abs(d) < NOISE ? `Same as the last run (${d >= 0 ? "+" : ""}${d.toFixed(1)}, within noise).`
          : d > 0 ? `▲ ${d.toFixed(1)} points better than the last run.` : `▼ ${(-d).toFixed(1)} points worse than the last run.`}{" "}
        <span className="text-muted">Copying the installer&apos;s usual design: {fmt(b0?.wholeDesign, true)}.</span>
      </p>
    </section>
  );
}

function RunAll({ minutes }: { minutes: number | null }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [sec, setSec] = useState(0);
  const [label, setLabel] = useState("");
  const [msg, setMsg] = useState<{ error?: string; tail?: string } | null>(null);
  useEffect(() => {
    if (!busy) return;
    const t = setInterval(() => setSec((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [busy]);

  async function run() {
    setBusy(true);
    setSec(0);
    setMsg(null);
    const r = await fetch("/lab/run", { method: "POST", body: JSON.stringify({ label }) })
      .then((x) => x.json())
      .catch((e: Error) => ({ error: e.message }));
    setBusy(false);
    setMsg(r.error ? r : null);
    if (!r.error) {
      setLabel("");
      router.refresh();
    }
  }
  const clock = `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}`;

  return (
    <Card className="flex flex-wrap items-center gap-3 p-4">
      <input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="What changed? (optional)" maxLength={80}
        aria-label="What changed in this run"
        className="min-w-0 flex-1 rounded-full bg-sand px-4 py-1.5 text-sm text-ink ring-1 ring-zinc-200 placeholder:text-muted focus-visible:outline-2 focus-visible:outline-blue-600 pointer-coarse:min-h-11" />
      <Button disabled={busy} onClick={run}>{busy ? `Running all tests… ${clock}` : `Run all tests${minutes ? ` (~${minutes} min)` : ""}`}</Button>
      {msg?.error && (
        <div className="w-full space-y-2">
          <ErrorNote error={msg.error} />
          {msg.tail && <pre className="overflow-x-auto rounded-xl bg-sand p-3 text-xs">{msg.tail}</pre>}
        </div>
      )}
    </Card>
  );
}

function Timeline({ runs, metric }: { runs: Run[]; metric: Metric }) {
  const rate = RATE[metric];
  const branches = [...new Set(runs.map((r) => r.git.branch))];
  const values = runs.flatMap((r) => [r.validation!.models.ours?.[metric], r.validation!.models.B0?.[metric]]).map((v) => pts(v, rate) ?? NaN).filter(Number.isFinite);
  const lo = Math.floor((Math.min(...values) - 3) / 5) * 5, hi = Math.ceil((Math.max(...values) + 3) / 5) * 5;
  const W = 720, H = 220, L = 40, R = 12, T = 10, B = 24;
  const x = (i: number) => (runs.length === 1 ? (L + W - R) / 2 : L + (i / (runs.length - 1)) * (W - L - R));
  const y = (v: number) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
  const ticks = Array.from({ length: (hi - lo) / 5 + 1 }, (_, i) => lo + i * 5).filter((_, i, a) => a.length <= 7 || i % 2 === 0);
  const line = (pick: (r: Run) => number | undefined, branch?: string) =>
    runs.map((r, i) => ({ r, i, v: pts(pick(r), rate) })).filter((p) => p.v != null && (!branch || p.r.git.branch === branch));

  return (
    <figure>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full text-xs" role="img" aria-label={`${metric === "ems" ? "Expert match" : "Whole design %"} per run, by branch; dashed line is the installer's usual design`}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} className="stroke-zinc-200" />
            <text x={L - 6} y={y(t) + 4} textAnchor="end" className="fill-zinc-500">{t}</text>
          </g>
        ))}
        <polyline fill="none" className="stroke-zinc-400" strokeDasharray="5 5" strokeWidth={1.5}
          points={line((r) => r.validation!.models.B0?.[metric]).map((p) => `${x(p.i)},${y(p.v!)}`).join(" ")} />
        {line((r) => r.validation!.models.B0?.[metric]).map((p) => (
          <line key={p.r.id} x1={x(p.i) - 5} x2={x(p.i) + 5} y1={y(p.v!)} y2={y(p.v!)} className="stroke-zinc-400" strokeWidth={2}>
            <title>{`installer's usual design · ${p.v!.toFixed(1)}`}</title>
          </line>
        ))}
        {branches.map((b, bi) => {
          const pts_ = line((r) => r.validation!.models.ours?.[metric], b);
          const c = BRANCH_COLOURS[bi % BRANCH_COLOURS.length];
          return (
            <g key={b}>
              <polyline fill="none" stroke={c} strokeWidth={2} points={pts_.map((p) => `${x(p.i)},${y(p.v!)}`).join(" ")} />
              {pts_.map((p) => (
                <circle key={p.r.id} cx={x(p.i)} cy={y(p.v!)} r={4} fill="white" stroke={c} strokeWidth={2}>
                  <title>{`${b} · ${when(p.r.timestamp)} · ${p.v!.toFixed(1)}${p.r.label ? ` · ${p.r.label}` : ""}`}</title>
                </circle>
              ))}
            </g>
          );
        })}
      </svg>
      <figcaption className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
        {branches.map((b, bi) => (
          <span key={b} className="flex items-center gap-1.5">
            <span className="h-0.5 w-4" style={{ background: BRANCH_COLOURS[bi % BRANCH_COLOURS.length] }} /> {b}
          </span>
        ))}
        <span className="flex items-center gap-1.5"><span className="w-4 border-t-2 border-dashed border-zinc-400" /> installer&apos;s usual design</span>
        <span>Validation window, one point per run.</span>
      </figcaption>
    </figure>
  );
}

const COLS: { key: keyof Scores; label: string; rate: boolean; low?: boolean }[] = [
  { key: "wholeDesign", label: "Whole design", rate: true },
  { key: "ems", label: "Expert match", rate: false },
  { key: "pv", label: "PV ±20%", rate: true },
  { key: "battery", label: "Battery ±25%", rate: true },
  { key: "latencyP50ms", label: "ms / home", rate: false, low: true },
];

function Compare({ run }: { run: Run }) {
  const blocks = [["Validation (Q4 2025)", run.validation], ["2026 test", run.test]] as const;
  return (
    <Card className="overflow-x-auto">
      <table className="w-full text-left text-sm tabular-nums">
        <caption className="px-4 pt-4 text-left text-lg font-semibold tracking-tight text-ink">Latest run, {when(run.timestamp)}</caption>
        <thead className="text-xs text-muted">
          <tr>
            <th scope="col" className="px-4 py-2 font-medium">Model</th>
            {COLS.map((c) => <th key={c.key} scope="col" className="px-4 py-2 font-medium">{c.label}</th>)}
          </tr>
        </thead>
        {blocks.map(([title, b]) => b && (
          <tbody key={title} className="divide-y divide-zinc-200 border-t border-zinc-200">
            <tr><th colSpan={COLS.length + 1} scope="colgroup" className="bg-sand-2 px-4 py-1.5 text-xs font-medium text-quiet">{title}, n={b.n}</th></tr>
            {MODELS.map((m) => (
              <tr key={m.key}>
                <th scope="row" className={`px-4 py-2 font-medium ${m.key === "ours" ? "text-ink" : ""}`}>{m.name}</th>
                {COLS.map((c) => {
                  const vals = MODELS.map((o) => b.models[o.key]?.[c.key]).filter((v): v is number => v != null);
                  const v = b.models[m.key]?.[c.key];
                  const best = v != null && v === (c.low ? Math.min(...vals) : Math.max(...vals));
                  return <td key={c.key} className={`px-4 py-2 ${best ? "font-semibold text-ink" : ""}`}>{fmt(v, c.rate, c.low ? 2 : 1)}</td>;
                })}
              </tr>
            ))}
          </tbody>
        ))}
      </table>
    </Card>
  );
}

function Honesty({ runs }: { runs: Run[] }) {
  const honest = latestWith(runs, "honesty"), oracle = latestWith(runs, "oracle");
  const tests = runs.filter((r) => r.testScored).length;
  const h = honest?.honesty, gap = (honest ?? oracle)?.repeated?.gap, roof = oracle?.oracle?.roof, demand = oracle?.oracle?.demand;
  const items = [
    h?.shuffledWhole != null && `Shuffled answers drop whole design from ${fmt(h.realWhole, true)} to ${fmt(h.shuffledWhole, true)}, so the model learns real signal.`,
    gap?.mean != null && `Over ${gap.n} random splits ours beats the usual design by ${fmt(gap.mean, true)} ± ${fmt(gap.sd, true)}${Math.abs(gap.mean) < (gap.sd ?? 0) ? " (not distinguishable from zero)" : ""}.`,
    h?.fuzzN != null && `${h.fuzzBroken} of ${h.fuzzN} random and extreme homes broke a rule.`,
    demand?.gainWhole != null && `Answering the real annual kWh is worth +${fmt(demand.gainWhole, true)} whole design.`,
    roof?.gainWhole != null && `Answering the roof size is worth +${fmt(roof.gainWhole, true)} (upper bound).`,
    `The 2026 exam has been scored ${tests} time${tests === 1 ? "" : "s"}. We decide on the 2025 numbers, not on it.`,
  ].filter(Boolean) as string[];
  return (
    <Card className="p-5">
      <h2 className="text-lg font-semibold tracking-tight text-ink">Honesty checks</h2>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{items.map((t) => <li key={t}>{t}</li>)}</ul>
    </Card>
  );
}

function History({ runs }: { runs: Run[] }) {
  const rows = [...runs].reverse();
  return (
    <Card className="overflow-x-auto">
      <table className="w-full text-left text-sm tabular-nums">
        <caption className="px-4 pt-4 text-left text-lg font-semibold tracking-tight text-ink">All runs</caption>
        <thead className="text-xs text-muted">
          <tr>{["When", "Branch", "Kind", "Whole design", "Δ vs previous", "Expert match", "Took", "Note"].map((h) => (
            <th key={h} scope="col" className="px-4 py-2 font-medium whitespace-nowrap">{h}</th>
          ))}</tr>
        </thead>
        <tbody className="divide-y divide-zinc-200">
          {rows.map((r) => {
            const v = r.validation?.models.ours;
            const prev = rows.slice(rows.indexOf(r) + 1).find((p) => p.validation?.models.ours);
            const d = v?.wholeDesign != null && prev ? (v.wholeDesign - (prev.validation!.models.ours.wholeDesign ?? 0)) * 100 : null;
            return (
              <tr key={r.id}>
                <td className="px-4 py-2 whitespace-nowrap">{when(r.timestamp)}</td>
                <td className="px-4 py-2 whitespace-nowrap">{r.git.branch}{r.git.commit && <span className="text-muted"> @{r.git.commit}{r.git.dirty ? "*" : ""}</span>}</td>
                <td className="px-4 py-2">{r.kind}{r.testScored && <span className="ml-1.5 rounded-full bg-amber-100 px-1.5 text-xs text-amber-900">2026 test</span>}</td>
                <td className="px-4 py-2">{fmt(v?.wholeDesign, true)}</td>
                <td className="px-4 py-2 whitespace-nowrap">{d == null ? "–" : Math.abs(d) < NOISE ? `${d >= 0 ? "+" : ""}${d.toFixed(1)} (noise)` : `${d > 0 ? "▲ +" : "▼ "}${d.toFixed(1)}`}</td>
                <td className="px-4 py-2">{fmt(v?.ems)}</td>
                <td className="px-4 py-2">{r.durationSec != null ? `${Math.round(r.durationSec)} s` : "–"}</td>
                <td className="px-4 py-2 text-muted">{r.label}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Card>
  );
}

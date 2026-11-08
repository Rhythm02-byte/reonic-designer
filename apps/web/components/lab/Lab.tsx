"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Button, Card, ErrorNote, Header, Logo } from "@/components/ui";
import { MODELS, day, examRun, historyPoints, researchRows, when, type Run, type Scores } from "@/lib/lab";
import type { CheckJob } from "@/lib/lab-jobs";

// ours: only the three metrics people can read at a glance; all other columns removed.
const METRICS: { key: keyof Scores; name: string }[] = [
  { key: "wholeDesign", name: "Whole design" }, { key: "pv", name: "Solar ±20%" }, { key: "battery", name: "Battery ±25%" },
];
const BAR = { B1: "bg-zinc-300", B0: "bg-zinc-500", ours: "bg-blue-600" } as const;
const pct = (v: number | undefined) => (v == null ? "–" : `${(v * 100).toFixed(0)}%`);
const cleanLog = (value: string) => value.replace(/\u001b\[[0-?]*[ -/]*[@-~]/g, "").replace(/\r/g, "");

export default function Lab({ runs, invalid, canRun }: { runs: Run[]; invalid: number; canRun: boolean }) {
  const exam = examRun(runs);
  const m = exam?.test?.models;
  const ours = m?.ours, b0 = m?.B0;
  // ours: verdict computed from the numbers, tie below 2 points.
  const verdict = (a?: number, b?: number) => a == null || b == null ? null : Math.abs(a - b) * 100 < 2 ? "tie" : a > b ? "win" : "loss";
  const vw = verdict(ours?.wholeDesign, b0?.wholeDesign), vp = verdict(ours?.pv, b0?.pv);
  const word = (v: string | null, what: string) => v === "tie" ? `Tie on ${what}` : v === "win" ? `Clear win on ${what}` : v === "loss" ? `Behind on ${what}` : null;
  const verdictLine = [word(vw, "the whole design"), word(vp, "solar")].filter(Boolean).join(", ");
  const rows = researchRows(runs), adopted = rows.filter(r => r.adopted).length;
  const hist = historyPoints(runs);
  const h = [...runs].reverse().find(r => r.kind !== "research" && r.honesty)?.honesty;
  const rep = [...runs].reverse().find(r => r.kind !== "research" && r.repeated)?.repeated;
  return (
    <div className="flex min-h-dvh flex-col">
      <Header width="max-w-3xl"><Link href="/"><Logo /></Link><span className="ml-3 text-sm text-quiet">Test Lab</span></Header>
      <main className="mx-auto w-full max-w-3xl space-y-8 px-4 py-8 sm:px-6">
        {invalid > 0 && <p className="text-sm text-amber-900">{invalid} unreadable history lines were skipped.</p>}
        <section className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
            {ours && b0 && exam?.test?.n != null
              ? `On ${exam.test.n} unseen 2026 homes, the whole design matched the expert ${pct(ours.wholeDesign)} of the time (installer's usual package: ${pct(b0.wholeDesign)}). Solar size: ${pct(ours.pv)} vs ${pct(b0.pv)}.`
              : "No scored run on unseen 2026 homes yet."}
          </h1>
          {verdictLine && <p className="text-base text-quiet">{verdictLine}.</p>}
        </section>

        {m && <Card className="space-y-5 p-5">
          <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-quiet">{MODELS.map(x => <li key={x.key} className="flex items-center gap-1.5"><span className={`inline-block size-2.5 rounded-sm ${BAR[x.key]}`} />{x.name}</li>)}</ul>
          {METRICS.map(c => <div key={c.key} className="space-y-1.5">
            <h2 className="text-sm font-medium text-ink">{c.name}</h2>
            {MODELS.map(x => { const v = m[x.key]?.[c.key]; return <div key={x.key} className="flex items-center gap-3 text-xs tabular-nums">
              <span className="w-28 shrink-0 text-quiet sm:w-40">{x.name}</span>
              <div className="h-3 flex-1 rounded-sm bg-sand-2"><div className={`h-3 rounded-sm ${BAR[x.key]}`} style={{ width: `${Math.min(100, (v ?? 0) * 100)}%` }} /></div>
              <span className="w-10 text-right font-medium text-ink">{pct(v)}</span></div>; })}
          </div>)}
        </Card>}

        <details className="rounded-2xl border border-zinc-200 bg-white p-5">
          <summary className="cursor-pointer text-sm font-medium">Research: {rows.length} settings tested · {adopted} passed the test rule · 1 adopted (battery sized from the catalogue)</summary>
          {rows.length === 0 ? <p className="mt-3 text-sm text-quiet">No research results recorded.</p> : <div className="mt-3 max-h-96 overflow-auto"><table className="w-full text-left text-sm tabular-nums">
            <thead><tr className="text-xs text-quiet"><th className="py-1 pr-3 font-medium">Idea</th><th className="px-3 py-1 text-right font-medium">Gain (points)</th><th className="py-1 pl-3 font-medium">Decision</th></tr></thead>
            <tbody>{rows.map((r, i) => <tr key={`${r.name}-${i}`} className="border-t border-zinc-200"><td className="py-1.5 pr-3">{r.name}</td><td className="px-3 py-1.5 text-right">{r.gain > 0 ? "+" : ""}{r.gain.toFixed(1)}</td><td className={`py-1.5 pl-3 ${r.adopted ? "font-medium text-emerald-800" : "text-quiet"}`}>{r.adopted ? "Passed" : "No effect"}</td></tr>)}</tbody></table></div>}
        </details>

        {hist.length >= 3 && <Card className="space-y-2 p-5"><h2 className="text-sm font-medium text-ink">Whole-design match over time</h2><History points={hist} /></Card>}

        {h && <section className="space-y-3">
          <h2 className="text-sm font-medium text-ink">Honesty checks</h2>
          <div className="flex flex-wrap gap-2">
            <Chip ok={h.realWhole != null && h.shuffledWhole != null && h.shuffledWhole < h.realWhole * 0.6} label="Shuffled labels" />
            <Chip ok={!!rep && rep.gap.mean != null && rep.gap.sd != null && rep.gap.mean - rep.gap.sd > 0} label="Repeated splits" />
            <Chip ok={h.fuzzBroken === 0} label="Fuzz" />
          </div>
          <details className="text-xs text-quiet"><summary className="cursor-pointer">Details</summary><ul className="mt-2 space-y-1">
            {h.realWhole != null && h.shuffledWhole != null && <li>Shuffled labels: real {(h.realWhole * 100).toFixed(1)}% vs shuffled {(h.shuffledWhole * 100).toFixed(1)}%. Passes only if shuffling clearly drops the score.</li>}
            {rep && <li>Repeated splits: ours {((rep.ours.mean ?? 0) * 100).toFixed(1)}% vs installer {((rep.b0.mean ?? 0) * 100).toFixed(1)}%, gap {((rep.gap.mean ?? 0) * 100).toFixed(1)} ± {((rep.gap.sd ?? 0) * 100).toFixed(1)} points. Passes only if the gap beats its spread.</li>}
            {h.fuzzN != null && <li>Fuzz: {h.fuzzBroken ?? 0} of {h.fuzzN} odd inputs broke the design.</li>}
          </ul></details>
        </section>}

        {canRun ? <Checks /> : <p className="text-xs text-quiet">Open this page on localhost to run the tests.</p>}

        <details className="text-xs text-quiet"><summary className="cursor-pointer">All runs ({runs.length})</summary>
          <div className="mt-3 overflow-auto"><table className="w-full text-left"><thead><tr>{["When", "Kind", "Branch", "Note"].map(x => <th key={x} className="px-2 py-1 font-medium">{x}</th>)}</tr></thead><tbody>{[...runs].reverse().map(r => <tr key={r.id} className="border-t border-zinc-200"><td className="px-2 py-1 whitespace-nowrap">{when(r.timestamp)}</td><td className="px-2 py-1">{r.kind}</td><td className="px-2 py-1">{r.git.branch}@{r.git.commit ?? "?"}{r.git.dirty ? "*" : ""}</td><td className="px-2 py-1">{r.label}</td></tr>)}</tbody></table></div>
        </details>
      </main>
    </div>
  );
}

function Chip({ ok, label }: { ok: boolean; label: string }) {
  return <span className={`rounded-full px-3 py-1 text-xs font-medium ring-1 ${ok ? "bg-emerald-50 text-emerald-900 ring-emerald-200" : "bg-amber-50 text-amber-900 ring-amber-200"}`}>{label}: {ok ? "pass" : "watch"}</span>;
}

// ours: simple dated line chart, ours solid and installer's usual package dashed; only rendered with 3+ distinct points.
function History({ points }: { points: ReturnType<typeof historyPoints> }) {
  const all = points.flatMap(p => [p.ours, p.b0 ?? p.ours]);
  const lo = Math.max(0, Math.floor(Math.min(...all) / 5) * 5 - 5), hi = Math.ceil(Math.max(...all) / 5) * 5 + 5;
  const x = (i: number) => 50 + (i / (points.length - 1)) * 640, y = (v: number) => 170 - ((v - lo) / (hi - lo)) * 150;
  const ticks = [lo, (lo + hi) / 2, hi];
  const line = (f: (p: (typeof points)[number]) => number | null) => points.flatMap((p, i) => { const v = f(p); return v == null ? [] : [`${x(i)},${y(v)}`]; }).join(" ");
  const step = Math.ceil(points.length / 6);
  return <div className="space-y-2">
    <svg viewBox="0 0 720 210" className="block w-full" role="img" aria-label="Whole-design match over time, ours versus installer's usual package">
      {ticks.map(v => <g key={v}><line x1="44" x2="704" y1={y(v)} y2={y(v)} stroke="#d4d4d8" strokeDasharray="3 5" /><text x="38" y={y(v) + 4} textAnchor="end" fontSize="12" fill="#71717a">{Math.round(v)}%</text></g>)}
      <polyline points={line(p => p.b0)} fill="none" stroke="#71717a" strokeWidth="2" strokeDasharray="6 4" />
      <polyline points={line(p => p.ours)} fill="none" stroke="#2563eb" strokeWidth="2.5" />
      {points.map((p, i) => <g key={p.t}><circle cx={x(i)} cy={y(p.ours)} r="4" fill="#2563eb" />{i % step === 0 && <text x={x(i)} y="200" textAnchor="middle" fontSize="12" fill="#71717a">{day(p.t)}</text>}</g>)}
    </svg>
    <p className="text-xs text-quiet">Solid: ours. Dashed: installer&apos;s usual package. Validation homes, identical reruns merged.</p>
  </div>;
}

function Checks() {
  const router = useRouter();
  const [job, setJob] = useState<CheckJob | null>(null), [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const finished = useRef<string | null>(null);
  const historyVersion = useRef<number | null>(null);
  useEffect(() => {
    let active = true;
    const poll = () => fetch("/lab/run", { cache: "no-store", signal: AbortSignal.timeout(8000) }).then(async r => {
      if (!r.ok) throw new Error("Cannot read local check status.");
      const data = await r.json();
      if (!active) return;
      setJob(data.job); setError(null);
      if (historyVersion.current !== null && data.historyVersion !== historyVersion.current) router.refresh();
      historyVersion.current = data.historyVersion;
      if (data.job && data.job.state !== "running" && finished.current !== data.job.id) {
        finished.current = data.job.id; router.refresh();
      }
    }).catch(e => { if (active) setError(e.message); });
    void poll(); const timer = setInterval(poll, 3000);
    return () => { active = false; clearInterval(timer); };
  }, [router]);
  async function start() {
    setStarting(true); setError(null);
    try {
      // ours: the 2026 exam option and label input were removed from this page; only the safe development checks start here.
      const r = await fetch("/lab/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode: "checks", confirmTestScoring: false, label: "" }), signal: AbortSignal.timeout(8000) });
      const data = await r.json(); if (!r.ok) throw new Error(data.error ?? "Could not start checks.");
      setJob(data.job);
    } catch (e) { setError(e instanceof Error ? e.message : "Could not start checks."); }
    finally { setStarting(false); }
  }
  const running = job?.state === "running";
  return <section className="space-y-2" role="status" aria-live="polite">
    <div className="flex flex-wrap items-center gap-3">
      <Button disabled={starting || running} onClick={start}>{starting ? "Starting…" : running ? "Running…" : "Run all tests"}</Button>
      {job && <span className={`text-xs ${job.state === "failed" ? "text-rose-800" : "text-quiet"}`}>{running ? `Running: ${job.stage}` : job.state === "failed" ? `Failed at ${job.stage}` : job.state === "passed" ? "Last run passed" : job.state}</span>}
    </div>
    {job?.error && <details><summary className="cursor-pointer text-xs font-medium text-rose-800">Failure details</summary><pre className="mt-2 max-h-72 overflow-auto rounded-lg bg-white p-3 font-mono text-xs text-rose-900 ring-1 ring-rose-200">{cleanLog(job.error).slice(-12000)}</pre></details>}
    <ErrorNote error={error} />
  </section>;
}

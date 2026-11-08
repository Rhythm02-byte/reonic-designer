"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Button, Card, ErrorNote, Header, Logo, Segmented } from "@/components/ui";
import { comparable, fmt, scored, when, type Run, type Scores } from "@/lib/lab";
import type { CheckJob } from "@/lib/lab-jobs";

type Metric = "wholeDesign" | "ems";
const cols: { key: keyof Scores; name: string; rate: boolean }[] = [
  { key: "wholeDesign", name: "Whole design", rate: true }, { key: "pv", name: "PV ±20%", rate: true },
  { key: "battery", name: "Battery ±25%", rate: true }, { key: "heatPump", name: "Heat pump ±25%", rate: true },
  { key: "wallbox", name: "Wallbox", rate: true }, { key: "ems", name: "Closeness", rate: false },
];
const modelName = (name: string) => ({ ours: "Served policy", B0: "Installer median bundle", B1: "Rule of thumb", default: "Current default" })[name] ?? name;
const cleanLog = (value: string) => value.replace(/\u001b\[[0-?]*[ -/]*[@-~]/g, "").replace(/\r/g, "");

export default function Lab({ runs, invalid, canRun }: { runs: Run[]; invalid: number; canRun: boolean }) {
  const [metric, setMetric] = useState<Metric>("wholeDesign");
  const series = scored(runs), latest = series.at(-1);
  const exam = [...runs].reverse().find(r => r.kind !== "research" && r.test?.models.ours);
  const research = runs.filter(r => r.kind === "research").reverse();
  const tests = runs.filter(r => r.testScored).length;
  return (
    <div className="flex min-h-dvh flex-col">
      <Header width="max-w-5xl"><Link href="/"><Logo /></Link><span className="ml-3 text-sm text-quiet">Test Lab</span></Header>
      <main className="mx-auto w-full max-w-5xl space-y-6 px-4 py-8 sm:px-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight text-ink">Evidence and current checks</h1>
          <p className="max-w-[65ch] text-sm text-quiet">Validation selects the policy. The 2026 exam measures later projects. Research compares candidates on its own folds; these are different populations.</p>
          <p className="text-xs text-quiet">{runs.length} saved runs · {tests} recorded 2026 scoring runs · {latest ? `Latest served-policy evaluation: ${when(latest.timestamp)}` : "No served-policy evaluation yet"}</p>
        </div>
        {invalid > 0 && <p className="text-sm text-amber-900">{invalid} unreadable history lines were skipped.</p>}
        {canRun ? <Checks /> : <p className="text-sm text-quiet">Open this page on localhost to start or inspect local check jobs.</p>}
        {canRun && <RuntimeModel />}
        {latest?.validation && <ScoreTable title="Served policy: validation" block={latest.validation} note={`Recorded ${when(latest.timestamp)}. Scores describe the recorded configuration, not automatically the currently loaded model.`} />}
        {exam?.test && <ScoreTable title="2026 exam: latest recorded results" block={exam.test} note={`Recorded ${when(exam.timestamp)}. Whole design means all components within the declared tolerances, not installation suitability.`} />}
        {series.length > 0 && <Card className="space-y-4 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-lg font-semibold">Served-policy history</h2><Segmented name="metric" label="Measure" value={metric} onChange={setMetric} options={[{ value: "wholeDesign", label: "Whole design" }, { value: "ems", label: "Closeness" }]} /></div>
          <Trend runs={series} metric={metric} />
          <p className="text-xs text-quiet">Only consecutive points on the same branch with an identical explicit dataset/split/metric comparison key are connected. Legacy points remain separate.</p>
        </Card>}
        <Card className="space-y-3 p-5">
          <h2 className="text-lg font-semibold">Research comparisons</h2>
          <p className="text-sm text-quiet">Each row compares models evaluated together in that research run. Research gains are not new 2026 exam scores.</p>
          {research.length === 0 ? <p className="text-sm">No research results recorded.</p> : <div className="max-h-[560px] overflow-auto"><table className="w-full text-left text-xs tabular-nums"><thead><tr>{["Run / candidate", "Population", ...cols.map(c => c.name)].map(x => <th key={x} className="px-3 py-2 font-medium whitespace-nowrap">{x}</th>)}</tr></thead><tbody>{research.flatMap(r => Object.entries(r.validation?.models ?? {}).map(([name, scores], i) => <tr key={`${r.id}-${name}`} className="border-t border-zinc-200"><td className="max-w-80 px-3 py-2"><span className="block font-medium text-ink">{modelName(name)}</span><span className="text-quiet">{i === 0 ? `${when(r.timestamp)} · ${r.label ?? r.kind}` : "Same run"}</span></td><td className="px-3 py-2 whitespace-nowrap">Research folds · n={r.validation?.n ?? "unknown"}</td>{cols.map(c => <td key={c.key} className="px-3 py-2">{fmt(scores[c.key], c.rate)}</td>)}</tr>))}</tbody></table></div>}
        </Card>
        <details className="rounded-2xl border border-zinc-200 bg-white p-5"><summary className="cursor-pointer text-sm font-medium">All saved runs, provenance and limitations</summary>
          <p className="mt-3 text-sm text-quiet">PV ±20%, battery/heat pump ±25%; wallbox inclusion. Shuffled labels retain much of the whole-design score, so that control does not prove absence of leakage. The recorded whole-design gain over the installer median is within noise; the observed PV advantage is stronger.</p>
          <div className="mt-4 overflow-auto"><table className="w-full text-left text-xs"><thead><tr>{["When", "Branch / revision", "Kind", "Comparison key", "Note"].map(x => <th key={x} className="px-2 py-2">{x}</th>)}</tr></thead><tbody>{[...runs].reverse().map(r => <tr key={r.id} className="border-t border-zinc-200"><td className="px-2 py-2 whitespace-nowrap">{when(r.timestamp)}</td><td className="px-2 py-2">{r.git.branch} @{r.git.commit ?? "unknown"}{r.git.dirty ? " (dirty)" : ""}</td><td className="px-2 py-2">{r.kind}{r.testScored ? " · 2026 scored" : ""}</td><td className="max-w-48 break-all px-2 py-2">{r.comparisonKey ?? "Unverified legacy population"}</td><td className="px-2 py-2">{r.label}</td></tr>)}</tbody></table></div>
        </details>
      </main>
    </div>
  );
}

function ScoreTable({ title, block, note }: { title: string; block: NonNullable<Run["validation"]>; note: string }) {
  return <Card className="space-y-3 overflow-auto p-5"><h2 className="text-lg font-semibold">{title}</h2><p className="text-xs text-quiet">n={block.n ?? "unknown"} · {note}</p><table className="w-full text-left text-sm tabular-nums"><thead><tr><th className="py-2 pr-4">Model</th>{cols.map(c => <th key={c.key} className="px-3 py-2 font-medium whitespace-nowrap">{c.name}</th>)}</tr></thead><tbody>{Object.entries(block.models).map(([name, s]) => <tr key={name} className="border-t border-zinc-200"><th className="py-3 pr-4 font-medium">{modelName(name)}</th>{cols.map(c => <td key={c.key} className="px-3 py-3">{fmt(s[c.key], c.rate)}</td>)}</tr>)}</tbody></table></Card>;
}

function Trend({ runs, metric }: { runs: Run[]; metric: Metric }) {
  const rate = metric !== "ems";
  const points = runs.map((r, i) => ({ r, i, value: r.validation?.models.ours?.[metric] })).filter(p => p.value != null);
  if (!points.length) return <p>No scores for this metric.</p>;
  const values = points.map(p => p.value! * (rate ? 100 : 1));
  const lo = Math.max(0, Math.floor(Math.min(...values) - 3)), hi = Math.max(lo + 5, Math.ceil(Math.max(...values) + 3));
  const x = (i: number) => points.length === 1 ? 380 : 64 + (i / Math.max(1, runs.length - 1)) * 632;
  const y = (v: number) => 175 - ((v * (rate ? 100 : 1) - lo) / (hi - lo)) * 155;
  const ticks = [...new Set([lo, Math.round((lo + hi) / 2), hi])];
  const labelPoints = points.length <= 5 ? points : [points[0], points[Math.floor((points.length - 1) / 2)], points.at(-1)!];
  return <div className="space-y-2">
    <div className="overflow-hidden rounded-xl bg-sand-2 px-2 py-3 sm:px-4">
      <svg viewBox="0 0 720 220" className="block w-full" role="img" aria-label={`Recorded ${rate ? "percentage" : "closeness"} validation scores; only verified comparable runs are connected`}>
      {ticks.map(v => <g key={v}><line x1="56" x2="704" y1={y(v / (rate ? 100 : 1))} y2={y(v / (rate ? 100 : 1))} stroke="#d4d4d8" strokeDasharray="3 5" /><text x="48" textAnchor="end" y={y(v / (rate ? 100 : 1)) + 4} fontSize="12" fill="#71717a">{v}{rate ? "%" : ""}</text></g>)}
      {points.map((p, i) => { const prev = points[i - 1]; return <g key={p.r.id}>{prev && prev.r.git.branch === p.r.git.branch && comparable(prev.r, p.r) && <line x1={x(prev.i)} y1={y(prev.value!)} x2={x(p.i)} y2={y(p.value!)} stroke="#2563eb" strokeWidth="2.5" />}<circle cx={x(p.i)} cy={y(p.value!)} r="5" fill="#2563eb" stroke="#fff" strokeWidth="2"><title>{`${p.r.git.branch} · ${when(p.r.timestamp)} · ${fmt(p.value, rate)}`}</title></circle></g>; })}
      {labelPoints.map(p => <text key={`date-${p.r.id}`} x={x(p.i)} y="208" textAnchor={p.i === points[0].i ? "start" : p.i === points.at(-1)!.i ? "end" : "middle"} fontSize="11" fill="#71717a">{when(p.r.timestamp)}</text>)}
      </svg>
    </div>
    <p className="text-xs text-quiet">{points.length} scored runs · values on the left · dates below. Gaps mean runs are not verified as comparable.</p>
  </div>;
}

function Checks() {
  const router = useRouter();
  const [job, setJob] = useState<CheckJob | null>(null), [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false), [exam, setExam] = useState(false);
  const [label, setLabel] = useState("");
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
      const r = await fetch("/lab/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode: exam ? "exam" : "checks", confirmTestScoring: exam, label }), signal: AbortSignal.timeout(8000) });
      const data = await r.json(); if (!r.ok) throw new Error(data.error ?? "Could not start checks.");
      setJob(data.job); setExam(false);
    } catch (e) { setError(e instanceof Error ? e.message : "Could not start checks."); }
    finally { setStarting(false); }
  }
  return <Card className="space-y-4 p-5 sm:p-6"><div className="space-y-1"><p className="text-xs font-medium uppercase tracking-wide text-quiet">Run locally</p><h2 className="text-lg font-semibold">Current checks</h2>
    <p className="max-w-[65ch] text-sm text-quiet">Development checks run regression tests, lint and type checking. They do not score the 2026 exam.</p></div>
    <div role="status" aria-live="polite" className={`rounded-xl border p-4 text-sm ${job?.state === "failed" ? "border-rose-200 bg-rose-50" : "border-zinc-200 bg-sand"}`}>{job ? <><div className="flex flex-wrap items-start justify-between gap-2"><p className="font-medium text-ink">{job.state === "running" ? "Checks are running" : job.state === "failed" ? "Checks failed" : job.state === "passed" ? "Checks passed" : job.state}: {job.stage}</p><span className="rounded-full bg-white px-2 py-0.5 text-xs text-quiet ring-1 ring-zinc-200">{job.completed.length} stages complete</span></div><p className="mt-2 text-xs text-quiet">Started {when(job.startedAt)} · last update {when(job.updatedAt)} · run {job.id.slice(0, 8)}</p>{job.completed.length > 0 && <p className="mt-2 text-xs text-quiet">Completed: {job.completed.join(" · ")}</p>}{job.error && <details className="mt-3"><summary className="cursor-pointer text-xs font-medium text-rose-800">Show failure details</summary><pre className="mt-2 max-h-72 overflow-auto rounded-lg bg-white p-3 font-mono text-xs leading-relaxed text-rose-900 ring-1 ring-rose-200">{cleanLog(job.error).slice(-12000)}</pre></details>}</> : "No Lab-managed check run has been started. Other CLI jobs are not inferred."}</div>
    <ErrorNote error={error} />
    <details><summary className="cursor-pointer text-xs text-quiet">More: final exam and run label</summary><div className="mt-3 space-y-3"><input value={label} onChange={e => setLabel(e.target.value)} maxLength={80} aria-label="Run label" placeholder="What changed?" className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm" /><label className="flex items-start gap-2 text-xs text-amber-900"><input type="checkbox" checked={exam} onChange={e => setExam(e.target.checked)} />I explicitly want to score the 2026 exam. This records another test look and must not be used to tune the policy.</label></div></details>
    <div className="flex flex-wrap items-center gap-3"><Button disabled={starting || job?.state === "running"} onClick={start}>{starting ? "Starting checks…" : job?.state === "running" ? "Checks running…" : exam ? "Run confirmed 2026 exam" : job?.state === "failed" ? "Retry development checks" : "Run development checks"}</Button>{job?.state === "running" && <span className="text-xs text-quiet">Wait for this run to finish before starting another.</span>}</div>
  </Card>;
}


type RuntimeProof={runtime:null|{alive:boolean;loadedFileMatches:boolean;verifiedManifest:boolean;trainingCutoff:string|null;trainingRows:number;modelSha256:string;policySha256:string;loadedAt:string};evaluationMatches:boolean;evaluationGeneratedAt:string|null};
function RuntimeModel(){
  const [proof,setProof]=useState<RuntimeProof|null>(null);
  useEffect(()=>{let active=true;const poll=()=>fetch("/api/runtime-provenance",{cache:"no-store",signal:AbortSignal.timeout(8000)}).then(r=>r.ok?r.json():null).then(d=>{if(active)setProof(d);}).catch(()=>{});void poll();const t=setInterval(poll,10000);return()=>{active=false;clearInterval(t);};},[]);
  const r=proof?.runtime;
  return <Card className="space-y-2 p-5"><h2 className="text-lg font-semibold">Running model provenance</h2>{!r?<p className="text-sm text-quiet">Runtime fingerprint unavailable. Start the engine with the current pnpm dev entry point; a legacy server cannot attest its loaded artifact.</p>:<>
    <p className="text-sm text-quiet">{r.alive&&r.loadedFileMatches&&r.verifiedManifest?`Verified training cutoff ${r.trainingCutoff} · ${r.trainingRows} training projects` : "Runtime training provenance is not verified. Retrain with the demo wrapper and restart the engine."}</p>
    <p className="text-xs text-quiet">Loaded {when(r.loadedAt)} · model {r.modelSha256?.slice(0,12)} · configuration {r.policySha256?.slice(0,12)}</p>
    <p className={`text-xs ${proof?.evaluationMatches?"text-quiet":"text-amber-900"}`}>{proof?.evaluationMatches?`Matching frozen evaluation: ${when(proof.evaluationGeneratedAt!)}`:"No matching frozen evaluation is certified. The saved scores above must not be attributed automatically to this artifact."}</p>
  </>}</Card>;
}

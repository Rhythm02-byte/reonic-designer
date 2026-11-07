"use client";

import { useState } from "react";
import { format, selectedModel, selectedScores, type Run, type Scores } from "@/lib/lab";

const columns: { key: keyof Scores; label: string; help: string; rate?: boolean }[] = [
  { key: "ems", label: "EMS", help: "Average closeness to the expert design (100 = identical)." },
  { key: "wholeDesign", label: "Whole design", help: "Share of homes where PV, battery, heat pump and wallbox are all within tolerance.", rate: true },
  { key: "pv", label: "PV", help: "PV within ±20% of the expert design.", rate: true },
  { key: "battery", label: "Battery", help: "Battery within ±25% of the expert design.", rate: true },
  { key: "latencyP50ms", label: "Latency p50 (ms)", help: "Median inference time in milliseconds; lower is better. This is not the full evaluation duration." },
];
const time = (run: Run) => new Date(run.timestamp).toISOString().replace("T", " ").slice(0, 19) + " UTC";
const label = (run: Run) => `${run.git.branch} · ${time(run)} · ${run.id.slice(0, 8)}`;
const duration = (run: Run) => typeof run.durationSec === "number" ? `${format(run.durationSec)} s` : "Not recorded";
const warning = (run: Run) => Object.values(run.splits.temporal?.models ?? {}).some((m) => typeof m.latencyP95ms === "number" && m.latencyP95ms > 400);

function Timeline({ runs, metric, onSelect }: { runs: Run[]; metric: "ems" | "wholeDesign"; onSelect: (id: string) => void }) {
  const branches = [...new Set(runs.map((r) => r.git.branch))];
  const start = Date.parse(runs[0].timestamp), end = Date.parse(runs[runs.length - 1].timestamp);
  const x = (r: Run) => end === start ? 460 : 64 + (Date.parse(r.timestamp) - start) / (end - start) * 792;
  const y = (v: number) => 248 - v * 2;
  const value = (r: Run) => { const v = selectedScores(r)[metric]; return typeof v === "number" ? v * (metric === "wholeDesign" ? 100 : 1) : null; };
  const baseline = (r: Run) => { const v = r.splits.temporal?.models.B0?.[metric]; return typeof v === "number" ? v * (metric === "wholeDesign" ? 100 : 1) : null; };
  return <>
    <svg className="lab-chart" viewBox="0 0 920 310" role="img" aria-labelledby="timeline-title timeline-desc">
      <title id="timeline-title">{metric === "ems" ? "EMS" : "Whole-design percentage"} over run time</title>
      <desc id="timeline-desc">Each numbered line is a branch. Dashed B0 references use the same branch number. Run buttons and the table below provide every point.</desc>
      {[0, 25, 50, 75, 100].map((v) => <g key={v}><line x1="64" x2="856" y1={y(v)} y2={y(v)} stroke="#e4e4e7" /><text x="52" y={y(v) + 4} textAnchor="end">{v}</text></g>)}
      {branches.map((branch, index) => { const group = runs.filter((r) => r.git.branch === branch); return <g key={branch}>
        <polyline points={group.filter((r) => baseline(r) !== null).map((r) => `${x(r)},${y(baseline(r)!)}`).join(" ")} fill="none" stroke="#71717a" strokeDasharray="6 5" />
        {group.filter((r) => baseline(r) !== null).map((r) => <text key={`baseline-${r.id}`} x={x(r) + 7} y={y(baseline(r)!) + 14}>B0·{index + 1}</text>)}
        <polyline points={group.filter((r) => value(r) !== null).map((r) => `${x(r)},${y(value(r)!)}`).join(" ")} fill="none" stroke="#1B1D20" strokeWidth="2" strokeDasharray={index ? `${12 + index * 2} ${3 + index}` : undefined} />
        {group.filter((r) => value(r) !== null).map((r) => <g key={r.id}>
          <circle cx={x(r)} cy={y(value(r)!)} r="6" fill="#FDFDFB" stroke="#1B1D20" strokeWidth="2" />
          <text x={x(r) + 8} y={y(value(r)!) - 9}>{index + 1}</text>
          <circle className="lab-point" cx={x(r)} cy={y(value(r)!)} r="12" fill="transparent" tabIndex={0} role="button" aria-label={`Inspect ${label(r)}: ${format(value(r))}`} onClick={() => onSelect(r.id)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(r.id); } }}><title>{label(r)}</title></circle>
        </g>)}
      </g>; })}
      <text x="64" y="282">{time(runs[0])}</text><text x="856" y="302" textAnchor="end">{time(runs[runs.length - 1])}</text>
    </svg>
    <p>{branches.map((branch, i) => `${i + 1}: ${branch}`).join(" · ")} · Dashed: installer median (B0), measured per run.</p>
  </>;
}

export default function Lab({ runs }: { runs: Run[] }) {
  const [metric, setMetric] = useState<"ems" | "wholeDesign">("ems");
  const [activeId, setActive] = useState(runs.at(-1)?.id ?? "");
  const [fromId, setFrom] = useState(runs.at(-2)?.id ?? runs[0]?.id ?? "");
  const [toId, setTo] = useState(runs.at(-1)?.id ?? "");
  if (!runs.length) return <section className="lab-section"><h1>No evaluation runs yet</h1><p>Record the current evaluation with <code>npm run lab:seed</code>, then reload this page.</p></section>;
  const latest = runs[runs.length - 1], active = runs.find((r) => r.id === activeId) ?? latest;
  const ours = selectedScores(latest), baseline = latest.splits.temporal?.models.B0 ?? {};
  const models = latest.splits.temporal?.models ?? {};
  const chosen = selectedModel(latest);
  const rows = [{ key: "B1", name: "Rule of thumb" }, { key: "B0", name: "Installer median" }, ...(chosen ? [{ key: chosen, name: `Ours (${chosen})` }] : [])];
  const from = runs.find((r) => r.id === fromId) ?? runs[0], to = runs.find((r) => r.id === toId) ?? latest;
  const a = selectedScores(from), b = selectedScores(to);
  const honesty = latest.honesty;
  return <>
    <header className="lab-intro"><h1>Expert match on unseen 2026 projects: <span>{format(ours.ems)}</span>/100</h1><p>vs {format(baseline.ems)} for &quot;copy the installer&apos;s usual design&quot; · {latest.splits.temporal?.nTest ?? "Unknown number of"} test projects · {label(latest)}</p>
      <dl className="lab-help"><div><dt>EMS</dt><dd>Average closeness to the expert design (100 = identical).</dd></div><div><dt>Whole design</dt><dd>Share of homes where PV, battery, heat pump and wallbox are all within tolerance.</dd></div><div><dt>PV/Battery within tolerance</dt><dd>PV within ±20%, battery within ±25%.</dd></div></dl>
    </header>
    <section className="lab-section" aria-labelledby="timeline-heading"><h2 id="timeline-heading">Run timeline</h2>
      <fieldset className="lab-toggle"><legend>Timeline measure</legend>{(["ems", "wholeDesign"] as const).map((key) => <label key={key}><input type="radio" name="metric" checked={metric === key} onChange={() => setMetric(key)} />{key === "ems" ? "EMS" : "Whole design %"}</label>)}</fieldset>
      <Timeline runs={runs} metric={metric} onSelect={setActive} />
      <details><summary>Show chart data as a table</summary><div className="lab-scroll"><table><caption>Temporal test scores by run, in time order</caption><thead><tr><th scope="col">Run</th><th scope="col">EMS</th><th scope="col">Whole design</th><th scope="col">B0 EMS</th><th scope="col">B0 whole design</th></tr></thead><tbody>{runs.map((r) => <tr key={r.id}><th scope="row"><button onClick={() => setActive(r.id)}>{label(r)}</button></th><td>{format(selectedScores(r).ems)}</td><td>{format(selectedScores(r).wholeDesign, true)}</td><td>{format(r.splits.temporal?.models.B0?.ems)}</td><td>{format(r.splits.temporal?.models.B0?.wholeDesign, true)}</td></tr>)}</tbody></table></div></details>
      <div className="lab-detail" aria-live="polite"><h3>Selected run: {label(active)}</h3><p>Commit: {active.git.commit ?? "Local checkout, no commit"}{active.git.dirty ? " (uncommitted changes)" : ""} · Duration: {duration(active)} · Engine: {active.engineVersion ?? "Not recorded"}</p><details><summary>Policy configuration at recording time</summary><pre>{JSON.stringify(active.policyConfig ?? {}, null, 2)}</pre></details><details><summary>Configuration selected in this evaluation</summary><pre>{JSON.stringify(active.selection?.config ?? {}, null, 2)}</pre></details></div>
    </section>
    <section className="lab-section"><h2>Latest run comparison</h2><p>Temporal test, n = {latest.splits.temporal?.nTest ?? "not recorded"}. Bold marks the best recorded value; lower latency is better.</p><div className="lab-scroll"><table><caption>{label(latest)}</caption><thead><tr><th scope="col">Model</th>{columns.map((c) => <th scope="col" key={c.key}><abbr title={c.help} tabIndex={0}>{c.label}</abbr></th>)}</tr></thead><tbody>{rows.map((row) => <tr key={row.key}><th scope="row">{row.name}</th>{columns.map((c) => {
      const v = models[row.key]?.[c.key];
      const values = rows.flatMap((r) => typeof models[r.key]?.[c.key] === "number" ? [models[r.key][c.key] as number] : []);
      const best = typeof v === "number" && v === (c.key === "latencyP50ms" ? Math.min(...values) : Math.max(...values));
      return <td key={c.key}>{best ? <strong>{format(v, c.rate)}</strong> : format(v, c.rate)}</td>;
    })}</tr>)}</tbody></table></div></section>
    {(honesty || latest.oracle || latest.selection) && <section className="lab-section"><h2>Honesty checks</h2>
      {latest.selection && <p>Protocol: selection on validation ({latest.selection.nValidation ?? "unrecorded"} projects); the frozen choice is refit through 2025 and evaluated on the 2026 temporal test.</p>}
      <p>Shuffled-label check: {honesty?.shuffledLabel?.passed === true ? "passed" : honesty?.shuffledLabel?.passed === false ? "failed" : "not recorded"}{typeof honesty?.shuffledLabel?.ems === "number" && ` (EMS ${format(honesty.shuffledLabel.ems)})`}.</p>
      <p>Repeated-split EMS: {format(honesty?.repeatedSplit?.mean)} ± {format(honesty?.repeatedSplit?.sd)}{typeof honesty?.repeatedSplit?.n === "number" && ` (${honesty.repeatedSplit.n} splits)`}. Fuzz passes: {honesty?.fuzz?.passed ?? "not recorded"} / {honesty?.fuzz?.total ?? "not recorded"}.</p>
      {latest.oracle && <div className="lab-scroll"><table><caption>Value of answering a question, measured on the temporal test. Roof uses expert capacity and is an upper bound.</caption><thead><tr><th scope="col">Question</th><th scope="col">n</th><th scope="col">Whole design: unknown → answered</th><th scope="col">Value in whole-design points</th></tr></thead><tbody>{Object.entries(latest.oracle).map(([key, o]) => <tr key={key}><th scope="row">{({ demand: "Real annual consumption", ev: "EV planned?", evAssumedNo: "EV vs assumed no", heat: "Heat demand", roof: "Roof capacity" } as Record<string, string>)[key] ?? key}{(o.upperBound || key === "roof") && " (UPPER BOUND)"}</th><td>{o.n ?? "Not recorded"}</td><td>{format(o.unknown.wholeDesign, true)} → {format(o.answered.wholeDesign, true)}</td><td>{typeof o.gain.wholeDesign === "number" ? `Answering this question is worth ${o.gain.wholeDesign >= 0 ? "+" : ""}${format(o.gain.wholeDesign * 100)} points` : "Not recorded"}</td></tr>)}</tbody></table></div>}
    </section>}
    <section className="lab-section"><h2>Run diff</h2>{runs.length < 2 ? <p>Record another evaluation to compare progress over time.</p> : <>
      <div className="lab-pickers"><label>From<select value={from.id} onChange={(e) => setFrom(e.target.value)}>{runs.map((r) => <option key={r.id} value={r.id}>{label(r)}</option>)}</select></label><label>To<select value={to.id} onChange={(e) => setTo(e.target.value)}>{runs.map((r) => <option key={r.id} value={r.id}>{label(r)}</option>)}</select></label></div>
      <p>Selected temporal model in each run: {selectedModel(from) ?? "unrecorded"} → {selectedModel(to) ?? "unrecorded"}. Differences under 2 points are marked within noise (n≈325); this is a heuristic, not a significance test.</p>
      {(from.splits.temporal?.nTest !== to.splits.temporal?.nTest) && <p role="status">Test sample sizes differ; these runs may not be directly comparable.</p>}
      <div className="lab-scroll"><table><caption>Change from the first selected run to the second</caption><thead><tr><th scope="col">Metric</th><th scope="col">From</th><th scope="col">To</th><th scope="col">Delta</th></tr></thead><tbody>{[...columns, { key: "heatPump", label: "Heat pump", rate: true }, { key: "wallbox", label: "Wallbox", rate: true }] .map((c) => {
        const av = a[c.key as keyof Scores], bv = b[c.key as keyof Scores];
        const delta = typeof av === "number" && typeof bv === "number" ? (bv - av) * (c.rate ? 100 : 1) : null;
        return <tr key={c.key}><th scope="row">{c.label}</th><td>{format(av, c.rate)}</td><td>{format(bv, c.rate)}</td><td>{delta === null ? "Not recorded" : `${delta > 0 ? "▲ increased" : delta < 0 ? "▼ decreased" : "= unchanged"} ${format(Math.abs(delta))} ${c.key === "latencyP50ms" ? "ms" : "points"}${c.key !== "latencyP50ms" && Math.abs(delta) < 2 ? " · within noise" : ""}`}</td></tr>;
      })}</tbody></table></div></>}</section>
    <section className="lab-section"><h2>Run durations</h2><p>Total evaluation duration and inference p95 are separate measurements. Warning threshold: p95 above 400 ms for any recorded model.</p><div className="lab-scroll"><table><caption>Timing for every recorded run</caption><thead><tr><th scope="col">Run</th><th scope="col">Evaluation duration</th><th scope="col">Selected model p95</th><th scope="col">Latency check</th></tr></thead><tbody>{runs.map((r) => <tr key={r.id}><th scope="row">{label(r)}</th><td>{duration(r)}</td><td>{format(selectedScores(r).latencyP95ms)}{typeof selectedScores(r).latencyP95ms === "number" ? " ms" : ""}</td><td>{warning(r) ? <span className="lab-warning">Warning: model p95 &gt; 400 ms</span> : Object.values(r.splits.temporal?.models ?? {}).some((m) => typeof m.latencyP95ms === "number") ? "Recorded models ≤ 400 ms; missing values unknown" : "Not recorded"}</td></tr>)}</tbody></table></div></section>
  </>;
}

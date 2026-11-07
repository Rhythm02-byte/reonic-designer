"use client";
// The full held-out evaluation: every model on the test projects it never saw. From /eval/summary.
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { pct } from "@/lib/format";
import type { EvalSummary, Source } from "@/lib/types";
import { ErrorNote, Footer, Header, Logo, PersonaChip } from "./ui";

const WIDTH = "max-w-5xl";
const COLS: { label: string; get: (m: EvalSummary["models"][string]) => string }[] = [
  { label: "Whole design", get: (m) => pct(m.wholeDesign) },
  { label: "Solar", get: (m) => pct(m.pv) },
  { label: "Battery", get: (m) => pct(m.battery) },
  { label: "Heat pump", get: (m) => pct(m.heatPump) },
  { label: "Wallbox", get: (m) => pct(m.wallbox) },
  { label: "Expert match score", get: (m) => (m.ems === null ? "n/a" : String(Math.round(m.ems))) },
];

export default function EvalReport() {
  const [r, setR] = useState<{ data: EvalSummary; source: Source } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.evalSummary().then(setR, (e: Error) => setError(e.message));
  }, []);
  return (
    <div className="flex min-h-dvh flex-col">
      <Header width={WIDTH}>
        <Logo />
        <PersonaChip who="planner" />
      </Header>
      <main className={`mx-auto w-full flex-1 space-y-6 px-4 py-8 sm:px-6 ${WIDTH}`}>
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Evaluation</h1>
        <ErrorNote error={error} />
        {r && (
          <>
            {r.source === "demo" && (
              <p className="text-sm text-amber-900">
                <strong className="font-semibold">Demo data.</strong> The engine is not reachable, so none of this was measured.
              </p>
            )}
            <p className="max-w-[65ch] text-base">
              Each model designs the {r.data.nTest} test projects ({r.data.split} split) it never saw. A size is right when it is
              within tolerance of the expert&apos;s, or both agree on none. Chosen model: <strong className="text-ink">{r.data.chosen}</strong>.
              {r.data.selection && ` ${r.data.selection}`}
            </p>
            <div className="overflow-x-auto rounded-2xl border border-zinc-200 bg-white">
              <table className="w-full text-left text-sm tabular-nums">
                <caption className="sr-only">Share of held-out projects each model gets right, by part</caption>
                <thead className="text-xs text-muted">
                  <tr>
                    <th scope="col" className="px-4 py-2 font-medium">Model</th>
                    {COLS.map((c) => (
                      <th key={c.label} scope="col" className="px-4 py-2 font-medium">{c.label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-200">
                  {Object.entries(r.data.models).map(([name, m]) => (
                    <tr key={name}>
                      <th scope="row" className="px-4 py-2 font-medium text-ink">
                        {name}
                        {name === r.data.chosen && <span className="ml-2 text-xs font-normal text-muted">(chosen)</span>}
                      </th>
                      {COLS.map((c) => (
                        <td key={c.label} className="px-4 py-2">{c.get(m)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-muted">Generated {r.data.generatedAt}. Offline and deterministic; the test split is never used for tuning.</p>
          </>
        )}
      </main>
      <Footer width={WIDTH}>
        <Link href="/" className="underline underline-offset-2">Back to the planner</Link>
      </Footer>
    </div>
  );
}

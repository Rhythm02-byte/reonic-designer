"use client";
// "Why this battery size": self-sufficiency and yearly savings against battery size, with the chosen size and the
// economic optimum marked. Plain SVG; the same numbers are in a table underneath.
import { eur, num, pct } from "@/lib/format";
import type { CurvePoint } from "@/lib/types";

const W = 640, H = 260, L = 44, R = 52, T = 14, B = 34;

type Pt = { x: number; y: number };

function at(series: Pt[], x: number): number | null {
  if (!series.length) return null;
  if (x <= series[0].x) return series[0].y;
  for (let i = 1; i < series.length; i++) {
    if (x <= series[i].x) {
      const a = series[i - 1], b = series[i];
      return a.y + ((b.y - a.y) * (x - a.x)) / (b.x - a.x || 1);
    }
  }
  return series.at(-1)!.y;
}

export function BatteryCurve({ points, chosenKwh, bestKwh }: { points: CurvePoint[]; chosenKwh: number; bestKwh: number | null }) {
  const pts = [...points].sort((a, b) => a.kwh - b.kwh);
  const aut = pts.filter((p) => p.autarky !== null).map((p) => ({ x: p.kwh, y: p.autarky! }));
  const sav = pts.filter((p) => p.savingsEurYear !== null).map((p) => ({ x: p.kwh, y: p.savingsEurYear! }));
  if (pts.length < 2 || (!aut.length && !sav.length)) return null;

  const maxX = Math.max(pts.at(-1)!.kwh, chosenKwh, bestKwh ?? 0) || 1;
  const maxA = Math.max(0.1, ...aut.map((p) => p.y)) * 1.1;
  const minS = Math.min(0, ...sav.map((p) => p.y));
  const maxS = Math.max(1, ...sav.map((p) => p.y)) * 1.1;
  const X = (x: number) => L + (x / maxX) * (W - L - R);
  const YA = (y: number) => T + (1 - y / maxA) * (H - T - B);
  const YS = (y: number) => T + (1 - (y - minS) / (maxS - minS)) * (H - T - B);
  const line = (s: Pt[], Y: (y: number) => number) => s.map((p, i) => `${i ? "L" : "M"}${X(p.x).toFixed(1)} ${Y(p.y).toFixed(1)}`).join(" ");

  const marks = [
    { kwh: bestKwh, kind: "best" as const },
    { kwh: chosenKwh, kind: "chosen" as const },
  ].filter((m): m is { kwh: number; kind: "best" | "chosen" } => m.kwh !== null);
  const chosenA = at(aut, chosenKwh), chosenS = at(sav, chosenKwh);
  const bestA = bestKwh === null ? null : at(aut, bestKwh), bestS = bestKwh === null ? null : at(sav, bestKwh);
  const xTicks = pts.filter((_, i) => pts.length <= 9 || i % 2 === 0).map((p) => p.kwh);

  return (
    <div className="space-y-3">
      <ul className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-quiet">
        <li className="flex items-center gap-2">
          <svg width="22" height="8" aria-hidden><path d="M0 4h22" className="stroke-ink" strokeWidth="2.5" /></svg>
          Self-sufficiency (left axis)
        </li>
        <li className="flex items-center gap-2">
          <svg width="22" height="8" aria-hidden><path d="M0 4h22" className="stroke-zinc-500" strokeWidth="2.5" strokeDasharray="5 3" /></svg>
          Savings per year (right axis)
        </li>
      </ul>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full"
        role="img"
        aria-label={`Chart of self-sufficiency and yearly savings for battery sizes from ${num(pts[0].kwh)} to ${num(maxX)} kWh. The table below has the same numbers.`}
      >
        {/* grid and axes */}
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <g key={f}>
            <line x1={L} x2={W - R} y1={YA(maxA * f)} y2={YA(maxA * f)} className="stroke-zinc-200" />
            <text x={L - 6} y={YA(maxA * f) + 4} textAnchor="end" className="fill-quiet text-[11px]">{Math.round(maxA * f * 100)}%</text>
            <text x={W - R + 6} y={YS(minS + (maxS - minS) * f) + 4} className="fill-quiet text-[11px]">{eur(minS + (maxS - minS) * f)}</text>
          </g>
        ))}
        {xTicks.map((k) => (
          <text key={k} x={X(k)} y={H - B + 16} textAnchor="middle" className="fill-quiet text-[11px]">{num(k)}</text>
        ))}
        <text x={(L + W - R) / 2} y={H - 4} textAnchor="middle" className="fill-quiet text-[11px]">Battery size (kWh)</text>

        {/* the two curves: solid vs dashed, so they differ by more than colour */}
        <path d={line(aut, YA)} fill="none" className="stroke-ink" strokeWidth="2.5" strokeLinejoin="round" />
        <path d={line(sav, YS)} fill="none" className="stroke-zinc-500" strokeWidth="2.5" strokeDasharray="6 4" strokeLinejoin="round" />

        {/* best value: open circles; chosen: filled blue circles with a guide line */}
        {bestKwh !== null && (
          <g className="fill-white stroke-ink" strokeWidth="2">
            {bestA !== null && <circle cx={X(bestKwh)} cy={YA(bestA)} r="5.5" />}
            {bestS !== null && <circle cx={X(bestKwh)} cy={YS(bestS)} r="5.5" />}
          </g>
        )}
        <line x1={X(chosenKwh)} x2={X(chosenKwh)} y1={T} y2={H - B} className="stroke-blue-600" strokeWidth="1.5" strokeDasharray="2 3" />
        <g className="fill-blue-600 stroke-white" strokeWidth="2">
          {chosenA !== null && <circle cx={X(chosenKwh)} cy={YA(chosenA)} r="5" />}
          {chosenS !== null && <circle cx={X(chosenKwh)} cy={YS(chosenS)} r="5" />}
        </g>
      </svg>

      <ul className="space-y-1 text-sm">
        {marks
          .sort((a, b) => (a.kind === "chosen" ? -1 : b.kind === "chosen" ? 1 : 0))
          .map((m) => {
            const a = at(aut, m.kwh), s = at(sav, m.kwh);
            return (
              <li key={m.kind} className="flex items-center gap-2">
                <svg width="14" height="14" aria-hidden>
                  {m.kind === "chosen" ? <circle cx="7" cy="7" r="5" className="fill-blue-600" /> : <circle cx="7" cy="7" r="5" className="fill-white stroke-ink" strokeWidth="2" />}
                </svg>
                <span>
                  <span className="font-medium text-ink">{m.kind === "chosen" ? "Your choice" : "Best value"}: {m.kwh > 0 ? `${num(m.kwh)} kWh` : "no battery"}</span>
                  {a !== null && ` · ${pct(a)} self-sufficient`}
                  {s !== null && ` · saves about ${eur(s)} a year`}
                  {m.kind === "best" && " · the size where an extra kWh stops paying for itself"}
                </span>
              </li>
            );
          })}
      </ul>

      <details className="text-sm">
        <summary className="cursor-pointer text-quiet underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-blue-600 pointer-coarse:py-3">
          Show the numbers as a table
        </summary>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-left">
            <caption className="sr-only">Self-sufficiency and savings by battery size</caption>
            <thead className="text-xs text-muted">
              <tr>
                <th scope="col" className="py-1 pr-3 font-medium">Battery</th>
                <th scope="col" className="py-1 pr-3 font-medium">Self-sufficiency</th>
                <th scope="col" className="py-1 pr-3 font-medium">Savings per year</th>
                <th scope="col" className="py-1 font-medium">Note</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 tabular-nums">
              {pts.map((p) => (
                <tr key={p.kwh}>
                  <th scope="row" className="py-1 pr-3 font-medium text-ink">{p.kwh > 0 ? `${num(p.kwh)} kWh` : "None"}</th>
                  <td className="py-1 pr-3">{p.autarky === null ? "n/a" : pct(p.autarky)}</td>
                  <td className="py-1 pr-3">{p.savingsEurYear === null ? "n/a" : eur(p.savingsEurYear)}</td>
                  <td className="py-1 text-xs">
                    {[p.kwh === chosenKwh && "your choice", p.kwh === bestKwh && "best value"].filter(Boolean).join(", ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

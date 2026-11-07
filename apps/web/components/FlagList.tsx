"use client";
// Checks on the design. Severity is always a word, never only a colour.
import { useEffect, useRef } from "react";
import { haptic } from "@/lib/haptics";
import { LABEL } from "@/lib/format";
import type { Flag, Target } from "@/lib/types";

const WORD = { error: "Error", warn: "Warning", info: "Note" } as const;
const LOOK = {
  error: "border-rose-200 bg-rose-50 text-rose-800",
  warn: "border-amber-300 bg-amber-50 text-amber-900",
  info: "border-zinc-200 bg-sand text-quiet",
};
const BADGE = { error: "bg-rose-800 text-white", warn: "bg-amber-400 text-ink", info: "bg-zinc-200 text-ink" };
const ORDER = { error: 0, warn: 1, info: 2 };
const TARGET_OF: Record<string, Target> = { pv: "pvKwp", battery: "batteryKwh", heatPump: "heatPumpKw", wallbox: "wallboxKw" };

export function FlagList({ flags }: { flags: Flag[] }) {
  // A buzz when a red flag appears, not on every re-render while it stays.
  const seen = useRef(false);
  const hasError = flags.some((f) => f.severity === "error");
  useEffect(() => {
    if (hasError && !seen.current) haptic("error");
    seen.current = hasError;
  }, [hasError]);

  const sorted = [...flags].sort((a, b) => ORDER[a.severity] - ORDER[b.severity]);
  return (
    <section aria-labelledby="checks" className="space-y-2">
      <h2 id="checks" className="text-sm font-semibold text-ink">
        Checks
      </h2>
      {sorted.length === 0 ? (
        <p className="text-sm text-muted">Nothing unusual found for this home.</p>
      ) : (
        <ul className="space-y-2">
          {sorted.map((f, i) => (
            <li key={`${f.code}-${i}`} className={`flex flex-wrap items-baseline gap-x-2 gap-y-1 rounded-xl border px-3 py-2 text-sm ${LOOK[f.severity]}`}>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${BADGE[f.severity]}`}>{WORD[f.severity]}</span>
              {f.component && <span className="font-medium">{LABEL[TARGET_OF[f.component]]}:</span>}
              <span className="min-w-0 flex-1 basis-48">{f.message}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

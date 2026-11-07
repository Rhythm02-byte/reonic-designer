"use client";
// The system the engine proposes: one row per component with a size stepper (snaps to the catalog), a lock pin
// and a range hint (what experts usually pick). Locked components are kept when anything else changes.
import { haptic } from "@/lib/haptics";
import { LABEL, num, pct, size, UNIT } from "@/lib/format";
import { TARGETS } from "@/lib/types";
import type { Design, Interval, Meta, Sizes, Target } from "@/lib/types";
import { IconButton } from "./ui";

/** p10 to p90 of the expert range as a quiet band, the current size as a tick; the words say the same. */
export function RangeHint({ target, value, interval, catalogMax }: { target: Target; value: number; interval?: Interval; catalogMax: number }) {
  if (!interval) return null;
  const { p10, p90, probIncluded } = interval;
  const unit = UNIT[target];
  const max = Math.max(p90, value, catalogMax, 1) * 1.05;
  const at = (v: number) => `${Math.min(100, Math.max(0, (v / max) * 100))}%`;
  const lowChance = probIncluded !== null && probIncluded < 0.5;
  let text: string;
  if (value === 0) text = lowChance ? `${pct(1 - (probIncluded ?? 0))} of similar designs have none` : `Similar designs usually have one: ${num(p10)} to ${num(p90)} ${unit}`;
  else if (lowChance) text = `Unusual: only ${pct(probIncluded ?? 0)} of similar designs include one`;
  else text = `Experts usually pick ${num(p10)} to ${num(p90)} ${unit}${value < p10 || value > p90 ? ". This is outside that range" : ""}`;
  return (
    <div className="space-y-1">
      {value > 0 && !lowChance && (
        <div aria-hidden className="relative h-1.5 rounded-full bg-sand">
          <div className="absolute inset-y-0 rounded-full bg-zinc-300" style={{ left: at(p10), width: `calc(${at(p90)} - ${at(p10)})` }} />
          <div className="absolute -top-0.5 h-2.5 w-0.5 rounded-full bg-blue-600" style={{ left: at(value) }} />
        </div>
      )}
      <p className="text-xs text-muted">{text}</p>
    </div>
  );
}

function nextStep(catalog: number[], value: number, dir: 1 | -1) {
  const xs = [...new Set([0, ...catalog])].sort((a, b) => a - b);
  if (dir === 1) return xs.find((c) => c > value + 1e-9);
  return [...xs].reverse().find((c) => c < value - 1e-9);
}

export function SystemCard({
  design, meta, locked, busy, onSet, onToggleLock,
}: {
  design: Design;
  meta: Meta;
  locked: Partial<Sizes>;
  busy: boolean;
  onSet: (t: Target, v: number) => void;
  onToggleLock: (t: Target) => void;
}) {
  return (
    <ul className={`divide-y divide-zinc-200 ${busy ? "opacity-60" : ""}`}>
      {TARGETS.map((t) => {
        const catalog = meta.targets.find((x) => x.name === t)?.catalog ?? [];
        const v = design.sizes[t];
        const down = nextStep(catalog, v, -1);
        const up = nextStep(catalog, v, 1);
        const isLocked = t in locked;
        const step = (to: number | undefined) => {
          if (to === undefined) return;
          haptic("nudge");
          onSet(t, to);
        };
        return (
          <li key={t} className="space-y-2 px-4 py-3">
            <div className="flex items-center gap-2">
              <div className="min-w-0 flex-1">
                <div className="text-xs text-muted">{LABEL[t]}</div>
                <div className="text-lg font-semibold tracking-tight text-ink tabular-nums">
                  {size(v, UNIT[t])}
                  {t === "pvKwp" && design.modules ? <span className="ml-2 text-xs font-normal text-muted">{design.modules} panels</span> : null}
                </div>
              </div>
              <IconButton icon="minus" label={`Smaller ${LABEL[t].toLowerCase()}`} disabled={down === undefined} onClick={() => step(down)} />
              <IconButton icon="plus" label={`Larger ${LABEL[t].toLowerCase()}`} disabled={up === undefined} onClick={() => step(up)} />
              <IconButton
                icon={isLocked ? "lock" : "unlock"}
                label={`${isLocked ? "Unpin" : "Pin"} ${LABEL[t].toLowerCase()} at ${size(v, UNIT[t])}`}
                pressed={isLocked}
                onClick={() => onToggleLock(t)}
              />
            </div>
            <RangeHint target={t} value={v} interval={design.confidence[t]} catalogMax={Math.max(0, ...catalog)} />
            {isLocked && <p className="text-xs text-quiet">Pinned: stays at this size when the home changes.</p>}
          </li>
        );
      })}
    </ul>
  );
}

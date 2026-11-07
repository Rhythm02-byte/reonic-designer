"use client";
// After every change: what moved, what it costs, what it does to self-sufficiency, why, and a way back.
import { eurSigned, LABEL, num, size, UNIT } from "@/lib/format";
import type { Sizes, Target } from "@/lib/types";
import { Button, IconButton } from "./ui";

export type Diff = {
  changes: { target: Target; from: number; to: number }[];
  price: number | null;
  autarkyPts: number | null;
  because: string;
};

export function diffOf(before: Sizes, after: Sizes, price: number | null, autarkyPts: number | null, because: string): Diff | null {
  const changes = (Object.keys(after) as Target[])
    .filter((t) => Math.abs(before[t] - after[t]) > 1e-6)
    .map((t) => ({ target: t, from: before[t], to: after[t] }));
  return changes.length ? { changes, price, autarkyPts, because } : null;
}

const change = (c: Diff["changes"][number]) =>
  c.from > 0 && c.to > 0 ? `${LABEL[c.target]} ${num(c.from)} → ${num(c.to)} ${UNIT[c.target]}` : `${LABEL[c.target]} ${size(c.from, UNIT[c.target])} → ${size(c.to, UNIT[c.target])}`;

export function DiffBar({ diff, onUndo, onDismiss }: { diff: Diff; onUndo: () => void; onDismiss: () => void }) {
  const parts = [
    diff.changes.map(change).join(", "),
    diff.price === null ? null : eurSigned(diff.price),
    diff.autarkyPts === null ? null : `autarky ${diff.autarkyPts < 0 ? "−" : "+"}${Math.abs(diff.autarkyPts)} pts`,
  ].filter(Boolean);
  return (
    <div role="status" className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-2xl border border-zinc-200 bg-sand px-4 py-3 text-sm text-quiet">
      <p className="min-w-0 flex-1 basis-60">
        <span className="font-medium text-ink">{parts.join(" · ")}</span>
        <span> · because {diff.because}</span>
      </p>
      <div className="flex items-center gap-2">
        <Button variant="secondary" onClick={onUndo}>
          Undo
        </Button>
        <IconButton icon="x" label="Dismiss" onClick={onDismiss} />
      </div>
    </div>
  );
}

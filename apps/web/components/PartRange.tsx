// ours: the expert range (p10 to p90 of what installers picked for similar homes) and the engine's flag severity
// for one part. Mounted in his SystemCard under the size; his card already lists warn/error messages, so this adds
// the range, an "Must fix" marker for rule errors, and the info notes he doesn't show.
import type { Design, Target } from "@/lib/api";
import { num, pct, UNIT } from "@/lib/copy";

export function PartRange({ t, design }: { t: Target; design: Design }) {
  const r = design.ranges?.[t];
  const v = design.values[t];
  const notes = (design.notes ?? []).filter((n) => n.target === t);
  const errors = notes.filter((n) => n.severity === "error").length;
  const info = notes.filter((n) => n.severity === "info");
  if (!r && notes.length === 0) return null;

  let text: string | null = null;
  if (r && v > 0 && r.p90 > 0) {
    const same = num(r.p10) === num(r.p90);
    text = same
      ? `Experts pick ${num(r.p10)} ${UNIT[t]}${num(v) !== num(r.p10) ? "; this differs" : ""}`
      : `Experts usually pick ${num(r.p10)} to ${num(r.p90)} ${UNIT[t]}${v < r.p10 || v > r.p90 ? "; this is outside that range" : ""}`;
  } else if (r && v === 0 && r.p90 > 0 && design.probability[t] >= 0.5) {
    text = `Similar homes usually have one: ${num(r.p10)} to ${num(r.p90)} ${UNIT[t]}`;
  } else if (r && v === 0) {
    text = `${pct(1 - design.probability[t])} of similar homes have none`;
  }
  const max = r ? Math.max(r.p90, v, 1) * 1.1 : 1;
  const at = (x: number) => `${(x / max) * 100}%`;

  return (
    <div className="space-y-1.5">
      {r && r.p90 > 0 && (v > 0 || design.probability[t] >= 0.5) && (
        <div aria-hidden className="relative h-1.5 rounded-full bg-sand">
          <div className="absolute inset-y-0 rounded-full bg-zinc-300" style={{ left: at(r.p10), width: `calc(${at(r.p90)} - ${at(r.p10)})` }} />
          {v > 0 && <div className="absolute -top-1 h-3.5 w-0.5 rounded-full bg-ink" style={{ left: at(v) }} />}
        </div>
      )}
      {text && <p className="text-xs text-quiet">{text}</p>}
      {errors > 0 && (
        <p className="text-xs font-medium text-red-700">
          Must fix: {errors === 1 ? "a planning rule is broken" : `${errors} planning rules are broken`} (see below).
        </p>
      )}
      {info.map((n) => (
        <p key={n.message} className="text-xs text-muted">
          {n.message}
        </p>
      ))}
    </div>
  );
}

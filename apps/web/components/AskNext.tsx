"use client";
// ours: "Ask next", the few unknown inputs that would change the design most, each with one-click answers.
// Mounted in his Planner under the project inputs; an answer goes through his setInput, so it lands in the draft,
// the "What changed?" bar and Undo like any edit.
import "@/lib/copy-ours";
import type { Design, InputValue, Target } from "@/lib/api";
import { eur, LABEL } from "@/lib/copy";
import { Button, Card } from "./ui";

const part = (t: Target) => (t === "pv_kwp" ? "solar" : LABEL[t].toLowerCase());
const list = (xs: string[]) => (xs.length > 1 ? `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}` : (xs[0] ?? ""));

export function AskNext({ design, set }: { design: Design | null; set: (name: string, v: InputValue) => void }) {
  const items = design?.askNext ?? [];
  if (items.length === 0) return null;
  return (
    <section aria-labelledby="ask-next" className="space-y-2">
      <h2 id="ask-next" className="text-sm font-semibold text-ink">
        Ask the customer next
      </h2>
      <Card className="divide-y divide-zinc-200">
        {items.map((q) => (
          <div key={q.field} className="space-y-2 p-4 text-sm">
            <div className="space-y-0.5">
              <p className="font-medium text-ink">{q.question}</p>
              <p className="text-xs text-muted">
                {q.why}
                {q.parts.length > 0 && ` Changes ${list(q.parts.map(part))}, up to ${eur(q.priceSwingEur)} apart.`}
              </p>
            </div>
            <div className="flex flex-wrap gap-2" role="group" aria-label={q.question}>
              {q.answers.map((a) => (
                <Button key={a.label} variant="secondary" className="px-3 py-1" onClick={() => set(q.field, a.value)}>
                  {a.label}
                </Button>
              ))}
            </div>
          </div>
        ))}
      </Card>
      {design?.source === "demo" && <p className="text-xs text-amber-800">Demo questions: the engine is not reachable.</p>}
    </section>
  );
}

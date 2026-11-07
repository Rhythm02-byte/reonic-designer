"use client";
// "Ask next": the few missing inputs that would change the design most, each with one-click answers.
import { eur, LABEL } from "@/lib/format";
import type { AskNext } from "@/lib/types";
import { Button, Card, OpenDot } from "./ui";

const list = (parts: string[]) => (parts.length > 1 ? `${parts.slice(0, -1).join(", ")} and ${parts[parts.length - 1]}` : (parts[0] ?? ""));

export function AskNextCard({ items, onAnswer }: { items: AskNext[]; onAnswer: (item: AskNext, value: number | boolean, label: string) => void }) {
  if (items.length === 0) return null;
  return (
    <Card className="p-4 text-sm" aria-labelledby="ask-next">
      <h2 id="ask-next" className="mb-3 text-sm font-semibold text-ink">
        Ask next
      </h2>
      <ul className="space-y-4">
        {items.map((q) => (
          <li key={q.field} className="flex gap-2.5">
            <OpenDot className="mt-0.5 size-4" />
            <div className="min-w-0 flex-1 space-y-2">
              <div className="space-y-0.5">
                <p className="font-medium text-ink">{q.question}</p>
                <p className="text-xs text-muted">
                  {q.why} Changes {list(q.impact.components.map((t) => (t === "pvKwp" ? LABEL[t] : LABEL[t].toLowerCase())))}, up to {eur(q.impact.priceSwingEur)} apart.
                </p>
              </div>
              <div className="flex flex-wrap gap-2" role="group" aria-label={q.question}>
                {q.answers.map((a) => (
                  <Button key={a.label} variant="secondary" className="px-3 py-1" onClick={() => onAnswer(q, a.value, a.label)}>
                    {a.label}
                  </Button>
                ))}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}

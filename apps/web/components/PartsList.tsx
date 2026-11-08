"use client";
// ours: the full parts list (bill of materials) from the engine, in Reonic's project_options_parts shape.
// PartsList: the planner's view of the current design. OfferParts: the homeowner's view of the chosen option; the
// offer link carries only sizes, so it asks the engine for the parts of exactly those sizes (all four pinned).
import { useEffect, useState } from "react";
import { api, type Inputs, type Part, type Values } from "@/lib/api";
import { num } from "@/lib/copy";
import { Card } from "./ui";

// Reonic's componentType values, worded for people.
const TYPE: Record<string, string> = {
  Module: "Solar modules", PvModule: "Solar modules", Inverter: "Inverter", BatteryStorage: "Battery", Battery: "Battery",
  Wallbox: "Wallbox", HeatPump: "Heat pump", Service: "Service", Mounting: "Mounting", Substructure: "Mounting",
};
const kind = (p: Part) => (p.type ? (TYPE[p.type] ?? p.type.replace(/([a-z])([A-Z])/g, "$1 $2")) : "Other");
const qty = (p: Part) => `${num(p.quantity, 2)}${p.units ? ` ${p.units}` : "×"}`;

export function PartsList({ parts, title = "Parts list", note }: { parts: Part[] | undefined; title?: string; note?: string }) {
  if (!parts) return null;
  return (
    <Card className="p-4 text-sm">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h2 className="text-sm font-semibold text-ink">{title}</h2>
        <span className="text-xs text-quiet">{parts.length} {parts.length === 1 ? "line" : "lines"}</span>
      </div>
      {parts.length === 0 ? (
        <p className="text-xs text-quiet">No parts: this setup adds no new equipment.</p>
      ) : (
        <table className="w-full">
          <caption className="sr-only">{title}</caption>
          <thead className="sr-only">
            <tr>
              <th scope="col">Quantity</th>
              <th scope="col">Part</th>
              <th scope="col">Type</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200">
            {parts.map((p, k) => (
              <tr key={`${p.name}-${k}`} className="align-top">
                <td className="w-14 py-2 pr-3 text-ink tabular-nums">{qty(p)}</td>
                <td className="py-2 pr-3">
                  <span className="block text-ink">{p.name}</span>
                  {p.brand && <span className="block text-xs text-quiet">{p.brand}</span>}
                </td>
                <td className="py-2 text-right text-xs whitespace-nowrap text-quiet">{kind(p)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {parts.length > 0 && (
        <p className="mt-3 text-xs text-muted">Preliminary: products picked from the installer&apos;s catalogue by size. Compatibility and string layout are not checked yet.</p>
      )}
      {note && <p className="mt-1 text-xs text-muted">{note}</p>}
    </Card>
  );
}

export function OfferParts({ inputs, values }: { inputs: Inputs; values: Values }) {
  const key = JSON.stringify([inputs, values]);
  const [got, setGot] = useState<{ key: string; parts: Part[] | undefined } | null>(null);
  useEffect(() => {
    let live = true;
    api.design(inputs, values).then(
      (d) => live && setGot({ key, parts: d.source === "live" ? d.parts : undefined }),
      () => live && setGot({ key, parts: undefined }),
    );
    return () => {
      live = false;
    };
  }, [inputs, values, key]);
  if (!got || got.key !== key) return <div className="h-40 animate-pulse rounded-2xl bg-sand" />;
  return (
    <PartsList
      parts={got.parts}
      title="What gets installed"
      note="Your installer confirms the exact products after checking your roof and wiring on site."
    />
  );
}

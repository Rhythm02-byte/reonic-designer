"use client";
// The home: the few facts the planner types in. Each says where its value comes from when it is not typed.
import { HEATING_LABEL, type Home } from "@/lib/format";
import type { Design, HomeInputs, Meta } from "@/lib/types";
import { Card, Icon, type IconName, Segmented } from "./ui";

const inputClass =
  "w-full rounded-lg bg-white px-2.5 py-1.5 text-sm text-ink ring-1 ring-zinc-200 placeholder:text-zinc-400 focus:ring-2 focus:ring-blue-600 focus:outline-none pointer-coarse:min-h-11";

export type HomeKey = keyof Home;

// The engine's name for each field: a dotted path into HomeInputs, the same key /meta fields and provenance use.
export const WIRE: Record<HomeKey, string> = {
  demandKwh: "demandKwh", persons: "persons", heatingType: "heating.type", hasEv: "ev.has", evKm: "ev.kmPerYear", roofModules: "building.roofMaxModules",
};

/** "estimated" / "default" in muted text, or nothing when the planner entered the value. */
export function provenanceHint(key: HomeKey, provenance: Design["provenance"] | undefined, touched: HomeKey[]): string | null {
  if (touched.includes(key)) return null;
  const p = provenance?.[WIRE[key]];
  if (!p) return "default";
  if (p.source === "entered") return null;
  if (p.source === "derived") return "estimated";
  if (p.source === "extracted") return "from document";
  if (key === "demandKwh" && p.confidence < 0.5) return "looks like a default";
  return "default";
}

function Hint({ text }: { text: string | null }) {
  return text ? <span className="text-xs text-muted">{text}</span> : null;
}

function Label({ icon, htmlFor, hint, children }: { icon: IconName; htmlFor?: string; hint: string | null; children: string }) {
  const Tag = htmlFor ? "label" : "div";
  return (
    <div className="flex items-baseline justify-between gap-2">
      <Tag htmlFor={htmlFor} className="flex items-center gap-2 text-sm text-ink">
        <Icon name={icon} className="size-4 translate-y-0.5 text-blue-600" />
        {children}
      </Tag>
      <Hint text={hint} />
    </div>
  );
}

type Props = {
  meta: Meta | null;
  inputs: HomeInputs;
  home: Home;
  provenance?: Design["provenance"];
  touched: HomeKey[];
  setHome: (patch: Partial<Home>, key: HomeKey) => void;
  setInstaller: (id: string) => void;
};

export function InputsCard({ meta, inputs, home, provenance, touched, setHome, setInstaller }: Props) {
  const hint = (k: HomeKey) => (k === "roofModules" && home.roofModules === null ? null : provenanceHint(k, provenance, touched));
  // Labels, units and choices come from /meta fields when the engine has them.
  const field = (k: HomeKey) => meta?.fields.find((f) => f.name === WIRE[k]);
  const number = (key: HomeKey, fallback: string, icon: IconName, fallbackUnit: string | undefined, step: number) => {
    const f = field(key);
    const label = f?.label ?? fallback;
    const unit = f ? (f.unit ?? undefined) : fallbackUnit;
    return (
    <div className="space-y-1">
      <Label icon={icon} htmlFor={`f-${key}`} hint={hint(key)}>{label}</Label>
      <div className="flex items-center gap-2">
        <input
          id={`f-${key}`}
          type="number"
          inputMode="decimal"
          min={0}
          step={step}
          placeholder="Unknown"
          className={inputClass}
          value={typeof home[key] === "number" ? (home[key] as number) : ""}
          onChange={(e) => {
            if (e.target.value === "") setHome({ [key]: null }, key);
            else if (Number.isFinite(e.target.valueAsNumber)) setHome({ [key]: e.target.valueAsNumber }, key);
          }}
        />
        {unit && <span className="w-14 shrink-0 text-xs text-muted">{unit}</span>}
      </div>
    </div>
    );
  };
  return (
    <Card className="space-y-3 p-4">
      {number("demandKwh", "Annual electricity use", "zap", "kWh/yr", 100)}
      {number("persons", "People in household", "users", undefined, 1)}
      <div className="space-y-1">
        <Label icon="flame" htmlFor="f-heating" hint={hint("heatingType")}>{field("heatingType")?.label ?? "Current heating"}</Label>
        <select id="f-heating" className={inputClass} value={home.heatingType} onChange={(e) => setHome({ heatingType: e.target.value }, "heatingType")}>
          {(field("heatingType")?.choices.length ? field("heatingType")!.choices : Object.keys(HEATING_LABEL)).map((v) => (
            <option key={v} value={v}>{HEATING_LABEL[v] ?? v}</option>
          ))}
        </select>
      </div>
      <div className="space-y-1">
        <Label icon="car" hint={hint("hasEv")}>{field("hasEv")?.label ?? "Electric car"}</Label>
        <Segmented
          name="f-ev"
          label={field("hasEv")?.label ?? "Electric car"}
          value={home.hasEv ? "yes" : "no"}
          options={[{ value: "yes", label: "Yes" }, { value: "no", label: "No" }]}
          onChange={(v) => setHome({ hasEv: v === "yes" }, "hasEv")}
        />
      </div>
      {home.hasEv && number("evKm", "Car distance", "route", "km/yr", 500)}
      {number("roofModules", "Roof fits about", "home", "modules", 1)}
      {meta && meta.installers.length > 1 && (
        <div className="space-y-1">
          <label htmlFor="f-installer" className="text-sm text-ink">Installer style</label>
          <select id="f-installer" className={inputClass} value={inputs.installerId} onChange={(e) => setInstaller(e.target.value)}>
            {!meta.installers.includes(inputs.installerId) && <option value={inputs.installerId}>{inputs.installerId.slice(0, 8)}</option>}
            {meta.installers.map((id) => (
              <option key={id} value={id}>{id.slice(0, 8)}</option>
            ))}
          </select>
        </div>
      )}
    </Card>
  );
}

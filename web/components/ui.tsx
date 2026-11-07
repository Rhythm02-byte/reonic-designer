// Small Reonic-style building blocks shared by the planner and the homeowner view.
import type { ComponentProps, ReactNode } from "react";

export function Logo() {
  return (
    <span className="flex items-center gap-2 text-[15px] font-semibold tracking-tight text-ink">
      <svg viewBox="0 0 24 24" className="size-5" aria-hidden>
        <path d="M12 2 3 9v13h6v-7h6v7h6V9z" fill="currentColor" />
        <path d="M12 2 3 9h18z" fill="#10B981" />
      </svg>
      Home Energy Designer
    </span>
  );
}

const PERSONA = {
  planner: "bg-blue-50 text-blue-700 ring-blue-200",
  homeowner: "bg-emerald-50 text-emerald-700 ring-emerald-200",
};
export function PersonaChip({ who }: { who: keyof typeof PERSONA }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ring-1 ${PERSONA[who]}`}>{who}</span>
  );
}

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ComponentProps<"button"> & { variant?: "primary" | "secondary" | "ghost" }) {
  const look = {
    primary: "bg-ink text-paper hover:bg-ink/85",
    secondary: "bg-white text-ink ring-1 ring-zinc-200 hover:bg-sand-2",
    ghost: "text-body hover:bg-sand",
  }[variant];
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500 disabled:opacity-40 ${look} ${className}`}
      {...props}
    />
  );
}

export function Card({ className = "", ...props }: ComponentProps<"div">) {
  return <div className={`rounded-2xl bg-white shadow-sm ring-1 ring-zinc-200 ${className}`} {...props} />;
}

const TONE = { good: "bg-emerald-50 text-emerald-700", warn: "bg-amber-50 text-amber-800" };
export function Badge({ tone, children }: { tone: keyof typeof TONE; children: ReactNode }) {
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${TONE[tone]}`}>{children}</span>;
}

export function Stat({ label, value, sub }: { label: string; value: ReactNode; sub?: ReactNode }) {
  return (
    <div className="min-w-0">
      <div className="text-xs text-muted">{label}</div>
      <div className="truncate text-lg font-semibold tracking-tight text-ink tabular-nums">{value}</div>
      {sub && <div className="text-xs text-muted">{sub}</div>}
    </div>
  );
}

export function ErrorNote({ error }: { error: string | null }) {
  if (!error) return null;
  return (
    <div role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-800 ring-1 ring-rose-200">
      {error}
    </div>
  );
}

/** Radio-button group styled as a segmented control; keyboard and screen readers get native radios. */
export function Segmented<T extends string | number>({
  name,
  label,
  value,
  options,
  onChange,
}: {
  name: string;
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <fieldset className="min-w-0">
      <legend className="sr-only">{label}</legend>
      <div className="flex flex-wrap gap-1 rounded-full bg-sand p-1">
        {options.map((o) => (
          <label
            key={String(o.value)}
            className="flex-1 cursor-pointer rounded-full px-3 py-1 text-center text-sm whitespace-nowrap text-body transition-colors has-checked:bg-white has-checked:font-medium has-checked:text-ink has-checked:shadow-sm has-focus-visible:outline-2 has-focus-visible:outline-emerald-500"
          >
            <input
              type="radio"
              className="sr-only"
              name={name}
              checked={o.value === value}
              onChange={() => onChange(o.value)}
            />
            {o.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

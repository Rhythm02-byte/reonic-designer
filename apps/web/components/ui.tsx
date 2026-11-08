// Small Reonic-style building blocks shared by the planner and the homeowner view (see ../../DESIGN.md).
import type { ComponentProps, ReactNode } from "react";

// Rhythm: an ink rounded square with three rising bars (output over a day), plus the wordmark in Geist.
export function Logo({ product = true }: { product?: boolean }) {
  return (
    <span className="flex items-center gap-3 text-ink">
      <span className="flex cursor-default items-center gap-2 select-none" role="img" aria-label="Rhythm"> {/* ours: no text selection on the triple-tap menu gesture */}
        <svg viewBox="0 0 24 24" className="size-6" aria-hidden>
          <rect width="24" height="24" rx="7" fill="currentColor" />
          <g stroke="var(--color-paper)" strokeWidth={2.5} strokeLinecap="round">
            <path d="M7.5 15v2" />
            <path d="M12 11v6" />
            <path d="M16.5 7v10" />
          </g>
        </svg>
        <span aria-hidden className="text-[19px] leading-none font-semibold tracking-[-0.03em]">
          Rhythm
        </span>
      </span>
      {product && (
        <>
          <span aria-hidden className="h-4 w-px bg-zinc-300" />
          <span className="text-sm font-medium tracking-tight">Home Energy Designer</span>
        </>
      )}
    </span>
  );
}

export function PersonaChip({ who }: { who: "planner" | "homeowner" }) {
  return (
    <span className="rounded-full bg-sand px-2.5 py-0.5 text-xs font-medium text-quiet capitalize ring-1 ring-zinc-200">
      {who}
    </span>
  );
}

export function Header({ width, children }: { width: string; children?: ReactNode }) {
  return (
    <header className="sticky top-0 z-30 border-b border-zinc-200 bg-paper">
      <div className={`mx-auto flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 sm:px-6 ${width}`}>{children}</div>
    </header>
  );
}

export function Footer({ width, children }: { width: string; children: ReactNode }) {
  return (
    <footer className="mt-12 border-t border-zinc-200 bg-sand">
      <div className={`mx-auto px-4 py-6 text-xs text-quiet sm:px-6 ${width}`}>{children}</div>
    </footer>
  );
}

// Lucide icons (ISC), inlined so the kit needs no icon dependency.
const ICONS = {
  zap: <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z" />,
  users: (
    <>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </>
  ),
  flame: <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />,
  car: (
    <>
      <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2" />
      <circle cx="7" cy="17" r="2" />
      <path d="M9 17h6" />
      <circle cx="17" cy="17" r="2" />
    </>
  ),
  route: (
    <>
      <circle cx="6" cy="19" r="3" />
      <path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15" />
      <circle cx="18" cy="5" r="3" />
    </>
  ),
  wallet: (
    <>
      <path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1" />
      <path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4" />
    </>
  ),
  trend: (
    <>
      <path d="M22 7 13.5 15.5 8.5 10.5 2 17" />
      <path d="M16 7h6v6" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </>
  ),
  arrow: (
    <>
      <path d="M7 7h10v10" />
      <path d="M7 17 17 7" />
    </>
  ),
  pin: (
    <>
      <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
      <circle cx="12" cy="10" r="3" />
    </>
  ),
  // ours: icons for the presenter menu
  present: (
    <>
      <rect x="2" y="3" width="20" height="14" rx="2" />
      <path d="M8 21h8M12 17v4" />
    </>
  ),
  chart: (
    <>
      <path d="M3 3v16a2 2 0 0 0 2 2h16" />
      <path d="M18 17V9M13 17V5M8 17v-3" />
    </>
  ),
};
export type IconName = keyof typeof ICONS;

export function Icon({ name, className = "size-4 text-blue-600" }: { name: IconName; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`shrink-0 ${className}`}
      aria-hidden
    >
      {ICONS[name]}
    </svg>
  );
}

/** Blue filled disc with a check: "this is included". */
export function CheckDot({ className = "size-4" }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" className={`shrink-0 ${className}`} aria-hidden>
      <circle cx="10" cy="10" r="10" className="fill-blue-600" />
      <path d="m6 10.5 2.5 2.5L14 7.5" fill="none" stroke="white" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Muted outlined disc with a dash: "not in this setup". */
export function MinusDot({ className = "size-4" }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" className={`shrink-0 text-zinc-400 ${className}`} aria-hidden>
      <circle cx="10" cy="10" r="9" fill="none" stroke="currentColor" strokeWidth={1.5} />
      <path d="M6.5 10h7" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" />
    </svg>
  );
}

export function CheckList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-2">
      {items.map((l) => (
        <li key={l} className="flex gap-2.5">
          <CheckDot className="mt-0.5 size-4" />
          <span>{l}</span>
        </li>
      ))}
    </ul>
  );
}

const focus = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600";
export const pill = `inline-flex items-center justify-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${focus}`;
export const pillLook = {
  primary: "bg-ink text-paper hover:bg-ink/85",
  secondary: "bg-white text-ink ring-1 ring-zinc-200 hover:bg-sand-2",
  ghost: "text-body hover:bg-sand",
};

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ComponentProps<"button"> & { variant?: keyof typeof pillLook }) {
  // ours: the pointed "chevron" shape is gone (one rounded pill style everywhere)
  return <button type="button" className={`${pill} disabled:cursor-not-allowed disabled:opacity-40 ${pillLook[variant]} ${className}`} {...props} />;
}

export function Card({ className = "", ...props }: ComponentProps<"div">) {
  return <div className={`rounded-2xl border border-zinc-200 bg-white ${className}`} {...props} />;
}

// Used on the dark panel of the reality card: ink on emerald-400 / amber-400.
const TONE = { good: "bg-emerald-400 text-ink", warn: "bg-amber-400 text-ink" };
export function Badge({ tone, children }: { tone: keyof typeof TONE; children: ReactNode }) {
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${TONE[tone]}`}>{children}</span>;
}

export function Stat({ label, value, sub, icon }: { label: string; value: ReactNode; sub?: ReactNode; icon?: IconName }) {
  return (
    <div className="min-w-0">
      <div className="flex items-center gap-1.5 text-xs text-muted">
        {icon && <Icon name={icon} className="size-3.5 text-blue-600" />}
        {label}
      </div>
      <div className="mt-0.5 truncate text-lg font-semibold tracking-tight text-ink tabular-nums">{value}</div>
      {sub && <div className="text-xs text-muted">{sub}</div>}
    </div>
  );
}

export function ErrorNote({ error }: { error: string | null }) {
  if (!error) return null;
  return (
    <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
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
            className="flex-1 cursor-pointer rounded-full px-3 py-1 text-center text-sm whitespace-nowrap text-quiet transition-colors pointer-coarse:py-2.5 has-checked:bg-white has-checked:font-medium has-checked:text-ink has-checked:shadow-sm has-focus-visible:outline-2 has-focus-visible:outline-blue-600"
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

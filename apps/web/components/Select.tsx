"use client";
// ours: custom dropdown (button + listbox), split from ui.tsx so ui.tsx stays usable in server components.
import { createPortal } from "react-dom";
import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
// ours: custom control. A real listbox (no native <select>) so the open list matches the app.
export function Select({
  value,
  onChange,
  options,
  id,
  className = "",
  placeholder = "Select",
  disabled,
  "aria-label": ariaLabel,
}: {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  id?: string;
  className?: string;
  placeholder?: string;
  disabled?: boolean;
  "aria-label"?: string;
}) {
  const uid = useId();
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [pos, setPos] = useState<{ left: number; width: number; top?: number; bottom?: number } | null>(null);
  const wrap = useRef<HTMLSpanElement>(null);
  const btn = useRef<HTMLButtonElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const selected = options.findIndex((o) => o.value === value);

  const show = () => {
    if (disabled || options.length === 0) return;
    const r = btn.current?.getBoundingClientRect();
    if (!r) return;
    const up = window.innerHeight - r.bottom < 270 && r.top > window.innerHeight - r.bottom;
    // Fixed + portal: an ancestor with an animation would otherwise trap the list under later siblings.
    setPos({ left: r.left, width: r.width, ...(up ? { bottom: window.innerHeight - r.top + 4 } : { top: r.bottom + 4 }) });
    setActive(Math.max(selected, 0));
    setOpen(true);
  };
  const close = (refocus = true) => {
    setOpen(false);
    if (refocus) btn.current?.focus();
  };
  const pick = (i: number) => {
    const o = options[i];
    if (o && o.value !== value) onChange(o.value);
    close();
  };

  useEffect(() => {
    if (!open) return;
    const away = (e: PointerEvent) => {
      const t = e.target as Node;
      if (!wrap.current?.contains(t) && !list.current?.contains(t)) setOpen(false);
    };
    const shut = (e: Event) => {
      if (!list.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", away);
    window.addEventListener("scroll", shut, true);
    window.addEventListener("resize", shut);
    return () => {
      document.removeEventListener("pointerdown", away);
      window.removeEventListener("scroll", shut, true);
      window.removeEventListener("resize", shut);
    };
  }, [open]);
  useEffect(() => {
    if (open) list.current?.children[active]?.scrollIntoView({ block: "nearest" });
  }, [open, active]);

  const onKey = (e: KeyboardEvent) => {
    if (!open) {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        show();
      }
      return;
    }
    const last = options.length - 1;
    if (e.key === "ArrowDown") setActive((a) => Math.min(a + 1, last));
    else if (e.key === "ArrowUp") setActive((a) => Math.max(a - 1, 0));
    else if (e.key === "Home") setActive(0);
    else if (e.key === "End") setActive(last);
    else if (e.key === "Enter" || e.key === " ") pick(active);
    else if (e.key === "Escape") close();
    else if (e.key === "Tab") return setOpen(false);
    else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
      const k = e.key.toLowerCase();
      const n = options.length;
      for (let step = 1; step <= n; step++) {
        const i = (active + step) % n;
        if (options[i].label.toLowerCase().startsWith(k)) return setActive(i), e.preventDefault();
      }
      return;
    } else return;
    e.preventDefault();
  };

  return (
    <span ref={wrap} className={`relative inline-block w-full ${className}`}>
      <button
        ref={btn}
        id={id}
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? `${uid}-list` : undefined}
        aria-activedescendant={open ? `${uid}-${active}` : undefined}
        aria-label={ariaLabel}
        disabled={disabled}
        onClick={() => (open ? close() : show())}
        onKeyDown={onKey}
        className="flex w-full cursor-pointer items-center rounded-lg bg-white py-1.5 pr-8 pl-2.5 text-left text-sm text-ink ring-1 ring-zinc-200 transition-colors hover:ring-zinc-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <span className={`truncate ${selected < 0 ? "text-zinc-400" : ""}`}>{selected < 0 ? placeholder : options[selected].label}</span>
      </button>
      <svg viewBox="0 0 16 16" fill="none" aria-hidden="true" className={`pointer-events-none absolute top-1/2 right-2.5 size-4 -translate-y-1/2 text-muted transition-transform ${open ? "rotate-180" : ""}`}>
        <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {open && pos && createPortal(
        <ul
          ref={list}
          id={`${uid}-list`}
          role="listbox"
          aria-label={ariaLabel}
          style={{ left: pos.left, minWidth: pos.width, top: pos.top, bottom: pos.bottom }}
          className={`fixed z-50 max-h-64 overflow-auto rounded-xl bg-white p-1 text-sm shadow-lg ring-1 ring-zinc-200 transition duration-100 starting:scale-95 starting:opacity-0 ${pos.bottom === undefined ? "origin-top" : "origin-bottom"}`}
        >
          {options.map((o, i) => (
            <li
              key={o.value}
              id={`${uid}-${i}`}
              role="option"
              aria-selected={i === selected}
              onPointerEnter={() => setActive(i)}
              onClick={() => pick(i)}
              className={`flex cursor-pointer items-center justify-between gap-3 rounded-lg px-2.5 py-1.5 whitespace-nowrap text-ink ${i === active ? "bg-sand" : ""} ${i === selected ? "font-medium" : ""}`}
            >
              {o.label}
              {i === selected && (
                <svg viewBox="0 0 16 16" fill="none" aria-hidden="true" className="size-4 shrink-0 text-blue-600">
                  <path d="M3.5 8.5l3 3 6-6.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </li>
          ))}
        </ul>,
        document.body,
      )}
    </span>
  );
}

"use client";

// Hidden presenter menu: tap or click the logo three times quickly (or any element with data-hidden-menu-trigger).
// Mounted once in app/layout.tsx. It asks where to go: iemko's pitch mode (/pitch) or the Test Lab (/lab).
import Link from "next/link";
import { useEffect, useRef } from "react";

const TRIGGER = '[data-hidden-menu-trigger], [aria-label="Rhythm"]';
const TAPS = 3;
const WINDOW_MS = 700;

const ITEMS = [
  { href: "/pitch", title: "Pitch mode", note: "The guided deck with the live app, on the engine" },
  { href: "/pitch?demo=1", title: "Pitch mode, offline", note: "Same deck on labelled demo data, no engine needed" },
  { href: "/lab", title: "Lab results", note: "How often we match the experts, per run and branch" },
];

export default function HiddenMenu() {
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    let taps: number[] = [];
    const onClick = (e: MouseEvent) => {
      if (!(e.target instanceof Element) || !e.target.closest(TRIGGER)) return;
      const now = performance.now();
      taps = [...taps.filter((t) => now - t < WINDOW_MS), now];
      if (taps.length < TAPS) return;
      taps = [];
      e.preventDefault(); // the logo is a link home; the third tap opens the menu instead
      dialog.current?.showModal();
    };
    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, []);

  const close = () => dialog.current?.close();
  const item = "flex w-full flex-col rounded-xl px-4 py-3 text-left ring-1 ring-zinc-200 transition-colors hover:bg-zinc-50 focus-visible:outline-2 focus-visible:outline-blue-600";

  return (
    <dialog
      ref={dialog}
      aria-label="Presenter menu"
      onClick={(e) => e.target === dialog.current && close()} // click on the backdrop closes
      className="m-auto w-[min(92vw,22rem)] rounded-2xl border border-zinc-200 bg-white p-0 text-ink shadow-xl backdrop:bg-black/30"
    >
      <div className="space-y-2 p-4">
        <p className="px-1 text-xs font-medium text-muted">Where to?</p>
        {ITEMS.map((i) => (
          <Link key={i.href} href={i.href} onClick={close} className={item}>
            <span className="text-sm font-semibold">{i.title}</span>
            <span className="text-xs text-muted">{i.note}</span>
          </Link>
        ))}
        <button type="button" onClick={close} className="w-full rounded-full px-4 py-2 text-sm text-muted hover:bg-zinc-50">
          Close
        </button>
      </div>
    </dialog>
  );
}

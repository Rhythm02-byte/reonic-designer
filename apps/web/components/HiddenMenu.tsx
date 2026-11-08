"use client";

// Hidden presenter menu: tap or click the logo three times quickly (or any element with data-hidden-menu-trigger).
// Mounted once in app/layout.tsx. Pitch mode lives at /pitch (iemko's branch); until that route exists it shows as
// unavailable instead of leading to a 404 during a demo.
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

const TRIGGER = '[data-hidden-menu-trigger], [aria-label="Rhythm"]';
const TAPS = 3;
const WINDOW_MS = 700;

export default function HiddenMenu() {
  const dialog = useRef<HTMLDialogElement>(null);
  const [pitchReady, setPitchReady] = useState<boolean | null>(null);

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
      fetch("/pitch", { method: "HEAD" }).then((r) => setPitchReady(r.ok), () => setPitchReady(false));
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
        <p className="px-1 text-xs font-medium text-muted">Presenter menu</p>
        {pitchReady ? (
          <Link href="/pitch" onClick={close} className={item}>
            <span className="text-sm font-semibold">Pitch mode</span>
            <span className="text-xs text-muted">The guided demo for the jury</span>
          </Link>
        ) : (
          <div aria-disabled className={`${item} cursor-not-allowed opacity-50 hover:bg-transparent`}>
            <span className="text-sm font-semibold">Pitch mode</span>
            <span className="text-xs text-muted">{pitchReady === null ? "Checking…" : "Not on this branch yet"}</span>
          </div>
        )}
        <Link href="/lab" onClick={close} className={item}>
          <span className="text-sm font-semibold">Lab results</span>
          <span className="text-xs text-muted">How often we match the experts, per run and branch</span>
        </Link>
        <button type="button" onClick={close} className="w-full rounded-full px-4 py-2 text-sm text-muted hover:bg-zinc-50">
          Close
        </button>
      </div>
    </dialog>
  );
}

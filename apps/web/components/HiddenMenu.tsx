"use client";

// Hidden presenter menu: tap or click the logo three times quickly (or any element with data-hidden-menu-trigger).
// Mounted once in app/layout.tsx. It asks where to go: iemko's pitch mode (/pitch) or the Test Lab (/lab).
import Link from "next/link";
import { motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { pill, pillLook, Segmented } from "./ui";

const TRIGGER = '[data-hidden-menu-trigger], [aria-label="Rhythm"]';
const TAPS = 3;
const WINDOW_MS = 700;

// ours: two entries; the pitch card carries a Live / Offline choice instead of two separate items
type PitchMode = "live" | "offline";
const PITCH_MODES: { value: PitchMode; label: string }[] = [{ value: "live", label: "Live" }, { value: "offline", label: "Offline" }];
const PITCH_HREF: Record<PitchMode, string> = { live: "/pitch", offline: "/pitch?demo=1" };

export default function HiddenMenu() {
  const dialog = useRef<HTMLDialogElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const [openCount, setOpenCount] = useState(0);
  const [pitchMode, setPitchMode] = useState<PitchMode>("live");

  useEffect(() => {
    if (dialog.current?.open) closeButton.current?.focus();
  }, [openCount]);

  useEffect(() => {
    let taps: number[] = [];
    const onClick = (e: MouseEvent) => {
      if (!(e.target instanceof Element) || !e.target.closest(TRIGGER)) return;
      const now = performance.now();
      taps = [...taps.filter((t) => now - t < WINDOW_MS), now];
      if (taps.length < TAPS) return;
      taps = [];
      e.preventDefault(); // the logo is a link home; the third tap opens the menu instead
      setOpenCount((count) => count + 1);
      dialog.current?.showModal();
      window.getSelection()?.removeAllRanges();
    };
    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, []);

  const close = () => dialog.current?.close();
  const item = "group flex min-h-16 w-full items-center gap-3 rounded-xl px-3 py-3 text-left ring-1 ring-zinc-200 transition-colors hover:bg-sand-2 focus-visible:outline-2 focus-visible:outline-blue-600";

  return (
    <dialog
      ref={dialog}
      aria-label="Presenter menu"
      onClick={(e) => e.target === dialog.current && close()} // click on the backdrop closes
      className="m-auto w-[min(92vw,26rem)] rounded-2xl border border-zinc-200 bg-white p-0 text-ink shadow-xl backdrop:bg-ink/40"
    >
      <motion.div key={openCount} initial={{ opacity: 0, y: 8, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.18, ease: "easeOut" }} className="overflow-hidden rounded-2xl">
        <div className="flex items-start justify-between border-b border-zinc-200 bg-sand-2 px-5 py-4">
          <div><p className="text-xs font-medium uppercase tracking-wide text-quiet">Rhythm · presenter tools</p><h2 className="mt-1 text-lg font-semibold">Where do you want to go?</h2><p className="mt-1 text-sm text-quiet">Choose a mode for the next part of the demo.</p></div>
          <button ref={closeButton} type="button" onClick={close} aria-label="Close menu" className="grid size-9 shrink-0 place-items-center rounded-full text-lg text-quiet transition-colors hover:bg-white focus-visible:outline-2 focus-visible:outline-blue-600">×</button>
        </div>
        <div className="space-y-2 p-4">
          <div className="rounded-xl px-3 py-3 ring-1 ring-zinc-200">
            <div className="flex items-center gap-3">
              <span className="grid size-10 shrink-0 place-items-center rounded-full bg-sand text-sm font-semibold text-ink ring-1 ring-zinc-200">01</span>
              <span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-ink">Pitch mode</span><span className="mt-0.5 block text-xs leading-relaxed text-quiet">The guided deck with the live app</span></span>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <div className="min-w-0 flex-1"><Segmented name="pitch-mode" label="Pitch data" value={pitchMode} options={PITCH_MODES} onChange={setPitchMode} /></div>
              <Link href={PITCH_HREF[pitchMode]} onClick={close} className={`${pill} ${pillLook.primary} shrink-0`}>Start</Link>
            </div>
            <p className="mt-2 text-xs text-quiet">Offline uses labelled demo data, no engine.</p>
          </div>
          <Link href="/lab" onClick={close} className={item}>
            <span className="grid size-10 shrink-0 place-items-center rounded-full bg-sand text-sm font-semibold text-ink ring-1 ring-zinc-200 transition-colors group-hover:bg-white">02</span>
            <span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-ink">Lab results</span><span className="mt-0.5 block text-xs leading-relaxed text-quiet">How often we match the experts, per run and branch</span></span>
            <span aria-hidden className="text-lg text-quiet transition-transform group-hover:translate-x-0.5">›</span>
          </Link>
          <p className="px-2 pt-1 text-center text-xs text-quiet">Press Escape to close</p>
        </div>
      </motion.div>
    </dialog>
  );
}

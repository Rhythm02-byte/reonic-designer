"use client";

// Hidden presenter menu: tap or click the logo three times quickly (or any element with data-hidden-menu-trigger).
// Mounted once in app/layout.tsx. It asks where to go: iemko's pitch mode (/pitch) or the Test Lab (/lab).
import Link from "next/link";
import { motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { Icon, Segmented } from "./ui";

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
  // ours: minimal rows, icon + one word; a row click goes
  const row = "flex min-h-14 items-center gap-3 rounded-xl px-3 ring-1 ring-zinc-200 transition-colors hover:bg-sand-2 focus-within:bg-sand-2";
  const go = "flex min-h-14 flex-1 cursor-pointer items-center gap-3 rounded-xl text-sm font-semibold text-ink focus-visible:outline-2 focus-visible:outline-blue-600";

  return (
    <dialog
      ref={dialog}
      aria-label="Presenter menu"
      onClick={(e) => e.target === dialog.current && close()} // click on the backdrop closes
      className="m-auto w-[min(92vw,22rem)] rounded-2xl border border-zinc-200 bg-white p-0 text-ink shadow-xl backdrop:bg-ink/40"
    >
      <motion.div key={openCount} initial={{ opacity: 0, y: 8, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.18, ease: "easeOut" }} className="relative space-y-2 p-3">
        <button ref={closeButton} type="button" onClick={close} aria-label="Close menu" className="absolute right-1 top-1 grid size-7 cursor-pointer place-items-center rounded-full text-quiet transition-colors hover:bg-sand-2 focus-visible:outline-2 focus-visible:outline-blue-600"><span aria-hidden>×</span></button>
        <div className={`${row} mt-5`}>
          <Link href={PITCH_HREF[pitchMode]} onClick={close} className={go}><Icon name="present" className="size-5 text-quiet" />Pitch</Link>
          <div className="w-36 shrink-0"><Segmented name="pitch-mode" label="Pitch data" value={pitchMode} options={PITCH_MODES} onChange={setPitchMode} /></div>
        </div>
        <div className={row}>
          <Link href="/lab" onClick={close} className={go}><Icon name="chart" className="size-5 text-quiet" />Lab</Link>
        </div>
      </motion.div>
    </dialog>
  );
}

"use client";
// Share with the customer: what they may change, the link and a QR code for it. A native <dialog> gives focus
// trapping, Escape and a backdrop for free.
import QRCode from "qrcode";
import { useEffect, useRef, useState } from "react";
import { haptic } from "@/lib/haptics";
import { HOME_NAME, num, UNIT } from "@/lib/format";
import { buildOptions, encodeOffer } from "@/lib/offer";
import { TARGETS } from "@/lib/types";
import type { HomeInputs, Meta, Sizes, Target } from "@/lib/types";
import { Button, pill, pillLook } from "./ui";

function Dialog({ url, options, onClose }: { url: string; options: Record<Target, number[]>; onClose: () => void }) {
  const [qr, setQr] = useState<string | null | undefined>(undefined);
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    let live = true;
    QRCode.toDataURL(url, { margin: 1, width: 360, errorCorrectionLevel: "L" }).then(
      (d) => live && setQr(d),
      () => live && setQr(null), // the link is too long for a QR code
    );
    return () => {
      live = false;
    };
  }, [url]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      haptic("success");
    } catch {
      setCopied(false);
    }
  };
  const changeable = TARGETS.filter((t) => options[t].length > 1);
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <h2 id="share-title" className="text-lg font-semibold text-ink">Share with customer</h2>
        <Button variant="ghost" onClick={onClose}>Close</Button>
      </div>
      <div className="text-sm">
        {changeable.length ? (
          <>
            <p>Your customer can switch between these options. Everything else stays as designed.</p>
            <ul className="mt-2 space-y-1">
              {changeable.map((t) => (
                <li key={t}>
                  <span className="font-medium text-ink">{HOME_NAME[t]}:</span>{" "}
                  {options[t].map((v) => (v === 0 ? "none" : `${num(v)} ${UNIT[t]}`)).join(", ")}
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p>This offer has no options: your customer sees the design as it is.</p>
        )}
      </div>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
        <div className="mx-auto size-44 shrink-0 rounded-xl bg-white p-1 ring-1 ring-zinc-200 sm:mx-0">
          {qr ? (
            // eslint-disable-next-line @next/next/no-img-element -- a data URL, nothing to optimise
            <img src={qr} alt="QR code for the offer link" className="size-full" />
          ) : (
            <p className="grid size-full place-items-center p-3 text-center text-xs text-muted">
              {qr === null ? "This link is too long for a QR code. Copy it instead." : "Making QR code…"}
            </p>
          )}
        </div>
        <div className="min-w-0 flex-1 space-y-2">
          <label htmlFor="share-url" className="text-xs text-muted">Offer link</label>
          <input id="share-url" readOnly value={url} onFocus={(e) => e.currentTarget.select()} className="w-full rounded-lg bg-white px-2.5 py-1.5 text-sm text-ink ring-1 ring-zinc-200 focus:ring-2 focus:ring-blue-600 focus:outline-none pointer-coarse:min-h-11" />
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={copy}>Copy link</Button>
            <a href={url} target="_blank" rel="noopener" className={`${pill} ${pillLook.secondary}`}>
              Open offer<span className="sr-only"> (new tab)</span>
            </a>
            <span aria-live="polite" className="text-xs text-quiet">{copied ? "Copied" : ""}</span>
          </div>
          <p className="text-xs text-muted">The link carries this home&apos;s data. Send it only to this customer.</p>
        </div>
      </div>
    </div>
  );
}

export function ShareDialog({ open, onClose, meta, sizes, inputs }: { open: boolean; onClose: () => void; meta: Meta | null; sizes: Sizes | null; inputs: HomeInputs }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);

  let body = null;
  if (open && meta && sizes) {
    const catalogs = Object.fromEntries(meta.targets.map((t) => [t.name, t.catalog])) as Record<Target, number[]>;
    const options = buildOptions(sizes, catalogs);
    const url = `${window.location.origin}/offer#${encodeOffer({ v: 2, inputs, recommended: sizes, options })}`;
    body = <Dialog key={url} url={url} options={options} onClose={onClose} />;
  }
  return (
    <dialog
      ref={ref}
      onClose={onClose}
      aria-labelledby="share-title"
      className="m-auto w-[min(36rem,calc(100%-2rem))] rounded-2xl border border-zinc-200 bg-paper p-5 text-body backdrop:bg-ink/40"
    >
      {body}
    </dialog>
  );
}


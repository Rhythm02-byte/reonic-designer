"use client";
// ours: ONE share entry point for the homeowner link (replaces the preview/share chevron pair + the separate QR button).
// The panel leads with the QR code (the customer scans it across the desk), then copy link / open the homeowner view.
import QRCode from "qrcode";
import { useEffect, useRef, useState } from "react";
import { encodeOffer, type Offer } from "@/lib/copy";
import { Button, Icon, pill, pillLook } from "./ui";

export function Share({ offer }: { offer: Offer | null }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState<"yes" | "failed" | null>(null);
  const [qr, setQr] = useState<{ url: string; img: string | null } | null>(null);
  // The link carries this home's data in its hash: send it only to this customer.
  const url = offer && typeof location !== "undefined" ? new URL(`/offer#${encodeOffer(offer)}`, location.href).href : null;

  useEffect(() => {
    if (!open || !url || qr?.url === url) return;
    let live = true;
    QRCode.toDataURL(url, { margin: 1, width: 360, errorCorrectionLevel: "L" }).then(
      (img) => live && setQr({ url, img }),
      () => live && setQr({ url, img: null }), // too long for a QR code
    );
    return () => {
      live = false;
    };
  }, [open, url, qr?.url]);

  const show = () => {
    setCopied(null);
    setOpen(true);
    dialog.current?.showModal();
  };
  const close = () => dialog.current?.close();
  const copy = () => url && navigator.clipboard.writeText(url).then(() => setCopied("yes"), () => setCopied("failed"));
  const img = qr?.url === url ? qr.img : undefined;

  return (
    <>
      <Button disabled={!offer} onClick={show} aria-haspopup="dialog">
        Share with homeowner <Icon name="arrow" className="size-4" />
      </Button>
      <dialog
        ref={dialog}
        aria-labelledby="share-h"
        onClose={() => setOpen(false)}
        onClick={(e) => e.target === dialog.current && close()}
        className="m-auto w-[min(92vw,360px)] rounded-2xl bg-white p-5 text-sm text-body shadow-xl ring-1 ring-zinc-200 backdrop:bg-ink/40"
      >
        <h2 id="share-h" className="text-base font-semibold text-ink">Share with the homeowner</h2>
        <p className="mt-1 text-xs text-muted">Scan on their phone, or send the link. It carries this home&apos;s data: share it only with this customer.</p>
        <div className="mt-4 grid aspect-square place-items-center rounded-xl bg-white ring-1 ring-zinc-200">
          {img ? (
            // eslint-disable-next-line @next/next/no-img-element -- a data: URL, nothing for next/image to optimise
            <img src={img} alt="QR code for the homeowner offer link" className="size-full rounded-xl" />
          ) : (
            <p className="p-6 text-center text-xs text-quiet">{img === null ? "This link is too long for a QR code: copy it instead." : "Making QR code…"}</p>
          )}
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <Button onClick={copy}>{copied === "yes" ? "Link copied" : "Copy link"}</Button>
          {url && (
            <a href={url} target="_blank" rel="noopener" className={`${pill} ${pillLook.secondary}`}>
              Open view<span className="sr-only"> (opens in a new tab)</span>
            </a>
          )}
        </div>
        <p aria-live="polite" className="mt-2 min-h-4 text-xs text-quiet">{copied === "failed" ? "Copy failed: open the view and copy its address." : ""}</p>
        <button type="button" onClick={close} className="mt-1 w-full rounded-full px-4 py-1.5 text-sm text-muted hover:bg-sand">
          Close
        </button>
      </dialog>
    </>
  );
}

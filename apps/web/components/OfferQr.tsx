"use client";
// ours: a QR code for the homeowner link, next to his "Preview homeowner view" / "Share offer" pair, so the customer
// can open the offer on their phone across the desk. Same link his OfferLinks builds; native <dialog> for focus.
import QRCode from "qrcode";
import { useEffect, useRef, useState } from "react";
import { encodeOffer, type Offer } from "@/lib/copy";
import { Button } from "./ui";

export function OfferQr({ offer }: { offer: Offer | null }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [open, setOpen] = useState(false);
  const [qr, setQr] = useState<{ url: string; img: string | null } | null>(null);
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
    setOpen(true);
    dialog.current?.showModal();
  };
  const close = () => dialog.current?.close();
  const img = qr?.url === url ? qr.img : undefined;

  return (
    <>
      <Button variant="secondary" disabled={!offer} onClick={show} aria-haspopup="dialog">
        QR code
      </Button>
      <dialog
        ref={dialog}
        aria-labelledby="offer-qr"
        onClose={() => setOpen(false)}
        onClick={(e) => e.target === dialog.current && close()}
        className="m-auto w-[min(92vw,380px)] rounded-2xl bg-white p-5 text-sm text-body shadow-xl ring-1 ring-zinc-200 backdrop:bg-ink/40"
      >
        <h2 id="offer-qr" className="text-base font-semibold text-ink">
          Homeowner view
        </h2>
        <p className="mt-1 text-xs text-muted">Scan to open this offer on a phone. The code carries the home&apos;s data: show it only to this customer.</p>
        <div className="mt-4 grid aspect-square place-items-center rounded-xl bg-white ring-1 ring-zinc-200">
          {img ? (
            // eslint-disable-next-line @next/next/no-img-element -- a data: URL, nothing for next/image to optimise
            <img src={img} alt="QR code for the homeowner offer link" className="size-full rounded-xl" />
          ) : (
            <p className="p-6 text-center text-xs text-quiet">
              {img === null ? "This link is too long for a QR code. Use Share offer to copy it." : "Making QR code…"}
            </p>
          )}
        </div>
        <div className="mt-4 flex justify-end">
          <Button variant="secondary" onClick={close}>
            Close
          </Button>
        </div>
      </dialog>
    </>
  );
}

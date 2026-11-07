import type { Metadata } from "next";
import Offer from "@/components/Offer";

// The offer lives in the URL hash, so it never reaches a server log, and the page stays out of search engines.
export const metadata: Metadata = { title: "Your offer · Home Energy Designer", robots: { index: false, follow: false } };

export default function OfferRoute() {
  return <Offer />;
}

import type { Metadata } from "next";
import Pitch from "@/components/pitch/Pitch";

// The pitch deck around the live app. Add ?demo=1 to run on the labelled demo data without the engine.
export const metadata: Metadata = { title: "Pitch · Home Energy Designer", robots: { index: false, follow: false } };

export default function PitchPage() {
  return <Pitch />;
}

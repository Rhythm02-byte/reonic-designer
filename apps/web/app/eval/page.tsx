import type { Metadata } from "next";
import EvalReport from "@/components/EvalReport";

export const metadata: Metadata = { title: "Evaluation · Home Energy Designer" };

export default function EvalPage() {
  return <EvalReport />;
}

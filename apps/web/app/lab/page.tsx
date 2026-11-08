import type { Metadata } from "next";
import { connection } from "next/server";
import { readFile } from "node:fs/promises";
import Lab from "@/components/lab/Lab";
import { parseHistory } from "@/lib/lab";
import { historyFile, repoRoot } from "@/lib/lab-server";

export const metadata: Metadata = { title: "Test Lab · Home Energy Designer", robots: { index: false, follow: false } };

async function load() {
  const root = repoRoot();
  if (!root) return { runs: [], invalid: 0, canRun: false };
  const text = await readFile(historyFile(root), "utf8").catch(() => "");
  return { ...parseHistory(text), canRun: process.env.NODE_ENV !== "production" };
}

export default async function LabPage() {
  await connection(); // read the history on every request, not at build time
  const { runs, invalid, canRun } = await load();
  return <Lab runs={runs} invalid={invalid} canRun={canRun} />;
}

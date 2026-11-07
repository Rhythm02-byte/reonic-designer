import type { Metadata } from "next";
import { connection } from "next/server";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import Lab from "@/components/lab/Lab";
import { parseHistory } from "@/lib/lab";
import "./lab.css";

export const metadata: Metadata = { title: "Test Lab · Home Energy Designer", robots: { index: false, follow: false } };

async function history() {
  let directory = process.cwd();
  while (true) {
    // Locate the repository even when its history file has not been seeded yet.
    try {
      await stat(path.join(directory, "eval"));
      try { return { ...parseHistory(await readFile(path.join(directory, "eval", "history", "runs.jsonl"), "utf8")), error: false }; }
      catch (error) {
        if ((error as NodeJS.ErrnoException).code === "ENOENT") return { runs: [], invalid: 0, error: false };
        throw error;
      }
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") return { runs: [], invalid: 0, error: true };
    }
    const parent = path.dirname(directory);
    if (parent === directory) return { runs: [], invalid: 0, error: false };
    directory = parent;
  }
}

export default async function LabPage() {
  await connection();
  const data = await history();
  return <main className="test-lab"><p className="lab-eyebrow">Home Energy Designer / Test Lab</p>
    {data.error ? <section role="alert" className="lab-error"><h1>Run history could not be read</h1><p>Check file permissions for eval/history/runs.jsonl, then reload.</p></section>
      : <><p role={data.invalid ? "status" : undefined}>{data.invalid > 0 && `${data.invalid} invalid history line(s) skipped. Check the history file before comparing runs.`}</p><Lab runs={data.runs} /></>}
  </main>;
}

import { spawn } from "node:child_process";
import { mkdir, open, readFile, unlink, writeFile } from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { repoRoot } from "./lab-server";

export type CheckJob = {
  id: string; mode: "checks" | "exam"; state: "running" | "passed" | "failed" | "interrupted";
  stage: string; completed: string[]; startedAt: string; updatedAt: string; pid?: number; error?: string;
};
const paths = () => {
  const root = repoRoot();
  if (!root) throw new Error("Repository root not found.");
  const dir = path.join(root, ".cache", "lab");
  return { root, dir, file: path.join(dir, "job.json"), lock: path.join(dir, "run.lock") };
};
export async function checkStatus(): Promise<CheckJob | null> {
  const { file } = paths();
  let job: CheckJob;
  try { job = JSON.parse(await readFile(file, "utf8")); } catch { return null; }
  if (job.state === "running" && Date.now() - Date.parse(job.updatedAt) > 15_000) {
    let alive = false;
    if (job.pid) { try { process.kill(job.pid, 0); alive = true; } catch { /* worker exited */ } }
    if (!alive) return { ...job, state: "interrupted", stage: "Worker stopped; retry the checks." };
  }
  return job;
}
export async function startChecks(mode: "checks" | "exam", label: string): Promise<CheckJob> {
  const { root, dir, file, lock } = paths();
  await mkdir(dir, { recursive: true });
  const previous = await checkStatus();
  if (previous?.state === "running") throw new Error("A check is already running.");
  if (previous) await unlink(lock).catch(() => {});
  const handle = await open(lock, "wx").catch(() => { throw new Error("A check is already starting. Refresh its status."); });
  await handle.close();
  const job: CheckJob = { id: randomUUID(), mode, state: "running", stage: "Starting", completed: [], startedAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
  try {
    await writeFile(file, JSON.stringify(job));
    const child = spawn(process.execPath, [path.join(root, "apps/web/scripts/lab-runner.mjs"), root, job.id, mode, label.slice(0, 80)], {
      cwd: root, windowsHide: true, stdio: "ignore", env: { ...process.env, OFFLINE: "1" },
    });
    await new Promise<void>((resolve, reject) => { child.once("spawn", resolve); child.once("error", reject); });
    job.pid = child.pid;
    child.unref();
    return job;
  } catch (error) {
    await unlink(lock).catch(() => {});
    job.state = "failed"; job.error = error instanceof Error ? error.message : "Worker could not start.";
    await writeFile(file, JSON.stringify(job));
    throw error;
  }
}

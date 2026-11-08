import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { randomUUID, createHash } from "node:crypto";
import os from "node:os";
import path from "node:path";
import { repoRoot } from "./lab-server";
import { locationKey, type HouseJob } from "./real-house";

export function housePaths(id?: string) {
  const root = repoRoot();
  if (!root) throw new Error("Repository root not found.");
  if (id !== undefined && !/^[0-9a-f-]{36}$/.test(id)) throw new Error("Invalid model id.");
  const cache = path.join(root, ".cache", "real-house");
  const dir = id ? path.join(cache, "jobs", id) : cache;
  return { root, cache, dir, status: path.join(dir, "job.json"), glb: path.join(dir, "house.glb") };
}
export async function houseStatus(id: string): Promise<HouseJob | null> {
  const { status } = housePaths(id);
  let job: HouseJob;
  try { job = JSON.parse(await readFile(status, "utf8")); } catch { return null; }
  // ours: a worker that died before writing job.pid left the job "running" forever
  if (job.state === "running" && !job.pid && Date.now() - Date.parse(job.startedAt) > 30_000) return { ...job, state: "failed", error: "The import did not start" };
  if (job.state === "running" && Date.now() - Date.parse(job.updatedAt) > 20_000 && job.pid) {
    try { process.kill(job.pid, 0); } catch { return { ...job, state: "failed", error: "The import worker stopped. Retry the import." }; }
  }
  return job;
}
const indexPath = (cache: string, key: string) => path.join(cache, `index-${createHash("sha256").update(key).digest("hex").slice(0, 20)}.json`);
// ours: a finished import for this exact location, without starting a new export (lets the planner open the mesh by default)
export async function findHouse(lat: number, lng: number): Promise<HouseJob | null> {
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  const { cache } = housePaths();
  try {
    const job = await houseStatus(JSON.parse(await readFile(indexPath(cache, locationKey(lat, lng)), "utf8")).id);
    return job && job.state === "ready" && existsSync(housePaths(job.id).glb) ? job : null;
  } catch { return null; }
}
export async function startHouse(lat: number, lng: number): Promise<HouseJob> {
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 85 || Math.abs(lng) > 180) throw new Error("Choose a valid map location.");
  const { root, cache } = housePaths();
  await mkdir(cache, { recursive: true });
  const key = locationKey(lat, lng);
  const index = indexPath(cache, key);
  try {
    const previous = await houseStatus(JSON.parse(await readFile(index, "utf8")).id);
    if (previous && previous.state !== "failed" && (previous.state !== "ready" || existsSync(housePaths(previous.id).glb))) return previous;
  } catch { /* no reusable import */ }
  const configured = process.env.REAL_HOUSE_EXPORTER;
  const exporter = [configured, path.join(cache, "exporter"), path.join(os.homedir(), ".codex", "real-house-exporter")] // ours: pinned .cache exporter beats the home-dir copy; env override stays first
    .find((p): p is string => !!p && existsSync(path.join(p, "google_map_export_bridge", "exporter", "earth-export.cjs")));
  if (!exporter) throw new Error("Install the exporter once: node apps/web/scripts/setup-real-house.mjs");
  const id = randomUUID(), { dir, status } = housePaths(id);
  await mkdir(dir, { recursive: true });
  const job: HouseJob = { id, locationKey: key, state: "running", stage: "Starting export", startedAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
  await writeFile(status, JSON.stringify(job));
  await writeFile(index, JSON.stringify({ id }));
  const child = spawn(process.execPath, [path.join(root, "scripts", "py.mjs"), path.join(root, "apps/web/scripts/export-house.py"), dir, exporter, String(lat), String(lng), process.execPath], {
    cwd: root, windowsHide: true, stdio: "ignore", env: process.env,
  });
  await new Promise<void>((resolve, reject) => { child.once("spawn", resolve); child.once("error", reject); }).catch(async e => {
    job.state = "failed"; job.error = "The export worker could not start."; await writeFile(status, JSON.stringify(job)); throw e;
  });
  if (child.pid) { // ours: lets houseStatus detect a dead worker; re-read so the worker's own progress is not clobbered
    try { const cur: HouseJob = JSON.parse(await readFile(status, "utf8")); if (!cur.pid) await writeFile(status, JSON.stringify({ ...cur, pid: child.pid })); } catch { /* worker owns the file */ }
  }
  child.unref();
  return job;
}

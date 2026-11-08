import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import path from "node:path";
import { repoRoot } from "./lab-server";
import { locationKey, type HouseJob } from "./real-house";

// LoD2 cadastre + Blender variant of real-house-jobs.ts: panels and devices are baked into the GLB by render/house_render.py.
export type Lod2Job = HouseJob & { panels?: number | null; source?: string };

export function lod2Paths(id?: string) {
  const root = repoRoot();
  if (!root) throw new Error("Repository root not found.");
  if (id !== undefined && !/^[0-9a-f-]{36}$/.test(id)) throw new Error("Invalid model id.");
  const cache = path.join(root, ".cache", "lod2-house");
  const dir = id ? path.join(cache, "jobs", id) : cache;
  return { root, cache, dir, status: path.join(dir, "job.json"), glb: path.join(dir, "house.glb") };
}

export async function lod2Status(id: string): Promise<Lod2Job | null> {
  let job: Lod2Job;
  try { job = JSON.parse(await readFile(lod2Paths(id).status, "utf8")); } catch { return null; }
  if (job.state === "running" && !job.pid && Date.now() - Date.parse(job.startedAt) > 30_000) return { ...job, state: "failed", error: "The render did not start" };
  if (job.state === "running" && job.pid) {
    try { process.kill(job.pid, 0); } catch { return { ...job, state: "failed", error: "The render worker stopped. Retry." }; }
  }
  return job.state === "ready" ? { ...job, modelUrl: `/api/lod2-house/${id}/model` } : job;
}

const indexPath = (cache: string, key: string) => path.join(cache, `index-${createHash("sha256").update(key).digest("hex").slice(0, 20)}.json`);

export async function startLod2(lat: number, lng: number): Promise<Lod2Job> {
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 85 || Math.abs(lng) > 180) throw new Error("Choose a valid map location.");
  const { root, cache } = lod2Paths();
  await mkdir(cache, { recursive: true });
  const key = locationKey(lat, lng), index = indexPath(cache, key);
  try {
    const previous = await lod2Status(JSON.parse(await readFile(index, "utf8")).id);
    if (previous && previous.state !== "failed" && (previous.state !== "ready" || existsSync(lod2Paths(previous.id).glb))) return previous;
  } catch { /* nothing to reuse */ }
  const id = randomUUID(), { dir, status } = lod2Paths(id);
  await mkdir(dir, { recursive: true });
  const now = new Date().toISOString();
  const job: Lod2Job = { id, locationKey: key, state: "running", stage: "Starting render", startedAt: now, updatedAt: now };
  await writeFile(status, JSON.stringify(job));
  await writeFile(index, JSON.stringify({ id }));
  const child = spawn(process.execPath, [path.join(root, "scripts", "py.mjs"), path.join(root, "apps/web/scripts/render-lod2-house.py"), dir, String(lat), String(lng)], {
    cwd: root, windowsHide: true, stdio: "ignore", env: process.env,
  });
  await new Promise<void>((resolve, reject) => { child.once("spawn", resolve); child.once("error", reject); }).catch(async e => {
    await writeFile(status, JSON.stringify({ ...job, state: "failed", error: "The render worker could not start." })); throw e;
  });
  child.unref();
  return job;
}

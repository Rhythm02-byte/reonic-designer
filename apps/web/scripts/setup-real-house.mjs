// Downloads the requested upstream dependency into ignored cache, never into the submission source.
import { spawnSync } from "node:child_process";
import { mkdirSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const target = path.join(root, ".cache/real-house/exporter");
const revision = "02c395f931c7a2d4b6fa9077c375eaa7d6d08382";
mkdirSync(path.dirname(target), { recursive: true });
function git(args) { const r = spawnSync("git", args, { stdio: "inherit", windowsHide: true }); if (r.status !== 0) process.exit(r.status ?? 1); }
if (!existsSync(path.join(target, ".git"))) git(["clone", "https://github.com/onlykshitij/Google-Earth-3D-to-Blender.git", target]);
git(["-C", target, "checkout", "--detach", revision]);
console.log(`Pinned real-house exporter ${revision}. Blender 4.2+ is required; set BLENDER_PATH if it is not detected.`);

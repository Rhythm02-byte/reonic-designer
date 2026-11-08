// `pnpm bootstrap`: everything a fresh clone needs, idempotent. Re-run after pulling engine or data changes.
// 1. Python venv + engine (editable)  2. web + contracts packages (pnpm)
// 3. With the private export in ./dataset: ETL -> data/processed, then train models/designer.joblib.
//    Without it the engine still runs, on labelled synthetic fallback data.
import { spawnSync } from "node:child_process";
import { existsSync, readdirSync } from "node:fs";
import path from "node:path";
import { root, venvPython } from "./py.mjs";

const run = (cmd, args, opts = {}) => {
  console.log(`\n> ${cmd} ${args.join(" ")}`);
  const r = spawnSync(cmd, args, { stdio: "inherit", cwd: root, shell: process.platform === "win32", ...opts });
  if (r.status !== 0) process.exit(r.status ?? 1);
};

if (!venvPython()) {
  const sys = process.platform === "win32" ? "python" : "python3";
  run(sys, ["-m", "venv", "services/engine/.venv"]);
}
const py = venvPython();
run(py, ["-m", "pip", "install", "-q", "-e", "services/engine[dev]"]);
run("pnpm", ["--dir", "apps/web", "install"]);
run("pnpm", ["--dir", "packages/contracts", "install"]);

const dataset = path.join(root, "dataset");
const hasData = existsSync(dataset) && readdirSync(dataset).some((d) => existsSync(path.join(dataset, d, "projects_status_quo.csv")));
if (hasData) {
  run(py, ["-m", "engine.etl.normalize", "--raw", "dataset", "--out", "data/processed"]);
  run(py, ["-m", "engine.policy.train"]);
  console.log("\nReady on the real data. Start with: pnpm dev");
} else {
  console.log("\nNo ./dataset/<installer>/projects_status_quo.csv found: the engine will run on synthetic fallback data.");
  console.log("Put the private Reonic export in ./dataset (never commit it), then run pnpm bootstrap again.");
}

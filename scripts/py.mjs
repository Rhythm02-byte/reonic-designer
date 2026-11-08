// Run the engine's Python (services/engine/.venv) on any OS: `node scripts/py.mjs <args>`.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

export const root = path.resolve(import.meta.dirname, "..");
export const venvPython = () =>
  ["Scripts/python.exe", "bin/python"].map((p) => path.join(root, "services/engine/.venv", p)).find(existsSync);

if (import.meta.main ?? process.argv[1] === import.meta.filename) {
  const py = venvPython();
  if (!py) {
    console.error("No services/engine/.venv yet. Run: pnpm bootstrap");
    process.exit(1);
  }
  const r = spawnSync(py, process.argv.slice(2), { stdio: "inherit", cwd: process.cwd(), env: process.env });
  process.exit(r.status ?? 1);
}

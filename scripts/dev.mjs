// `pnpm dev`: engine (FastAPI :8000) + web (Next :3000) in one terminal. Ctrl+C stops both.
import { spawn } from "node:child_process";
import { root, venvPython } from "./py.mjs";

const py = venvPython();
if (!py) {
  console.error("No services/engine/.venv yet. Run: pnpm bootstrap");
  process.exit(1);
}

const procs = [
  ["engine", py, ["-m", "uvicorn", "scripts.runtime_app:app", "--reload", "--port", "8000"], { cwd: root }],
  ["web", "pnpm", ["--dir", "apps/web", "dev"], { cwd: root, shell: true }],
].map(([name, cmd, args, opts]) => {
  const p = spawn(cmd, args, { ...opts, env: process.env });
  const tag = (d) => d.toString().split(/\r?\n/).filter(Boolean).forEach((l) => console.log(`[${name}] ${l}`));
  p.stdout.on("data", tag);
  p.stderr.on("data", tag);
  p.on("exit", (code) => console.log(`[${name}] exited (${code})`));
  return p;
});

console.log("Planner: http://localhost:3000   Test Lab: http://localhost:3000/lab   Engine: http://localhost:8000/docs");
const stop = () => { procs.forEach((p) => p.kill()); process.exit(0); };
process.on("SIGINT", stop);
process.on("SIGTERM", stop);

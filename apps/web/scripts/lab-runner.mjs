import { spawn } from "node:child_process";
import { readFile, writeFile, rename, unlink } from "node:fs/promises";
import path from "node:path";

const [root, id, mode, label] = process.argv.slice(2);
const dir = path.join(root, ".cache", "lab"), file = path.join(dir, "job.json");
const job = JSON.parse(await readFile(file, "utf8"));
if (job.id !== id) process.exit(1);
job.pid = process.pid;
const save = async () => {
  job.updatedAt = new Date().toISOString();
  await writeFile(`${file}.tmp`, JSON.stringify(job));
  await rename(`${file}.tmp`, file);
};
const py = path.join(root, "scripts", "py.mjs");
const commands = mode === "exam"
  ? [["2026 exam and offline evaluation", process.execPath, [py, "eval/run.py", "--data", "dataset", "--offline", ...(label ? ["--label", label] : [])], root]]
  : [
      ["Engine regression tests", process.execPath, [py, "-m", "pytest", "-q"], path.join(root, "services/engine")],
      ["Evaluation unit tests (no 2026 scoring)", process.execPath, [py, "-m", "pytest", "-q", "eval"], root],
      ["Web behavior tests", process.execPath, ["scripts/test-web.mjs"], path.join(root, "apps/web")],
      ["Web lint", process.execPath, ["node_modules/eslint/bin/eslint.js", "."], path.join(root, "apps/web")],
      ["Web type check", process.execPath, ["node_modules/typescript/bin/tsc", "--noEmit"], path.join(root, "apps/web")],
    ];
try {
  for (const [stage, command, args, cwd] of commands) {
    job.stage = stage; await save();
    let tail = "";
    const code = await new Promise((resolve, reject) => {
      const child = spawn(command, args, { cwd, windowsHide: true, env: { ...process.env, OFFLINE: "1" }, shell: false });
      child.stdout.on("data", d => { tail = (tail + d.toString()).slice(-2000); });
      child.stderr.on("data", d => { tail = (tail + d.toString()).slice(-2000); });
      child.once("error", reject); child.once("close", resolve);
    });
    if (code !== 0) throw new Error(`${stage} failed. ${tail}`);
    job.completed.push(stage); await save();
  }
  job.state = "passed"; job.stage = "Complete";
} catch (error) {
  job.state = "failed"; job.error = String(error.message ?? error).slice(-2000);
} finally {
  await save(); await unlink(path.join(dir, "run.lock")).catch(() => {});
}

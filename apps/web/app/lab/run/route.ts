import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { repoRoot } from "@/lib/lab-server";

// Local-only: runs all tests (`eval/run.py`, the same as `npm run eval`). The run records itself in eval/history.
let running = false;

export async function POST(req: Request) {
  if (process.env.NODE_ENV === "production") return Response.json({ error: "Runs start only on a local dev server." }, { status: 403 });
  if (running) return Response.json({ error: "A run is already in progress." }, { status: 409 });
  const root = repoRoot();
  const py = root && ["Scripts/python.exe", "bin/python"].map((p) => path.join(root, "services/engine/.venv", p)).find(existsSync);
  if (!root || !py) return Response.json({ error: "services/engine/.venv not found. Run npm run setup first." }, { status: 500 });

  const { label = "" } = (await req.json().catch(() => ({}))) as { label?: string };
  const args = ["eval/run.py", "--data", "dataset", "--offline", ...(label ? ["--label", label.slice(0, 80)] : [])];
  running = true;
  try {
    const { code, out } = await new Promise<{ code: number | null; out: string }>((resolve) => {
      let out = "";
      const p = spawn(py, args, { cwd: root, env: { ...process.env, OFFLINE: "1", PYTHONIOENCODING: "utf-8" } });
      p.stdout.on("data", (d) => (out += d));
      p.stderr.on("data", (d) => (out += d));
      p.on("close", (code) => resolve({ code, out }));
      p.on("error", (e) => resolve({ code: 1, out: String(e) }));
    });
    const tail = out.trim().split(/\r?\n/).slice(-12).join("\n");
    return code === 0 ? Response.json({ ok: true, tail }) : Response.json({ error: "The run failed.", tail }, { status: 500 });
  } finally {
    running = false;
  }
}

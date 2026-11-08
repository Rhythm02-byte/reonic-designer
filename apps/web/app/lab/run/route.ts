import { historyFile, isLocalMutation, isLocalRequest, repoRoot } from "@/lib/lab-server"; // ours: merged duplicate import
import { checkStatus, startChecks } from "@/lib/lab-jobs";
import { stat } from "node:fs/promises";

export async function GET(req: Request) {
  if (!isLocalRequest(req.headers)) return Response.json({ error: "Checks are local-only." }, { status: 403 });
  const root=repoRoot();
  const historyVersion=root?await stat(historyFile(root)).then(s=>s.mtimeMs).catch(()=>null):null;
  return Response.json({ job: await checkStatus(), historyVersion }, { headers: { "Cache-Control": "no-store" } });
}
export async function POST(req: Request) {
  if (!isLocalMutation(req)) return Response.json({ error: "Checks are local-only and must start from this app." }, { status: 403 });
  const body = await req.json().catch(() => null);
  if (!body || !["checks", "exam"].includes(body.mode)) return Response.json({ error: "Choose checks or exam." }, { status: 400 });
  if (body.mode === "exam" && body.confirmTestScoring !== true) return Response.json({ error: "Explicit confirmation is required to score 2026." }, { status: 400 });
  try {
    return Response.json({ job: await startChecks(body.mode, typeof body.label === "string" ? body.label : "") }, { status: 202 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not start checks.";
    return Response.json({ error: message }, { status: message.includes("already") ? 409 : 500 });
  }
}

import { isLocalMutation, isLocalRequest } from "@/lib/lab-server";
import { findHouse, startHouse } from "@/lib/real-house-jobs";
// ours: look up a ready import for a location; never starts an export
export async function GET(req: Request) {
  if (!isLocalRequest(req.headers)) return Response.json({ error: "House imports are local-only." }, { status: 403 });
  const q = new URL(req.url).searchParams, lat = Number(q.get("lat")), lng = Number(q.get("lng"));
  return Response.json({ job: await findHouse(lat, lng) }, { headers: { "Cache-Control": "no-store" } });
}
export async function POST(req: Request) {
  if (!isLocalMutation(req)) return Response.json({ error: "House imports must start from the local app." }, { status: 403 });
  const body = await req.json().catch(() => null);
  if (body?.confirmed !== true || typeof body?.lat !== "number" || typeof body?.lng !== "number" || !Number.isFinite(body.lat) || !Number.isFinite(body.lng) || Math.abs(body.lat) > 85 || Math.abs(body.lng) > 180) {
    return Response.json({ error: "Confirm the building and send valid coordinates." }, { status: 400 });
  }
  try { return Response.json({ job: await startHouse(body.lat, body.lng) }, { status: 202 }); }
  catch (e) { return Response.json({ error: e instanceof Error ? e.message : "Import could not start." }, { status: 503 }); }
}

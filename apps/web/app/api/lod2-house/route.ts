import { isHouseMutation } from "@/lib/lab-server";
import { startLod2 } from "@/lib/lod2-jobs";
export async function POST(req: Request) {
  if (!isHouseMutation(req)) return Response.json({ error: "House renders must start from the local app." }, { status: 403 });
  const body = await req.json().catch(() => null);
  if (typeof body?.lat !== "number" || typeof body?.lng !== "number" || !Number.isFinite(body.lat) || !Number.isFinite(body.lng) || Math.abs(body.lat) > 85 || Math.abs(body.lng) > 180) {
    return Response.json({ error: "Send valid coordinates." }, { status: 400 });
  }
  try { return Response.json({ job: await startLod2(body.lat, body.lng) }, { status: 202 }); }
  catch (e) { return Response.json({ error: e instanceof Error ? e.message : "Render could not start." }, { status: 503 }); }
}

import { isHouseRequest } from "@/lib/lab-server";
import { lod2Status } from "@/lib/lod2-jobs";
export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!isHouseRequest(req.headers)) return Response.json({ error: "House renders are local-only." }, { status: 403 });
  const { id } = await params;
  if (!/^[0-9a-f-]{36}$/.test(id)) return Response.json({ error: "Invalid model id." }, { status: 400 });
  const job = await lod2Status(id);
  return job ? Response.json({ job }, { headers: { "Cache-Control": "no-store" } }) : Response.json({ error: "Render not found." }, { status: 404 });
}

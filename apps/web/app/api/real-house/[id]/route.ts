import { isLocalRequest } from "@/lib/lab-server";
import { houseStatus } from "@/lib/real-house-jobs";
export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!isLocalRequest(req.headers)) return Response.json({ error: "House imports are local-only." }, { status: 403 });
  const { id } = await params;
  if (!/^[0-9a-f-]{36}$/.test(id)) return Response.json({ error: "Invalid model id." }, { status: 400 });
  const job = await houseStatus(id);
  return job ? Response.json({ job }, { headers: { "Cache-Control": "no-store" } }) : Response.json({ error: "Import not found." }, { status: 404 });
}

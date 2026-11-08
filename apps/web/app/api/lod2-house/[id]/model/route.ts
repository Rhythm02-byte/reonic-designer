import { readFile } from "node:fs/promises";
import { isHouseRequest } from "@/lib/lab-server";
import { lod2Paths, lod2Status } from "@/lib/lod2-jobs";
export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!isHouseRequest(req.headers)) return new Response("Local model only.", { status: 403 });
  const { id } = await params;
  if (!/^[0-9a-f-]{36}$/.test(id)) return new Response("Invalid model id.", { status: 400 });
  if ((await lod2Status(id))?.state !== "ready") return new Response("Model is not ready.", { status: 404 });
  try {
    const data = await readFile(lod2Paths(id).glb);
    return new Response(data, { headers: { "Content-Type": "model/gltf-binary", "Cache-Control": "private, max-age=86400", "X-Content-Type-Options": "nosniff" } });
  } catch { return new Response("Model unavailable. Retry the render.", { status: 404 }); }
}

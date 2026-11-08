// Address <-> coordinates, proxied so the server-only Google key never reaches the browser.
import { NextResponse } from "next/server";
import { isLocalMutation } from "@/lib/lab-server";

const KEY = process.env.GOOGLE_MAPS_API_KEY;

export async function POST(req: Request) {
  if (!isLocalMutation(req)) return NextResponse.json({ error: "Address lookup is local-only." }, { status: 403 });
  if (!KEY) return NextResponse.json({ error: "GOOGLE_MAPS_API_KEY is not set" }, { status: 500 });
  const body = await req.json().catch(() => null);
  const params = new URLSearchParams({ key: KEY });
  if (typeof body?.address === "string" && body.address.trim()) {
    params.set("address", body.address.trim());
  } else if (typeof body?.lat === "number" && typeof body?.lng === "number") {
    params.set("latlng", `${body.lat},${body.lng}`);
  } else {
    return NextResponse.json({ error: "Send either { address } or { lat, lng }" }, { status: 400 });
  }

  const res = await fetch(`https://maps.googleapis.com/maps/api/geocode/json?${params}`, { signal: AbortSignal.timeout(15_000) }).catch(() => null);
  if (!res) return NextResponse.json({ error: "Address lookup timed out. Please retry." }, { status: 504 });
  const data = await res.json();
  if (data.status !== "OK" || !data.results?.length) {
    return NextResponse.json({ error: data.error_message ?? `No match (${data.status})` }, { status: 404 });
  }
  const top = data.results[0];
  return NextResponse.json({
    lat: top.geometry.location.lat,
    lng: top.geometry.location.lng,
    formatted_address: top.formatted_address as string,
  });
}

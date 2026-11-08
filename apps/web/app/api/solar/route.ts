// Real roof/solar potential for a coordinate, via Google's Solar API. Proxied for the same
// reason as /api/geocode: the key stays server-side. Coverage is patchy outside the US, so a
// miss here is an expected, handled case, not an error to surface loudly.
import { NextResponse } from "next/server";
import { isHouseMutation } from "@/lib/lab-server";

const KEY = process.env.GOOGLE_MAPS_API_KEY;

export async function POST(req: Request) {
  if (!isHouseMutation(req)) return NextResponse.json({ error: "Roof lookup is local-only." }, { status: 403 });
  if (!KEY) return NextResponse.json({ error: "GOOGLE_MAPS_API_KEY is not set" }, { status: 500 });
  const { lat, lng } = await req.json().catch(() => ({}));
  if (typeof lat !== "number" || typeof lng !== "number" || !Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 85 || Math.abs(lng) > 180) {
    return NextResponse.json({ error: "Send { lat, lng }" }, { status: 400 });
  }

  const params = new URLSearchParams({
    "location.latitude": String(lat),
    "location.longitude": String(lng),
    requiredQuality: "LOW",
    key: KEY,
  });
  const res = await fetch(`https://solar.googleapis.com/v1/buildingInsights:findClosest?${params}`, { signal: AbortSignal.timeout(15_000) }).catch(() => null);
  if (!res) return NextResponse.json({ error: "Roof lookup timed out. Retry or enter roof capacity manually." }, { status: 504 });
  if (res.status === 404) {
    return NextResponse.json({ covered: false as const });
  }
  const data = await res.json();
  if (!res.ok) {
    return NextResponse.json({ error: data.error?.message ?? `Solar API error (${res.status})` }, { status: res.status });
  }

  const roof = data.solarPotential;
  return NextResponse.json({
    covered: true as const,
    maxArrayPanelsCount: roof?.maxArrayPanelsCount ?? null,
    maxArrayAreaMeters2: roof?.maxArrayAreaMeters2 ?? null,
    maxSunshineHoursPerYear: roof?.maxSunshineHoursPerYear ?? null,
    // Google's panel wattage assumption, used to turn a panel count into a kWp figure the rest of the app understands.
    panelCapacityWatts: roof?.panelCapacityWatts ?? null,
    panelWidthMeters: roof?.panelWidthMeters ?? null,
    panelHeightMeters: roof?.panelHeightMeters ?? null,
    roofSegmentStats: roof?.roofSegmentStats ?? [],
    solarPanels: roof?.solarPanels ?? [],
    center: data.center ?? null,
    boundingBox: data.boundingBox ?? null,
    imageryDate: data.imageryDate ?? null,
  });
}

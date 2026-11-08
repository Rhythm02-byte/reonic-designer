export type GeoPoint = { latitude: number; longitude: number };
export type RoofSegment = { pitchDegrees: number; azimuthDegrees: number; center?: GeoPoint; planeHeightAtCenterMeters?: number };
export type SolarPanel = { center: GeoPoint; orientation: "LANDSCAPE" | "PORTRAIT"; segmentIndex: number; yearlyEnergyDcKwh?: number };
export type RoofInfo = {
  covered: boolean; maxArrayPanelsCount?: number | null; maxArrayAreaMeters2?: number | null;
  maxSunshineHoursPerYear?: number | null; panelCapacityWatts?: number | null;
  panelWidthMeters?: number | null; panelHeightMeters?: number | null;
  roofSegmentStats?: RoofSegment[]; solarPanels?: SolarPanel[];
  center?: GeoPoint; boundingBox?: { sw: GeoPoint; ne: GeoPoint }; imageryDate?: { year?: number; month?: number; day?: number };
};
const cache = new Map<string, Promise<RoofInfo>>();
export function fetchRoof(lat: number, lng: number): Promise<RoofInfo> {
  const key = `${lat.toFixed(7)},${lng.toFixed(7)}`;
  let result = cache.get(key);
  if (!result) {
    result = fetch("/api/solar", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ lat, lng }), signal: AbortSignal.timeout(20_000) })
      .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.error ?? "Roof information unavailable."); return d as RoofInfo; })
      .catch(e => { cache.delete(key); throw e; });
    cache.set(key, result);
  }
  return result;
}

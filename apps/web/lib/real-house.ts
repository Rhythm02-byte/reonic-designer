export type Vec3 = [number, number, number];
export type RoofSurface = { outline: Vec3[]; exclusions: Vec3[][] };
export type HouseLayout = { surfaces: RoofSurface[]; width: number; height: number; gap: number; setback: number };
export type HouseAsset = { id: string; locationKey: string };
export type HouseJob = {
  id: string; locationKey: string; state: "running" | "ready" | "failed"; stage: string;
  startedAt: string; updatedAt: string; pid?: number; error?: string;
  origin?: { lat: number; lng: number }; modelUrl?: string; triangles?: number; exporterRevision?: string;
};
export const locationKey = (lat: number, lng: number) => `${lat.toFixed(7)},${lng.toFixed(7)}`;

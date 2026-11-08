// ours: fast downward "raycasts" on the imported Google mesh. A 100k-triangle GLB is too slow for
// thousands of three.js raycasts, so triangles near the house are binned once into an XZ grid and
// each query only tests the few triangles in its cell (no extra dependency, no BVH build).
import { Mesh, Vector3, type Object3D } from "three";
import type { Vec3 } from "./real-house";
import type { PanelPlacement } from "./roof-layout";
import type { RoofInfo } from "./roof";

export type Hit = { y: number; normal: Vector3 };
export type Heightfield = { sample: (x: number, z: number) => Hit | null };

export function buildHeightfield(root: Object3D, center: Vector3, radius = 45, cell = 0.75): Heightfield {
  const tris: number[] = []; // x0 y0 z0 x1 y1 z1 x2 y2 z2 per triangle, world space
  const bins = new Map<number, number[]>();
  const n = Math.ceil((2 * radius) / cell), x0 = center.x - radius, z0 = center.z - radius;
  const a = new Vector3(), b = new Vector3(), c = new Vector3();
  root.updateMatrixWorld(true);
  root.traverse((o) => {
    if (!(o instanceof Mesh)) return;
    const pos = o.geometry.getAttribute("position"), index = o.geometry.getIndex();
    if (!pos) return;
    const count = index ? index.count : pos.count;
    for (let i = 0; i + 2 < count; i += 3) {
      const ia = index ? index.getX(i) : i, ib = index ? index.getX(i + 1) : i + 1, ic = index ? index.getX(i + 2) : i + 2;
      a.fromBufferAttribute(pos, ia).applyMatrix4(o.matrixWorld);
      b.fromBufferAttribute(pos, ib).applyMatrix4(o.matrixWorld);
      c.fromBufferAttribute(pos, ic).applyMatrix4(o.matrixWorld);
      const minX = Math.min(a.x, b.x, c.x), maxX = Math.max(a.x, b.x, c.x), minZ = Math.min(a.z, b.z, c.z), maxZ = Math.max(a.z, b.z, c.z);
      if (maxX < x0 || maxZ < z0 || minX > x0 + 2 * radius || minZ > z0 + 2 * radius) continue;
      const t = tris.length / 9;
      tris.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z);
      const i0 = Math.max(0, Math.floor((minX - x0) / cell)), i1 = Math.min(n - 1, Math.floor((maxX - x0) / cell));
      const j0 = Math.max(0, Math.floor((minZ - z0) / cell)), j1 = Math.min(n - 1, Math.floor((maxZ - z0) / cell));
      if ((i1 - i0 + 1) * (j1 - j0 + 1) > 400) continue; // ground/terrain sheets: not roof
      for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
        const k = j * n + i, list = bins.get(k);
        if (list) list.push(t); else bins.set(k, [t]);
      }
    }
  });
  return {
    sample(x, z) {
      const i = Math.floor((x - x0) / cell), j = Math.floor((z - z0) / cell);
      if (i < 0 || j < 0 || i >= n || j >= n) return null;
      let best: Hit | null = null;
      for (const t of bins.get(j * n + i) ?? []) {
        const o = t * 9;
        const ax = tris[o], az = tris[o + 2], bx = tris[o + 3], bz = tris[o + 5], cx = tris[o + 6], cz = tris[o + 8];
        const d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz);
        if (Math.abs(d) < 1e-10) continue; // vertical wall triangle
        const l1 = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / d, l2 = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / d, l3 = 1 - l1 - l2;
        if (l1 < -1e-6 || l2 < -1e-6 || l3 < -1e-6) continue;
        const y = l1 * tris[o + 1] + l2 * tris[o + 4] + l3 * tris[o + 7];
        if (best && y <= best.y) continue;
        const e1 = new Vector3(bx - ax, tris[o + 4] - tris[o + 1], bz - az), e2 = new Vector3(cx - ax, tris[o + 7] - tris[o + 1], cz - az);
        const nn = e1.cross(e2).normalize();
        if (nn.y < 0) nn.negate();
        best = { y, normal: nn };
      }
      return best;
    },
  };
}

const tuple = (v: Vector3): Vec3 => [v.x, v.y, v.z];
export const MODULE = { width: 1.13, height: 1.72, gap: 0.02 }; // ours: typical 430 Wp module; planning assumption
const LIFT = 0.08; // above the fitted plane, so the noisy photogrammetry roof never pokes through

type Slot = { at: Vector3; corners: Vector3[] };
const quantile = (xs: number[], q: number) => { const s = [...xs].sort((a, b) => a - b); return s[Math.min(s.length - 1, Math.floor(q * s.length))]; };

/** Put all slots of one roof face on a single plane (shared normal, robust level), so rows stay straight. */
function onPlane(hf: Heightfield, slots: Slot[], u: Vector3, v: Vector3, normal: Vector3, tol: number): (PanelPlacement | null)[] {
  const level = (p: Vector3) => { const hit = hf.sample(p.x, p.z); return hit ? normal.x * p.x + normal.y * hit.y + normal.z * p.z : null; };
  const measured = slots.map((s) => {
    const ls = [s.at, ...s.corners].map(level);
    return ls.some((l) => l === null) ? null : (ls as number[]);
  });
  const all = measured.flatMap((m) => m ?? []);
  if (!all.length) return slots.map(() => null);
  const mid = quantile(all, 0.5);
  const keep = measured.map((m) => !!m && m.every((l) => Math.abs(l - mid) < tol));
  const kept = measured.filter((m, i) => keep[i]).flatMap((m) => m!);
  if (!kept.length) return slots.map(() => null);
  const d = quantile(kept, 0.9) + LIFT;
  return slots.map((s, i) => keep[i]
    ? { position: tuple(new Vector3(s.at.x, (d - normal.x * s.at.x - normal.z * s.at.z) / normal.y, s.at.z)), u: tuple(u), v: tuple(v), normal: tuple(normal) }
    : null);
}
const slot = (at: Vector3, u: Vector3, v: Vector3, w: number, h: number): Slot => ({
  at, corners: [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]].map(([a, b]) => at.clone().addScaledVector(u, a * w).addScaledVector(v, b * h)),
});

/** Google Solar panel centres (best-first) projected into the mesh frame (x east, z south); one plane per roof segment. */
export function placeFromSolar(hf: Heightfield, roof: RoofInfo, origin: { lat: number; lng: number }): { panels: PanelPlacement[]; width: number; height: number } {
  const w = roof.panelWidthMeters ?? 1.045, h = roof.panelHeightMeters ?? 1.879, R = 6371000, rad = Math.PI / 180;
  const list = (roof.solarPanels ?? []).slice(0, 400);
  const bySegment = new Map<number, { order: number; p: (typeof list)[number] }[]>();
  list.forEach((p, order) => { const g = bySegment.get(p.segmentIndex) ?? []; g.push({ order, p }); bySegment.set(p.segmentIndex, g); });
  const ranked: { order: number; placement: PanelPlacement }[] = [];
  for (const [index, group] of bySegment) {
    const seg = roof.roofSegmentStats?.[index];
    if (!seg) continue;
    const az = seg.azimuthDegrees * rad, pitch = seg.pitchDegrees * rad;
    const across = new Vector3(Math.cos(az), 0, Math.sin(az));
    const down = new Vector3(Math.sin(az) * Math.cos(pitch), -Math.sin(pitch), -Math.cos(az) * Math.cos(pitch));
    const normal = new Vector3().crossVectors(across, down).normalize();
    // one orientation per segment (the majority), so a face never mixes portrait and landscape
    const landscape = group.filter((g) => g.p.orientation === "LANDSCAPE").length * 2 > group.length;
    const u = landscape ? down : across, v = landscape ? across.clone().negate() : down;
    const slots = group.map((g) => slot(new Vector3((g.p.center.longitude - origin.lng) * rad * R * Math.cos(origin.lat * rad), 0, -(g.p.center.latitude - origin.lat) * rad * R), u, v, w, h));
    const placed = onPlane(hf, slots, u, v, normal, 0.6);
    placed.forEach((pl, i) => { if (pl) ranked.push({ order: group[i].order, placement: pl }); });
  }
  ranked.sort((a, b) => a.order - b.order);
  return { panels: ranked.map((r) => r.placement), width: w, height: h };
}

/** No Solar data: find south-ish roof faces (10–60° tilt) near the pin and lay straight rows on each face's plane, best face first. */
export function placeOnGrid(hf: Heightfield, center: Vector3, w = MODULE.width, h = MODULE.height, gap = MODULE.gap, radius = 14, limit = 200): PanelPlacement[] {
  type Pt = { x: number; z: number; y: number; n: Vector3 };
  const groups = new Map<string, Pt[]>();
  for (let x = -radius; x <= radius; x += 0.5) for (let z = -radius; z <= radius; z += 0.5) {
    const hit = hf.sample(center.x + x, center.z + z);
    if (!hit || hit.y < center.y - 4) continue; // ground, not roof
    const tilt = Math.acos(Math.min(1, hit.normal.y)) * 180 / Math.PI;
    if (tilt < 10 || tilt > 60) continue;
    const az = (Math.atan2(hit.normal.x, -hit.normal.z) * 180 / Math.PI + 360) % 360; // compass, 180 = south
    if (az < 90 || az > 270) continue;
    const key = `${Math.round(az / 20)}:${Math.round(tilt / 10)}`;
    const list = groups.get(key) ?? [];
    list.push({ x: center.x + x, z: center.z + z, y: hit.y, n: hit.normal });
    groups.set(key, list);
  }
  const faces = [...groups.values()].filter((g) => g.length >= 8).sort((a, b) => b.length - a.length);
  const out: PanelPlacement[] = [];
  const overlaps = (p: Vector3) => out.some((q) => Math.hypot(q.position[0] - p.x, q.position[2] - p.z) < Math.min(w, h) * 0.95);
  for (const face of faces) {
    const normal = face.reduce((s, p) => s.add(p.n), new Vector3()).normalize();
    const u = new Vector3(0, 1, 0).cross(normal).normalize(); // along the eaves
    const v = new Vector3().crossVectors(normal, u).normalize(); // downslope
    if (v.y > 0) v.negate();
    const hv = Math.hypot(v.x, v.z) || 1, vh = new Vector3(v.x / hv, 0, v.z / hv); // horizontal downslope direction
    const us = face.map((p) => p.x * u.x + p.z * u.z), vs = face.map((p) => p.x * vh.x + p.z * vh.z);
    const minU = Math.min(...us), maxU = Math.max(...us), minV = Math.min(...vs), maxV = Math.max(...vs);
    const dh = h * hv, step = (h + gap) * hv; // panel footprint along the downslope, in plan
    let best: PanelPlacement[] = [];
    for (const [ou, ov] of [[0, 0], [0.5, 0], [0, 0.5], [0.5, 0.5]]) {
      const slots: Slot[] = [];
      for (let a = minU + w / 2 + ou * (w + gap); a <= maxU - w / 2; a += w + gap)
        for (let b = minV + dh / 2 + ov * step; b <= maxV - dh / 2; b += step) {
          const at = new Vector3(u.x * a + vh.x * b, 0, u.z * a + vh.z * b);
          if (!overlaps(at)) slots.push(slot(at, u, v, w, h));
        }
      const trial = onPlane(hf, slots, u, v, normal, 0.25).filter((p): p is PanelPlacement => !!p);
      if (trial.length > best.length) best = trial;
    }
    out.push(...best);
    if (out.length >= limit) break;
  }
  return out.slice(0, limit);
}

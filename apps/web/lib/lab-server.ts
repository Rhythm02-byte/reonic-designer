import { existsSync } from "node:fs";
import path from "node:path";

/** The monorepo root: the first ancestor of the Next.js cwd that holds eval/run.py. */
export function repoRoot(): string | null {
  let dir = process.cwd();
  for (;;) {
    if (existsSync(path.join(dir, "eval", "run.py"))) return dir;
    const up = path.dirname(dir);
    if (up === dir) return null;
    dir = up;
  }
}

export const historyFile = (root: string) => path.join(root, "eval", "history", "runs.jsonl");

/** Runs start only on this machine's dev server: not in production, and not through a tunnel or proxy
 * (cloudflared adds cf-connecting-ip, and the Host is then the public name). Not x-forwarded-for: Next's own dev
 * server adds that to every request. */
export function isLocalRequest(h: Headers): boolean {
  if (process.env.NODE_ENV === "production") return false;
  if (h.get("cf-connecting-ip")) return false;
  const local = (v: string | null) => ["localhost", "127.0.0.1", "[::1]"].includes((v ?? "").replace(/:\d+$/, ""));
  return local(h.get("host")) && (!h.get("x-forwarded-host") || local(h.get("x-forwarded-host")));
}

/** A browser on another site must not be able to start local jobs or spend a map API key. */
export function isLocalMutation(req: Request): boolean {
  if (!isLocalRequest(req.headers)) return false;
  const origin = req.headers.get("origin");
  return origin === null || origin === new URL(req.url).origin;
}

// ours: NEXT_PUBLIC_TUNNEL_3D=1 opens the map and the house imports/renders (not project data or the lab) to a tunnel
// in dev. Anyone with the link can then spend the Google key and start Blender jobs on this machine.
export const tunnelHouse = process.env.NEXT_PUBLIC_TUNNEL_3D === "1" && process.env.NODE_ENV !== "production";
export const isHouseRequest = (h: Headers) => tunnelHouse || isLocalRequest(h);
/** Same-origin check by Host: behind cloudflared the request URL is the local origin, the Origin header the public one. */
export function isHouseMutation(req: Request): boolean {
  if (!tunnelHouse) return isLocalMutation(req);
  const origin = req.headers.get("origin");
  return origin === null || new URL(origin).host === req.headers.get("host");
}

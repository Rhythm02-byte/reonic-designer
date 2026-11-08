// ours: data guard for a public tunnel (cloudflared → `pnpm dev`). Real held-out projects (/engine/holdout) and the
// test runner (/lab/run) answer only on this machine; through the tunnel (cf-connecting-ip, or a non-local Host) they
// are refused, so a shared demo URL never serves Reonic project rows. The laptop running the pitch is unaffected.
import { NextResponse, type NextRequest } from "next/server";

const LOCAL = ["localhost", "127.0.0.1", "[::1]"];
const isLocal = (v: string | null) => LOCAL.includes((v ?? "").replace(/:\d+$/, ""));

export function proxy(req: NextRequest) {
  const h = req.headers;
  const local = !h.get("cf-connecting-ip") && isLocal(h.get("host")) && (!h.get("x-forwarded-host") || isLocal(h.get("x-forwarded-host")));
  if (!local) return NextResponse.json({ detail: "Real projects are shown only on the presenter's machine." }, { status: 403 });
  return NextResponse.next();
}

// /api/geocode and /api/solar spend the team's paid Google key: local only too, so a public link can't burn it.
export const config = { matcher: ["/engine/holdout/:path*", "/engine/holdout", "/lab/run", "/api/geocode", "/api/solar"] };

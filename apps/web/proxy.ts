// ours: data guard for a public tunnel (cloudflared → `pnpm dev`). Real held-out projects (/engine/holdout) and the
// test runner (/lab/run) answer only on this machine; through the tunnel (cf-connecting-ip, or a non-local Host) they
// are refused, so a shared demo URL never serves Reonic project rows. The laptop running the pitch is unaffected.
import { NextResponse, type NextRequest } from "next/server";

const LOCAL = ["localhost", "127.0.0.1", "[::1]"];
const isLocal = (v: string | null) => LOCAL.includes((v ?? "").replace(/:\d+$/, ""));

// ours: matched in code, case-insensitively. Next's rewrite /engine/:path* ignores case, so /ENGINE/holdout reached the
// engine through the tunnel (HTTP 200, real rows) while the case-sensitive matcher below skipped it.
const GUARDED = /^\/(engine\/holdout|lab\/run|api\/geocode|api\/solar)(\/|$)/i;

// ours: the rewrite decodes percent-escapes (even doubly encoded ones) before the engine sees the path, so decode here too.
function decoded(pathname: string): string {
  let p = pathname;
  for (let i = 0; i < 4; i++) {
    try {
      const d = decodeURIComponent(p);
      if (d === p) break;
      p = d;
    } catch {
      break;
    }
  }
  return p;
}

export function proxy(req: NextRequest) {
  if (!GUARDED.test(decoded(req.nextUrl.pathname))) return NextResponse.next();
  const h = req.headers;
  const local = !h.get("cf-connecting-ip") && isLocal(h.get("host")) && (!h.get("x-forwarded-host") || isLocal(h.get("x-forwarded-host")));
  if (!local) return NextResponse.json({ detail: "Real projects are shown only on the presenter's machine." }, { status: 403 });
  return NextResponse.next();
}

// /api/geocode and /api/solar spend the team's paid Google key: local only too, so a public link can't burn it.
// ours: every page and route passes through proxy(); only the guarded paths above are checked (assets are skipped).
export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };

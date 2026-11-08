#!/bin/sh
# Reproducible check for the data guard (apps/web/proxy.ts): with the dev servers running (pnpm dev), every spelling of the
# real-project routes must be refused when the request looks like it came through the tunnel. Exit 1 on any leak.
# Never calls /lab/run with a local request: that would start a run that scores the 2026 test.
BASE="${1:-http://localhost:3000}"; H='cf-connecting-ip: 1.2.3.4'; bad=0
for p in /engine/holdout /ENGINE/holdout /Engine/holdout /engine/%68oldout /ENGINE/%48oldout /engine/%2568oldout /engine/./holdout /engine/x/../holdout "/engine/holdout?x=1"; do
  code=$(curl -sL -m 30 -o /dev/null -w '%{http_code}' --path-as-is -H "$H" "$BASE$p")
  case "$code" in 403|404) echo "ok    $code $p" ;; *) echo "LEAK  $code $p"; bad=1 ;; esac
done
for p in /lab/run /api/geocode /api/solar; do
  code=$(curl -s -m 30 -o /dev/null -w '%{http_code}' -X POST -H "$H" -H 'content-type: application/json' -d '{}' "$BASE$p")
  [ "$code" = 403 ] && echo "ok    $code POST $p" || { echo "LEAK  $code POST $p"; bad=1; }
done
exit $bad

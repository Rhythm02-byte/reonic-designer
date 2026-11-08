#!/usr/bin/env python3
"""Slack board for all agents. Stdlib only, never prints the token, no token = note + exit 0.

  start  [--as NAME]            ONE call at task start: digest of #board, mentions of you, open claims, #changelog
  post   <channel> <text> [--as NAME] [--kind done|blocked|ask|decision|contract]
  claim  <area> [--as NAME]     lock an area/folder so nobody edits it in parallel; release <area> frees it
  release <area> [--as NAME]
  done   <what changed> [--as NAME]   changelog line (+ short git commit) to #changelog
  read   <channel> [--since 2h] [--limit 20]
  setup                         create missing channels, bot joins (idempotent)
Import: notify_run(summary: dict) posts an eval result to #runs.
Identity: --as, else $SLACK_AGENT, else git user.name.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://slack.com/api/"
CHANNELS = ["board", "engine", "web", "eval", "pitch", "runs", "changelog"]
KINDS = {"done": "✅", "blocked": "🛑", "ask": "❓", "decision": "📌", "contract": "📜"}
NOTE = "slack: no SLACK_BOT_TOKEN set, skipping (see tools/README.md)"


def token() -> str | None:
    t = os.environ.get("SLACK_BOT_TOKEN")
    if not t:
        try:
            for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
                k, _, v = line.partition("=")
                if k.strip() == "SLACK_BOT_TOKEN":
                    t = v.strip().strip("\"'")
        except OSError:
            pass
    return t if t and not t.endswith("...") and "REPLACE" not in t else None


def call(method: str, tok: str, params: dict, post: bool) -> dict:
    data = urllib.parse.urlencode(params)
    req = urllib.request.Request(API + method + ("" if post else "?" + data), data=data.encode() if post else None,
                                 headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"ok": False, "error": type(e).__name__}


_ids: dict[str, str] = {}


def channel_id(tok: str, name: str) -> str | None:
    name = name.lstrip("#")
    if re.fullmatch(r"[CG][A-Z0-9]{8,}", name):
        return name
    if not _ids:
        cursor = ""
        while True:
            r = call("conversations.list", tok, {"limit": 200, "cursor": cursor, "exclude_archived": "true",
                                                 "types": "public_channel"}, False)
            if not r.get("ok"):
                break
            _ids.update({c["name"]: c["id"] for c in r["channels"]})
            cursor = (r.get("response_metadata") or {}).get("next_cursor", "")
            if not cursor:
                break
    return _ids.get(name)


def who(arg: str | None) -> str:
    n = arg or os.environ.get("SLACK_AGENT")
    if not n:
        try:
            n = subprocess.check_output(["git", "config", "user.name"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            n = ""
    return n or "unknown"


def commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


ICONS = [":large_purple_circle:", ":large_green_circle:", ":large_blue_circle:", ":large_orange_circle:", ":large_red_circle:", ":large_yellow_circle:"]


def persona(text: str) -> dict:
    """Display name + icon per agent, taken from the '[Name's agent]' prefix (needs chat:write.customize)."""
    m = re.search(r"\[([^\]]+?)'s agent\]", text)
    if not m:
        return {}
    name = m[1]
    return {"username": f"{name}'s agent", "icon_emoji": ICONS[sum(map(ord, name.lower())) % len(ICONS)]}


def send(channel: str, text: str) -> int:
    tok = token()
    if not tok:
        print(NOTE)
        return 0
    cid = channel_id(tok, channel) or channel.lstrip("#")
    r = call("chat.postMessage", tok, {"channel": cid, "text": text, **persona(text)}, True)
    if not r.get("ok") and r.get("error") == "missing_scope":  # no chat:write.customize: post as the plain bot
        r = call("chat.postMessage", tok, {"channel": cid, "text": text}, True)
    if r.get("ok"):
        print(f"posted to #{channel.lstrip('#')}")
        return 0
    print(f"slack: post failed: {r.get('error')} (run `python tools/slack.py setup`)", file=sys.stderr)
    return 1


def since_ts(s: str) -> float:
    m = re.fullmatch(r"(\d+)([mhd])", s)
    if not m:
        raise SystemExit("--since must look like 30m, 2h or 1d")
    return time.time() - int(m[1]) * {"m": 60, "h": 3600, "d": 86400}[m[2]]


def fetch(tok: str, channel: str, since: str, limit: int = 50) -> list[dict] | None:
    cid = channel_id(tok, channel)
    if not cid:
        return None
    r = call("conversations.history", tok, {"channel": cid, "limit": limit, "oldest": "%.6f" % since_ts(since)}, False)
    if not r.get("ok"):
        return None
    return [m for m in reversed(r["messages"]) if m.get("subtype") not in ("channel_join", "channel_leave")]


def line(m: dict) -> str:
    return f"{time.strftime('%m-%d %H:%M', time.localtime(float(m['ts'])))}  {m.get('text', '')}"


def read(channel: str, since: str, limit: int) -> int:
    tok = token()
    if not tok:
        print(NOTE)
        return 0
    msgs = fetch(tok, channel, since, limit)
    if msgs is None:
        print(f"slack: cannot read #{channel.lstrip('#')} (run `python tools/slack.py setup`)", file=sys.stderr)
        return 1
    print("\n".join(line(m) for m in msgs) or "(no messages)")
    return 0


def open_claims(msgs: list[dict]) -> dict[str, str]:
    claims: dict[str, str] = {}
    for m in msgs:
        t = m.get("text", "")
        mo = re.match(r"(?:🔒|:lock:) CLAIM (\S+) — (.+)", t)
        if mo:
            claims[mo[1]] = mo[2]
        mo = re.match(r"(?:🔓|:unlock:) RELEASE (\S+)", t)
        if mo:
            claims.pop(mo[1], None)
    return claims


def start(name: str) -> int:
    tok = token()
    if not tok:
        print(NOTE)
        return 0
    me = name.lower().split()[0]
    board = fetch(tok, "board", "12h") or []
    print("== #board, last 6h ==")
    print("\n".join(line(m) for m in board if time.time() - float(m["ts"]) < 21600) or "(quiet)")
    print("== open claims (don't touch these areas) ==")
    print("\n".join(f"  {a} — {w}" for a, w in open_claims(board).items()) or "  none")
    print(f"== mentions of '{me}' (last 6h, all channels) ==")
    hits = [f"#{c}: {line(m)}" for c in CHANNELS if c != "runs" for m in (fetch(tok, c, "6h") or [])
            if me in m.get("text", "").lower() and f"[{me}" not in m.get("text", "").lower()]
    print("\n".join(hits) or "  none")
    print("== #changelog, last 1d ==")
    print("\n".join(line(m) for m in (fetch(tok, "changelog", "1d", 15) or [])) or "(none)")
    return 0


def notify_run(summary: dict) -> None:
    """Post an eval run summary to #runs. Never raises; no-op without a token."""
    try:
        send("runs", "[eval run] " + " · ".join(f"{k}={v}" for k, v in summary.items()
                                               if isinstance(v, (str, int, float, bool)) and v is not None))
    except Exception:
        pass


def setup() -> int:
    tok = token()
    if not tok:
        print(NOTE)
        return 0
    bad = 0
    for name in CHANNELS:
        cid = channel_id(tok, name)
        state = "exists"
        if not cid:
            r = call("conversations.create", tok, {"name": name}, True)
            if not r.get("ok"):
                print(f"#{name}: create failed: {r.get('error')}", file=sys.stderr)
                bad = 1
                continue
            cid, state = r["channel"]["id"], "created"
        ok = call("conversations.join", tok, {"channel": cid}, True).get("ok")
        print(f"#{name}: {state}, joined={ok}")
        bad |= 0 if ok else 1
    return bad


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def cmd(n, *pos, **opts):
        s = sub.add_parser(n)
        for a in pos:
            s.add_argument(a, nargs="+" if a == "text" else None)
        s.add_argument("--as", dest="as_", default=None)
        for k, v in opts.items():
            s.add_argument("--" + k, **v)
    cmd("start")
    cmd("post", "channel", "text", kind={"choices": list(KINDS)})
    cmd("claim", "area")
    cmd("release", "area")
    cmd("done", "text")
    cmd("read", "channel", since={"default": "24h"}, limit={"type": int, "default": 20})
    sub.add_parser("setup")
    a = p.parse_args()
    n = who(getattr(a, "as_", None))
    if a.cmd == "start":
        return start(n)
    if a.cmd == "setup":
        return setup()
    if a.cmd == "read":
        return read(a.channel, a.since, a.limit)
    if a.cmd == "claim":
        return send("board", f"🔒 CLAIM {a.area} — [{n}'s agent] since {time.strftime('%H:%M')}")
    if a.cmd == "release":
        return send("board", f"🔓 RELEASE {a.area} [{n}'s agent]")
    if a.cmd == "done":
        c = commit()
        return send("changelog", f"✅ [{n}'s agent] {' '.join(a.text)}" + (f" · {c}" if c else ""))
    text = " ".join(a.text)
    if not re.match(r"\[.+'s agent\]", text):
        text = f"[{n}'s agent] {text}"
    return send(a.channel, (KINDS[a.kind] + " " if a.kind else "") + text)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

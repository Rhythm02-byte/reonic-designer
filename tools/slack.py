#!/usr/bin/env python3
"""Slack board for all agents. Stdlib only.

  python tools/slack.py post <channel> <text>
  python tools/slack.py setup   (create #board #engine #web #eval #pitch #runs, bot joins)
  python tools/slack.py read <channel> [--since 2h] [--limit 20]

Token: SLACK_BOT_TOKEN from the environment or the repo-root .env. Never printed.
No token -> short note, exit 0 (clean no-op).
Import helper: notify_run(summary: dict) posts a one-line eval result to #runs.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://slack.com/api/"


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
    url = API + method + ("" if post else "?" + data)
    req = urllib.request.Request(url, data=data.encode() if post else None,
                                 headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"ok": False, "error": type(e).__name__}


def channel_id(tok: str, name: str) -> str | None:
    name = name.lstrip("#")
    if re.fullmatch(r"[CG][A-Z0-9]{8,}", name):
        return name
    cursor = ""
    while True:
        r = call("conversations.list", tok, {"limit": 200, "cursor": cursor, "exclude_archived": "true",
                                             "types": "public_channel"}, False)
        if not r.get("ok"):
            return None
        for c in r["channels"]:
            if c["name"] == name:
                return c["id"]
        cursor = (r.get("response_metadata") or {}).get("next_cursor", "")
        if not cursor:
            return None


def post(channel: str, text: str) -> int:
    tok = token()
    if not tok:
        print("slack: no SLACK_BOT_TOKEN set, skipping (see tools/README.md)")
        return 0
    r = call("chat.postMessage", tok, {"channel": channel.lstrip("#"), "text": text}, True)
    if r.get("ok"):
        print(f"posted to #{channel.lstrip('#')}")
        return 0
    print(f"slack: post failed: {r.get('error')} (is the bot invited to #{channel.lstrip('#')}?)", file=sys.stderr)
    return 1


def parse_since(s: str) -> float:
    m = re.fullmatch(r"(\d+)([mhd])", s)
    if not m:
        raise SystemExit("--since must look like 30m, 2h or 1d")
    return time.time() - int(m[1]) * {"m": 60, "h": 3600, "d": 86400}[m[2]]


def read(channel: str, since: str, limit: int) -> int:
    tok = token()
    if not tok:
        print("slack: no SLACK_BOT_TOKEN set, skipping (see tools/README.md)")
        return 0
    cid = channel_id(tok, channel)
    if not cid:
        print(f"slack: channel #{channel.lstrip('#')} not found or bot lacks channels:read", file=sys.stderr)
        return 1
    r = call("conversations.history", tok, {"channel": cid, "limit": limit, "oldest": parse_since(since)}, False)
    if not r.get("ok"):
        print(f"slack: read failed: {r.get('error')} (invite the bot to the channel)", file=sys.stderr)
        return 1
    for m in reversed(r["messages"]):
        ts = time.strftime("%m-%d %H:%M", time.localtime(float(m["ts"])))
        print(f"{ts}  {m.get('text', '')}")
    if not r["messages"]:
        print("(no messages)")
    return 0


CHANNELS = ["board", "engine", "web", "eval", "pitch", "runs"]


def setup() -> int:
    """Create the standard channels (if missing) and make the bot join them."""
    tok = token()
    if not tok:
        print("slack: no SLACK_BOT_TOKEN set, skipping (see tools/README.md)")
        return 0
    bad = 0
    for name in CHANNELS:
        cid = channel_id(tok, name)
        if not cid:
            r = call("conversations.create", tok, {"name": name}, True)
            if not r.get("ok"):
                print(f"#{name}: create failed: {r.get('error')}", file=sys.stderr)
                bad = 1
                continue
            cid, state = r["channel"]["id"], "created"
        else:
            state = "exists"
        j = call("conversations.join", tok, {"channel": cid}, True)
        print(f"#{name}: {state}, joined={j.get('ok')}")
        bad |= 0 if j.get("ok") else 1
    return bad


def notify_run(summary: dict) -> None:
    """Post an eval run summary to #runs. Never raises; no-op without a token."""
    try:
        parts = [f"{k}={v}" for k, v in summary.items() if isinstance(v, (str, int, float, bool)) and v is not None]
        post("runs", "[eval run] " + " · ".join(parts))
    except Exception:
        pass


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("post")
    a.add_argument("channel")
    a.add_argument("text", nargs="+")
    sub.add_parser("setup")
    b = sub.add_parser("read")
    b.add_argument("channel")
    b.add_argument("--since", default="24h")
    b.add_argument("--limit", type=int, default=20)
    args = p.parse_args()
    if args.cmd == "setup":
        return setup()
    if args.cmd == "post":
        return post(args.channel, " ".join(args.text))
    return read(args.channel, args.since, args.limit)


if __name__ == "__main__":
    sys.exit(main())

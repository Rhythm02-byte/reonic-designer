#!/usr/bin/env python3
"""Slack board for all agents. Stdlib only, never prints the token, no token = note + exit 0.

  start  [--as NAME] [--full]   compact task-start digest; --full shows all fetched activity
  post   <channel> <text> [--as NAME] [--kind done|blocked|ask|decision|contract]
  claim  <area> [area ...] [--as NAME]    update your single status in #claims (advisory)
  release <area> [area ...] [--as NAME]  remove your claims without new messages
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
CHANNELS = ["board", "engine", "web", "eval", "pitch", "runs", "changelog", "claims"]
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
    data = urllib.parse.urlencode({k: json.dumps(v) if isinstance(v, (dict, list, bool)) else v for k, v in params.items()})
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
    from slack_bridge.mentions import resolve_mentions
    text = resolve_mentions(text)
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


def fetch(tok: str, channel: str, since: str | None, limit: int = 50, paginate: bool = False) -> list[dict] | None:
    cid = channel_id(tok, channel)
    if not cid:
        return None
    params = {"channel": cid, "limit": limit}
    if since is not None:
        params["oldest"] = "%.6f" % since_ts(since)
    messages = []
    while True:
        r = call("conversations.history", tok, params, False)
        if not r.get("ok"):
            return None
        messages.extend(r["messages"])
        cursor = (r.get("response_metadata") or {}).get("next_cursor", "")
        if not paginate or not cursor:
            break
        params["cursor"] = cursor
    return [m for m in reversed(messages) if m.get("subtype") not in ("channel_join", "channel_leave")]


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


def registry_row(m: dict) -> tuple[str, list[str]] | None:
    lines = m.get("text", "").splitlines()
    match = re.fullmatch(r"CLAIMS \[([^\]]+)'s agent\]", lines[0]) if lines else None
    if match:
        return match[1], [line[2:] for line in lines[1:] if line.startswith("- ")]
    return None


def owner(label: str) -> str:
    match = re.match(r"\[([^\]]+)'s agent\]", label)
    return match[1].casefold() if match else label.casefold()


def open_claims(msgs: list[dict]) -> dict[str, str]:
    claims: dict[str, str] = {}
    for m in sorted(msgs, key=lambda m: float((m.get("edited") or {}).get("ts", m["ts"]))):
        row = registry_row(m)
        if row:
            name, areas = row
            claims = {a: w for a, w in claims.items() if owner(w) != name.casefold()}
            claims.update({a: f"[{name}'s agent]" for a in areas})
            continue
        t = m.get("text", "")
        mo = re.match(r"(?:🔒|:lock:) CLAIM (\S+) — (.+)", t)
        if mo:
            claims[mo[1]] = mo[2]
        mo = re.match(r"(?:🔓|:unlock:) RELEASE (\S+)", t)
        if mo:
            claims.pop(mo[1], None)
    return claims


def normalize_area(area: str) -> str:
    area = area.replace("\\", "/")
    if area.startswith("/") or ":" in area or any(c.isspace() for c in area) or ".." in area.split("/"):
        raise ValueError("use repository-relative paths without whitespace or '..'")
    return "/".join(p for p in area.split("/") if p and p != ".") or "."


def overlaps(a: str, b: str) -> bool:
    a, b = normalize_area(a).casefold(), normalize_area(b).casefold()
    return a == "." or b == "." or a == b or a.startswith(b + "/") or b.startswith(a + "/")


def change_claims(name: str, areas: list[str], release: bool = False) -> int:
    from slack_bridge.common import read_config, request
    config = read_config()
    if config:
        try:
            request(config, '/claims', {'paths': areas, 'release': release})
            print('claims updated via bridge')
            return 0
        except Exception as error:
            print('slack: bridge claim failed; no unsafe fallback (' + type(error).__name__ + ')', file=sys.stderr)
            return 1
    tok = token()
    if not tok:
        print(NOTE)
        return 0
    try:
        areas = sorted({normalize_area(a) for a in areas})
    except ValueError as e:
        print(f"slack: {e}", file=sys.stderr)
        return 1
    board = fetch(tok, "board", "12h", 100, paginate=True)
    registry = fetch(tok, "claims", None, 100, paginate=True)
    if board is None or registry is None:
        print("slack: cannot check claims; run setup if #claims is missing", file=sys.stderr)
        return 1
    active = open_claims(board + registry)
    mine = {normalize_area(a) for a, w in active.items() if owner(w) == name.casefold()}
    for area in areas:
        for held, by in active.items():
            if owner(by) != name.casefold() and (overlaps(area, held) if not release else
                                                normalize_area(area).casefold() == normalize_area(held).casefold()):
                print(f"slack: {area} conflicts with {held} — {by}", file=sys.stderr)
                return 1
    previous = set(mine)
    if release:
        mine = {a for a in mine if a.casefold() not in {p.casefold() for p in areas}}
    else:
        # One parent claim is enough; collapse redundant child scopes in a batch.
        combined = {a.casefold(): a for a in sorted(mine | set(areas))}
        mine = {a for key, a in combined.items() if not any(
            parent != key and (parent == "." or key.startswith(parent + "/")) for parent in combined)}
    rows = [m for m in registry if registry_row(m) and registry_row(m)[0].casefold() == name.casefold()]
    row = rows[-1] if rows else None
    stored = {normalize_area(a) for a in registry_row(row)[1]} if row else set()
    if previous == mine and stored == mine:
        print("claims unchanged")
        return 0
    text = f"CLAIMS [{name}'s agent]" + "".join(f"\n- {a}" for a in sorted(mine))
    params = {"channel": channel_id(tok, "claims"), "text": text}
    if row:
        params["ts"] = row["ts"]
    result = call("chat.update" if row else "chat.postMessage", tok, params, True)
    if not result.get("ok"):
        print(f"slack: claim update failed: {result.get('error')}", file=sys.stderr)
        return 1
    print("claims updated in #claims")
    return 0


def is_claim(m: dict) -> bool:
    return bool(re.match(r"(?:🔒|:lock:) CLAIM |(?:🔓|:unlock:) RELEASE ", m.get("text", "")))


def start(name: str, full: bool = False) -> int:
    tok = token()
    if not tok:
        print(NOTE)
        return 0
    me = name.lower().split()[0]
    from slack_bridge.mentions import resolve_mentions
    from slack_bridge.common import read_config, request
    mention = resolve_mentions('@' + me)
    board = fetch(tok, "board", "12h", 100, paginate=True)
    registry = fetch(tok, "claims", None, 100, paginate=True)
    if board is None or registry is None:
        print("slack: cannot read #board/#claims; claims could not be checked (run setup)", file=sys.stderr)
        return 1
    seen = set()

    def section(channel: str, messages: list[dict], limit: int, prefix: str = "") -> None:
        fresh = [m for m in messages if (channel, m["ts"]) not in seen]
        # Keep decisions, contracts, blockers and requests even when older than the compact tail.
        important = r"^(?:📌|📜|🛑|❓|:pushpin:|:scroll:|:octagonal_sign:|:question:)"
        tail = {m["ts"] for m in fresh[-limit:]}
        shown = [m for m in fresh if full or m["ts"] in tail
                 or (channel == "board" and re.match(important, m.get("text", "")))]
        for m in shown:
            print(prefix + line(m))
            seen.add((channel, m["ts"]))
        if not shown:
            print("  none")
        if len(fresh) > len(shown):
            print(f"  ({len(fresh) - len(shown)} older messages omitted; start --full or read {channel})")

    print("== #board, last 6h ==")
    recent = [m for m in board if time.time() - float(m["ts"]) < 21600]
    section("board", [m for m in recent if full or not is_claim(m)], 8)
    print("== open claims (#claims + legacy board 12h; don't touch these areas) ==")
    config = read_config()
    if config:
        try:
            active = {c['area']: c['agent'] for c in request(config, '/claims')}
        except Exception:
            print('slack: authoritative bridge claims unavailable', file=sys.stderr)
            return 1
    else:
        active = open_claims(board + registry)
    print("\n".join(f"  {a} — {w}" for a, w in active.items()) or "  none")
    changelog = fetch(tok, "changelog", "1d", 100, paginate=True)
    print("== #changelog, last 1d ==")
    section("changelog", changelog or [], 5)
    print(f"== additional mentions of '{me}' (last 6h) ==")
    failed = ["changelog"] if changelog is None else []
    for c in CHANNELS:
        if c in ("runs", "claims"):
            continue
        msgs = recent if c == "board" else changelog if c == "changelog" else fetch(tok, c, "6h", 100, paginate=True)
        if msgs is None:
            if c not in failed:
                failed.append(c)
            continue
        hits = [m for m in msgs if time.time() - float(m["ts"]) < 21600
                and (re.search(r"(?<!\w)" + re.escape(me) + r"(?!\w)", m.get("text", ""), re.I)
                     or (mention != '@' + me and mention in m.get('text', '')))
                and f"[{me}" not in m.get("text", "").lower() and not is_claim(m)
                and (c, m["ts"]) not in seen]
        if hits:
            section(c, hits, 8, f"#{c}: ")
    if failed:
        print("slack: incomplete digest; cannot read " + ", ".join("#" + c for c in failed), file=sys.stderr)
    return 1 if failed else 0


def notify_run(summary: dict) -> None:
    """Post an eval run summary to #runs. Never raises; no-op without a token."""
    try:
        tok = token()
        if not tok:
            return
        from slack_bridge.runs import publish
        result = publish(summary, lambda method, params: call(method, tok, params, True), channel_id(tok, 'runs'))
        if result.get('status') not in ('published', 'pending'):
            print('slack: run card ' + str(result.get('status', result.get('error', 'failed'))), file=sys.stderr)
    except Exception as error:
        print('slack: run notification failed (' + type(error).__name__ + ')', file=sys.stderr)


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
    from slack_bridge.cli import COMMANDS, main as bridge_main
    if len(sys.argv) > 1 and sys.argv[1] in COMMANDS:
        return bridge_main(sys.argv[1:])
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def cmd(n, *pos, **opts):
        s = sub.add_parser(n)
        for a in pos:
            s.add_argument(a, nargs="+" if a in ("text", "area") else None)
        s.add_argument("--as", dest="as_", default=None)
        for k, v in opts.items():
            s.add_argument("--" + k, **v)
    cmd("start", full={"action": "store_true"})
    cmd("post", "channel", "text", kind={"choices": list(KINDS)},
        to={"action": "append", "default": []}, path={"action": "append", "default": []},
        priority={"choices": ['normal', 'critical'], "default": 'normal'}, wake={"action": 'store_true'}, thread={})
    cmd("claim", "area")
    cmd("release", "area")
    cmd("done", "text")
    cmd("read", "channel", since={"default": "24h"}, limit={"type": int, "default": 20})
    sub.add_parser("setup")
    a = p.parse_args()
    n = who(getattr(a, "as_", None))
    if a.cmd == "start":
        return start(n, a.full)
    if a.cmd == "setup":
        return setup()
    if a.cmd == "read":
        return read(a.channel, a.since, a.limit)
    if a.cmd == "claim":
        return change_claims(n, a.area)
    if a.cmd == "release":
        return change_claims(n, a.area, release=True)
    if a.cmd == "done":
        c = commit()
        return send("changelog", f"✅ [{n}'s agent] {' '.join(a.text)}" + (f" · {c}" if c else ""))
    text = " ".join(a.text)
    if a.to or a.wake or a.path or a.thread:
        from slack_bridge.common import read_config, request
        try:
            print(json.dumps(request(read_config(), '/post', {'text': text, 'channel': a.channel, 'to': a.to,
                'paths': a.path, 'priority': a.priority, 'wake': a.wake, 'thread': a.thread})))
            return 0
        except Exception as error:
            print('slack: task post failed (' + type(error).__name__ + ')', file=sys.stderr)
            return 1
    if not re.match(r"\[.+'s agent\]", text):
        text = f"[{n}'s agent] {text}"
    return send(a.channel, (KINDS[a.kind] + " " if a.kind else "") + text)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

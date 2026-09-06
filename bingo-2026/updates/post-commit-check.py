#!/usr/bin/env python3
"""PostToolUse(Bash) hook.

After a git commit/push that changed the Bingo board and left it ahead of the last
Signal post, print a reminder (as hook additionalContext) to draft the weekly update.
Reads the hook JSON payload on stdin. Silent (exit 0) unless it has something to say.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # bingo-2026/updates
ROOT = HERE.parent.parent                        # repo root

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

cmd = (payload.get("tool_input") or {}).get("command", "")
if not re.search(r"\bgit\b.*\b(commit|push)\b", cmd, re.S):
    sys.exit(0)


def git(*args):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True
    ).stdout


if "bingo-2026/index.html" not in git("show", "--stat", "--format=", "HEAD"):
    sys.exit(0)

try:
    html = (ROOT / "bingo-2026" / "index.html").read_text(encoding="utf-8")
    live = json.loads(re.search(r"var state = (\{.*?\});", html, re.S).group(1))
    prev = json.loads((HERE / "last-post.json").read_text(encoding="utf-8"))["state"]
except Exception:
    sys.exit(0)

new = sum(len(set(ids) - set(prev.get(k, []))) for k, ids in live.items())
if new == 0:
    sys.exit(0)

msg = (
    f"The Bingo board was just committed with {new} new completed square(s) since the "
    f"last Signal post. Draft Anita's weekly update now: run "
    f'`python3 "{HERE / "draft-update.py"}"`, show her the draft, and ask for the intro '
    f"paragraph. After she confirms it's posted, update "
    f'"{HERE / "last-post.json"}" and append the final text to '
    f'"{HERE / "history.md"}", then commit both.'
)
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": msg,
}}))

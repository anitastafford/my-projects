#!/usr/bin/env bash
# PostToolUse(Bash) hook: after a commit/push that changes the Bingo board and leaves
# it ahead of the last Signal post, remind Claude to draft the weekly update.
# Reads the hook JSON payload on stdin. Silent (exit 0) unless it has something to say.

ROOT="/Users/anita/Library/Mobile Documents/com~apple~CloudDocs/** PROJECTS 🟣/Github Projects"
UPDATES="$ROOT/bingo-2026/updates"

python3 - "$ROOT" "$UPDATES" <<'PY'
import json, re, subprocess, sys

root, updates = sys.argv[1], sys.argv[2]

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

cmd = (payload.get("tool_input") or {}).get("command", "")
if not re.search(r"\bgit\b.*\b(commit|push)\b", cmd):
    sys.exit(0)

def git(*args):
    return subprocess.run(["git", "-C", root, *args],
                          capture_output=True, text=True).stdout

# Did the current HEAD touch the board?
if "bingo-2026/index.html" not in git("show", "--stat", "--format=", "HEAD"):
    sys.exit(0)

# Is the live board actually ahead of the last posted snapshot?
try:
    html = open(f"{root}/bingo-2026/index.html", encoding="utf-8").read()
    live = json.loads(re.search(r"var state = (\{.*?\});", html, re.S).group(1))
    prev = json.loads(open(f"{updates}/last-post.json", encoding="utf-8").read())["state"]
except Exception:
    sys.exit(0)

new = 0
for k, ids in live.items():
    new += len(set(ids) - set(prev.get(k, [])))
if new == 0:
    sys.exit(0)

msg = (
    f"The Bingo board was just committed with {new} new completed square(s) since the "
    f"last Signal post. Draft Anita's weekly update now: run "
    f'`python3 "{updates}/draft-update.py"`, show her the draft, and ask for the intro '
    f"paragraph. After she confirms it's posted, update {updates}/last-post.json and "
    f"append the final text to {updates}/history.md, then commit both."
)
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": msg,
}}))
PY

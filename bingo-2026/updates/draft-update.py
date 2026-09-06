#!/usr/bin/env python3
"""Draft the weekly Bingo 2026 Signal update.

Diffs the live board (bingo-2026/index.html) against the last posted snapshot
(updates/last-post.json) and prints the recap in Anita's format. She fills in the
intro paragraph; everything else is generated.

Usage:
  python3 draft-update.py                 # normal: diff vs updates/last-post.json
  python3 draft-update.py --date 2026-09-06   # override the week's date
  python3 draft-update.py --since 3dc2cb3     # diff vs a git commit instead (for testing)
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # bingo-2026/updates
BINGO_DIR = HERE.parent                          # bingo-2026
INDEX_HTML = BINGO_DIR / "index.html"
LAST_POST = HERE / "last-post.json"

BOARD_URL = "https://anitastafford.github.io/my-projects/bingo-2026/"

# Fixed post order: (id, display name, heart emoji)
PEOPLE = [
    ("marie", "Marié", "💚"),
    ("maya", "Maya", "🩷"),
    ("anita", "Anita", "💜"),
    ("shawn", "Shawn", "🩵"),
    ("mila", "Mila", "💗"),
    ("max", "Max", "💛"),
]


def parse_board(html):
    """Return (state dict {index:int -> [ids]}, titles list indexed by card index)."""
    m = re.search(r"var state = (\{.*?\});", html, re.S)
    if not m:
        sys.exit("Could not find `var state = {...};` in index.html")
    state = {int(k): v for k, v in json.loads(m.group(1)).items()}

    grid = re.search(r'<div class="grid">(.*?)\n  </div>', html, re.S)
    if not grid:
        sys.exit("Could not find the .grid block in index.html")
    titles = re.findall(r"<p>(.*?)</p>", grid.group(1), re.S)
    titles = [re.sub(r"\s+", " ", t).strip() for t in titles]
    return state, titles


def load_previous_state(since):
    if since:
        html = subprocess.run(
            ["git", "show", f"{since}:bingo-2026/index.html"],
            capture_output=True, text=True, check=True,
            cwd=BINGO_DIR.parent,
        ).stdout
        prev, _ = parse_board(html)
        return prev, since
    data = json.loads(LAST_POST.read_text(encoding="utf-8"))
    return {int(k): v for k, v in data["state"].items()}, f"week {data['week']} ({data['date']})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="date of this update, YYYY-MM-DD (default: today)")
    ap.add_argument("--since", help="diff against this git ref instead of last-post.json")
    args = ap.parse_args()

    when = (
        datetime.date.fromisoformat(args.date) if args.date else datetime.date.today()
    )
    week = when.isocalendar()[1]

    state, titles = parse_board(INDEX_HTML.read_text(encoding="utf-8"))
    prev, prev_label = load_previous_state(args.since)
    total = len(titles)

    def count(pid):
        return sum(1 for ids in state.values() if pid in ids)

    def new_squares(pid):
        out = []
        for idx in sorted(state):
            if pid in state[idx] and pid not in prev.get(idx, []):
                out.append(titles[idx] if idx < len(titles) else f"square {idx}")
        return out

    # ---- stderr sanity summary ----
    changes = 0
    print(f"[diff vs {prev_label}]  week {week} ({when.isoformat()})", file=sys.stderr)
    for pid, name, _ in PEOPLE:
        ns = new_squares(pid)
        changes += len(ns)
        for t in ns:
            print(f"  + {name}: {t}", file=sys.stderr)
    print(f"  {changes} new square(s) total\n", file=sys.stderr)

    # ---- stdout: the post ----
    lines = [f"WEEK {week} BINGO UPDATE!", "", "<INTRO PARAGRAPH — replace me>", BOARD_URL, ""]
    for pid, name, heart in PEOPLE:
        lines.append(f"{heart} {name} ({count(pid)}/{total})")
        for t in new_squares(pid):
            lines.append(f"-- {t} ⭐")
        lines.append("")
    print("\n".join(lines).rstrip() + "\n")


if __name__ == "__main__":
    main()

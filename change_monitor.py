#!/usr/bin/env python3
"""Recipe 5 — change_monitor: hash a page, report when its text changes.

Stores a baseline (SHA-256 of the normalised visible text plus the
text lines themselves). On re-check it reports UNCHANGED, or CHANGED
with the first differing line as a compact diff summary.

Examples:
    python change_monitor.py fixtures/page_v1.html --baseline page.json --init
    python change_monitor.py fixtures/page_v2.html --baseline page.json
    python change_monitor.py --demo
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys

from common import fetch_text


def normalize_lines(html: str) -> list[str]:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html,
                  flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "\n", text)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    return [ln for ln in lines if ln]


def content_hash(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def first_diff(old: list[str], new: list[str]) -> str:
    for i, (a, b) in enumerate(zip(old, new)):
        if a != b:
            return f"line {i + 1}: - {a!r} → + {b!r}"
    if len(new) > len(old):
        return f"line {len(old) + 1}: added {new[len(old)]!r}"
    if len(old) > len(new):
        return f"line {len(new) + 1}: removed {old[len(new)]!r}"
    return "(hash differs but lines match after normalisation)"


def check(source: str, baseline_path: str, init: bool = False) -> tuple[str, str]:
    lines = normalize_lines(fetch_text(source))
    digest = content_hash(lines)
    if init:
        with open(baseline_path, "w", encoding="utf-8") as fh:
            json.dump({"source": source, "hash": digest, "lines": lines}, fh, indent=2)
        return "BASELINE", f"saved hash {digest[:12]}… ({len(lines)} lines) from {source}"
    try:
        with open(baseline_path, encoding="utf-8") as fh:
            base = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return "NO BASELINE", f"no baseline at {baseline_path} — run with --init first"
    if base["hash"] == digest:
        return "UNCHANGED", f"hash {digest[:12]}… matches baseline"
    return "CHANGED", first_diff(base["lines"], lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Monitor a page for content changes via hashing.")
    p.add_argument("source", nargs="?", help="Page URL or local HTML file")
    p.add_argument("--baseline", default=".change_baseline.json",
                   help="Baseline JSON file (default: .change_baseline.json)")
    p.add_argument("--init", action="store_true", help="Save current content as the baseline")
    p.add_argument("--demo", action="store_true",
                   help="Baseline fixtures/page_v1.html in memory, then check page_v2.html")
    args = p.parse_args(argv)

    if args.demo:
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            base = os.path.join(td, "base.json")
            status, detail = check("fixtures/page_v1.html", base, init=True)
            print(f"{status}: {detail}")
            status, detail = check("fixtures/page_v1.html", base)
            print(f"{status}: fixtures/page_v1.html — {detail}")
            status, detail = check("fixtures/page_v2.html", base)
            print(f"{status}: fixtures/page_v2.html — {detail}")
        return 0

    if not args.source:
        p.error("give a source or --demo")
    status, detail = check(args.source, args.baseline, init=args.init)
    print(f"{status}: {args.source} — {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

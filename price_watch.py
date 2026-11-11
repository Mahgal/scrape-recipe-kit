#!/usr/bin/env python3
"""Recipe 1 — price_watch: watch product pages and print price diffs.

Extraction is deliberately dependency-free: a small regex finder looks
for an element whose class contains ``price`` and pulls the first
currency amount out of it, falling back to the first currency amount
on the page. No real store is scraped by the demo — it compares two
bundled fixture pages.

Examples:
    python price_watch.py --demo
    python price_watch.py --baseline prices.json fixtures/product_a.html
    python price_watch.py --config watch.json --baseline prices.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from common import fetch_text

_PRICE_CLASS_RE = re.compile(
    r'class="[^"]*price[^"]*"[^>]*>\s*([^<]+)', re.IGNORECASE
)
_AMOUNT_RE = re.compile(r"([$¥€£])\s?(\d[\d,]*\.?\d*)")
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)


def extract_title(html: str) -> str:
    for pattern in (_H1_RE, _TITLE_RE):
        m = pattern.search(html)
        if m:
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
    return "(untitled)"


def extract_price(html: str) -> tuple[str, float] | None:
    """Return (raw_text, numeric_value) for the price, or None."""
    candidates = _PRICE_CLASS_RE.findall(html) or [html]
    for text in candidates:
        m = _AMOUNT_RE.search(text)
        if m:
            return m.group(0), float(m.group(2).replace(",", ""))
    # Fallback: first currency amount anywhere on the page.
    m = _AMOUNT_RE.search(html)
    if m:
        return m.group(0), float(m.group(2).replace(",", ""))
    return None


def snapshot(source: str) -> dict:
    html = fetch_text(source)
    price = extract_price(html)
    return {
        "source": source,
        "title": extract_title(html),
        "price_text": price[0] if price else None,
        "price": price[1] if price else None,
    }


def diff_snapshots(old: dict, new: dict) -> list[str]:
    lines = []
    if old.get("price") != new.get("price"):
        old_p, new_p = old.get("price"), new.get("price")
        if old_p and new_p:
            delta = new_p - old_p
            pct = delta / old_p * 100 if old_p else 0.0
            arrow = "▲" if delta > 0 else "▼"
            lines.append(
                f"{new['title']}: {old['price_text']} → {new['price_text']} "
                f"({arrow} {delta:+.2f}, {pct:+.1f}%) [{new['source']}]"
            )
        else:
            lines.append(
                f"{new['title']}: price appeared/disappeared "
                f"{old.get('price_text')} → {new.get('price_text')} [{new['source']}]"
            )
    return lines


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Watch product-page prices and print diffs.")
    p.add_argument("sources", nargs="*", help="Product page URLs or local HTML files")
    p.add_argument("--config", help="JSON list of {name?, url|file, source} entries")
    p.add_argument("--baseline", default=".price_baseline.json",
                   help="Baseline snapshot JSON file (default: .price_baseline.json)")
    p.add_argument("--demo", action="store_true",
                   help="Compare bundled fixtures/product_a.html vs product_b.html")
    args = p.parse_args(argv)

    if args.demo:
        old = snapshot("fixtures/product_a.html")
        new = snapshot("fixtures/product_b.html")
        diffs = diff_snapshots(old, new)
        print("Price watch demo (fixture A → fixture B)")
        print(f"  before: {old['title']} — {old['price_text']}")
        print(f"  after:  {new['title']} — {new['price_text']}")
        print("Diff:")
        for line in diffs or ["  (no price change)"]:
            print(f"  {line}" if not line.startswith(" ") else line)
        return 0

    sources = list(args.sources)
    if args.config:
        with open(args.config, encoding="utf-8") as fh:
            for entry in json.load(fh):
                sources.append(entry.get("url") or entry.get("file") or entry["source"])
    if not sources:
        p.error("give at least one source, --config, or --demo")

    current = {s: snapshot(s) for s in sources}
    try:
        with open(args.baseline, encoding="utf-8") as fh:
            old_data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        old_data = {}

    changed = 0
    for src, snap in current.items():
        if src in old_data:
            for line in diff_snapshots(old_data[src], snap):
                print(line)
                changed += 1
        else:
            print(f"NEW  {snap['title']}: {snap['price_text']} [{src}]")
    if old_data and changed == 0:
        print("No price changes.")
    with open(args.baseline, "w", encoding="utf-8") as fh:
        json.dump(current, fh, indent=2, ensure_ascii=False)
    print(f"Baseline saved to {args.baseline} ({len(current)} item(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Recipe 3 — rss_digest: merge RSS/Atom feeds into one Markdown digest.

Examples:
    python rss_digest.py https://news.ycombinator.com/rss
    python rss_digest.py fixtures/feed_sample.xml fixtures/feed_atom.xml -o digest.md
    python rss_digest.py https://news.ycombinator.com/rss --limit 5
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from datetime import date

from common import fetch_text

ATOM = "{http://www.w3.org/2005/Atom}"


def _text(elem, *names: str) -> str:
    for name in names:
        child = elem.find(name)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def parse_feed(xml_text: str, source: str = "") -> list[dict]:
    root = ET.fromstring(xml_text)
    items: list[dict] = []
    # RSS 2.0: <channel><item>
    channel_title = ""
    for channel in root.iter("channel"):
        channel_title = _text(channel, "title")
        for item in channel.findall("item"):
            link = _text(item, "link")
            items.append({
                "title": _text(item, "title") or "(untitled)",
                "link": link,
                "date": _text(item, "pubDate", "date"),
                "summary": _text(item, "description")[:200],
                "source": channel_title or source,
            })
    # Atom: <feed><entry>
    if not items:
        feed_title = _text(root, f"{ATOM}title")
        for entry in root.findall(f"{ATOM}entry"):
            link = ""
            for link_elem in entry.findall(f"{ATOM}link"):
                if link_elem.get("rel") in (None, "alternate"):
                    link = link_elem.get("href", "")
                    break
            items.append({
                "title": _text(entry, f"{ATOM}title") or "(untitled)",
                "link": link,
                "date": _text(entry, f"{ATOM}updated", f"{ATOM}published"),
                "summary": _text(entry, f"{ATOM}summary")[:200],
                "source": feed_title or source,
            })
    return items


def build_digest(feeds_items: list[list[dict]], title: str | None = None,
                 limit: int | None = None) -> str:
    title = title or f"Feed Digest — {date.today().isoformat()}"
    lines = [f"# {title}", ""]
    total = 0
    for items in feeds_items:
        if not items:
            continue
        source = items[0]["source"] or "Feed"
        lines += [f"## {source}", ""]
        for item in (items[:limit] if limit else items):
            date_part = f" — {item['date']}" if item["date"] else ""
            lines.append(f"- [{item['title']}]({item['link']}){date_part}")
            total += 1
        lines.append("")
    lines.append(f"_{total} item(s) from {len(feeds_items)} feed(s)._")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Aggregate RSS/Atom feeds into a Markdown digest.")
    p.add_argument("sources", nargs="*", help="Feed URLs or local XML files")
    p.add_argument("-o", "--output", help="Write digest to this file instead of stdout")
    p.add_argument("--title", help="Digest title")
    p.add_argument("--limit", type=int, help="Max items per feed")
    args = p.parse_args(argv)

    sources = args.sources or ["https://news.ycombinator.com/rss"]
    feeds = [parse_feed(fetch_text(s), source=s) for s in sources]
    digest = build_digest(feeds, title=args.title, limit=args.limit)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(digest)
        print(f"Wrote {args.output}")
    else:
        print(digest, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

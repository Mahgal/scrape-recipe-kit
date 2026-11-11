#!/usr/bin/env python3
"""Recipe 2 — sitemap_diff: diff two sitemap XML files.

Prints URLs that were added and URLs that disappeared between an old
and a new sitemap. Works with local files or URLs, plain ``<urlset>``
documents (the common case).

Examples:
    python sitemap_diff.py fixtures/sitemap_old.xml fixtures/sitemap_new.xml
    python sitemap_diff.py https://example.com/sitemap-old.xml https://example.com/sitemap.xml
    python sitemap_diff.py old.xml new.xml --json
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET

from common import fetch_text


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_sitemap(xml_text: str) -> set[str]:
    root = ET.fromstring(xml_text)
    urls: set[str] = set()
    for elem in root.iter():
        if _local(elem.tag) == "loc" and elem.text:
            urls.add(elem.text.strip())
    return urls


def diff_sitemaps(old_xml: str, new_xml: str) -> tuple[list[str], list[str]]:
    old, new = parse_sitemap(old_xml), parse_sitemap(new_xml)
    return sorted(new - old), sorted(old - new)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Diff two sitemap XML files (added / removed URLs).")
    p.add_argument("old", help="Old sitemap (local file or URL)")
    p.add_argument("new", help="New sitemap (local file or URL)")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = p.parse_args(argv)

    added, removed = diff_sitemaps(fetch_text(args.old), fetch_text(args.new))
    if args.json:
        print(json.dumps({"added": added, "removed": removed}, indent=2))
    else:
        print(f"Added ({len(added)}):")
        for u in added:
            print(f"  + {u}")
        print(f"Removed ({len(removed)}):")
        for u in removed:
            print(f"  - {u}")
        print(f"Summary: +{len(added)} / -{len(removed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

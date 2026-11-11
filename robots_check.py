#!/usr/bin/env python3
"""Recipe 4 — robots_check: is a path allowed by robots.txt?

Parses robots.txt itself (instead of hiding behind robotparser) so it
can print the exact rule that matched — the thing you actually want
when debugging a crawl.

Examples:
    python robots_check.py https://example.com /private/page
    python robots_check.py --robots fixtures/robots.txt --path /admin/panel
    python robots_check.py --robots fixtures/robots.txt --path /blog/post --agent MyBot
"""
from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

from common import USER_AGENT, fetch_text


class RobotsRules:
    """Minimal robots.txt parser: user-agent groups, Allow/Disallow."""

    def __init__(self, text: str):
        self.groups: list[dict] = []  # {agents: [...], rules: [(kind, pattern)]}
        current = None
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, _, value = line.partition(":")
            key, value = key.strip().lower(), value.strip()
            if key == "user-agent":
                if current is None or current["rules"]:
                    current = {"agents": [], "rules": []}
                    self.groups.append(current)
                current["agents"].append(value)
            elif key in ("allow", "disallow") and current is not None:
                current["rules"].append((key, value))

    def _group_for(self, agent: str) -> dict | None:
        agent_l = agent.lower()
        wildcard = None
        for group in self.groups:
            agents = [a.lower() for a in group["agents"]]
            if any(a != "*" and a in agent_l for a in agents):
                return group
            if "*" in agents:
                wildcard = wildcard or group
        return wildcard

    def check(self, path: str, agent: str = "*") -> tuple[bool, str]:
        """Return (allowed, explanation naming the matched rule)."""
        group = self._group_for(agent)
        if group is None:
            return True, "no matching user-agent group — allowed by default"
        best: tuple[int, str, str] | None = None  # (len, kind, pattern)
        for kind, pattern in group["rules"]:
            if pattern and path.startswith(pattern):
                if best is None or len(pattern) > best[0] or (
                    len(pattern) == best[0] and kind == "allow"
                ):
                    best = (len(pattern), kind, pattern)
        if best is None:
            return True, "no Allow/Disallow rule matches this path — allowed"
        _, kind, pattern = best
        return kind == "allow", f"matched rule: {kind.capitalize()}: {pattern}"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Check whether robots.txt allows crawling a path.")
    p.add_argument("target", nargs="?", help="Site base URL, e.g. https://example.com")
    p.add_argument("path", nargs="?", default="/", help="Path to check (default: /)")
    p.add_argument("--robots", help="Local robots.txt file (offline mode)")
    p.add_argument("--path", dest="path_opt", help="Path to check (overrides positional path)")
    p.add_argument("--agent", default=USER_AGENT, help="User-Agent to test as")
    args = p.parse_args(argv)
    if args.path_opt:
        args.path = args.path_opt

    if args.robots:
        text = fetch_text(args.robots)
        origin = args.robots
    elif args.target:
        parsed = urlparse(args.target)
        if not parsed.scheme:
            parsed = urlparse("https://" + args.target)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        # If target itself looks like a full page URL and no path arg differs, use its path.
        text = fetch_text(robots_url)
        origin = robots_url
        if args.path == "/" and parsed.path not in ("", "/"):
            args.path = parsed.path
    else:
        p.error("give a target URL or --robots <file>")

    allowed, why = RobotsRules(text).check(args.path, agent=args.agent)
    verdict = "ALLOWED" if allowed else "DISALLOWED"
    print(f"{verdict}: {args.path}")
    print(f"  robots: {origin}")
    print(f"  agent:  {args.agent}")
    print(f"  reason: {why}")
    return 0 if allowed else 2


if __name__ == "__main__":
    sys.exit(main())

"""Offline tests — every test runs against local fixtures only."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
FIX = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def read(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read()


# --- common -------------------------------------------------------------
def test_fetch_text_reads_local_file():
    from common import fetch_text
    assert "Acme Widget Pro" in fetch_text(os.path.join(FIX, "product_a.html"))


# --- price_watch ----------------------------------------------------------
def test_extract_price_from_fixture():
    from price_watch import extract_price, extract_title
    price = extract_price(read("product_a.html"))
    assert price == ("$49.99", 49.99)
    assert extract_title(read("product_a.html")) == "Acme Widget Pro"


def test_price_diff_detects_drop():
    from price_watch import snapshot, diff_snapshots
    old = snapshot(os.path.join(FIX, "product_a.html"))
    new = snapshot(os.path.join(FIX, "product_b.html"))
    diffs = diff_snapshots(old, new)
    assert len(diffs) == 1
    assert "$49.99" in diffs[0] and "$39.99" in diffs[0]
    assert "-20.0%" in diffs[0]


def test_price_no_change_no_diff():
    from price_watch import snapshot, diff_snapshots
    snap = snapshot(os.path.join(FIX, "product_a.html"))
    assert diff_snapshots(snap, snap) == []


# --- sitemap_diff -----------------------------------------------------------
def test_sitemap_diff_added_and_removed():
    from sitemap_diff import diff_sitemaps
    added, removed = diff_sitemaps(read("sitemap_old.xml"), read("sitemap_new.xml"))
    assert added == [
        "https://example.com/blog/new-post",
        "https://example.com/features",
    ]
    assert removed == ["https://example.com/blog/old-post"]


def test_sitemap_identical_no_diff():
    from sitemap_diff import diff_sitemaps
    assert diff_sitemaps(read("sitemap_old.xml"), read("sitemap_old.xml")) == ([], [])


# --- rss_digest ---------------------------------------------------------------
def test_parse_rss_fixture():
    from rss_digest import parse_feed
    items = parse_feed(read("feed_sample.xml"))
    assert len(items) == 2
    assert items[0]["title"] == "Polite Scraping in Practice"
    assert items[0]["source"] == "Sample Engineering Blog"


def test_parse_atom_fixture():
    from rss_digest import parse_feed
    items = parse_feed(read("feed_atom.xml"))
    assert len(items) == 1
    assert items[0]["link"] == "https://example.com/journal/hashes-beat-screenshots"


def test_build_digest_markdown():
    from rss_digest import parse_feed, build_digest
    digest = build_digest(
        [parse_feed(read("feed_sample.xml")), parse_feed(read("feed_atom.xml"))],
        title="Test Digest",
    )
    assert digest.startswith("# Test Digest")
    assert "## Sample Engineering Blog" in digest
    assert "_3 item(s) from 2 feed(s)._" in digest


# --- robots_check ---------------------------------------------------------------
def test_robots_disallow_admin():
    from robots_check import RobotsRules
    allowed, why = RobotsRules(read("robots.txt")).check("/admin/panel")
    assert allowed is False
    assert "Disallow: /admin/" in why


def test_robots_longest_match_allow_wins():
    from robots_check import RobotsRules
    allowed, why = RobotsRules(read("robots.txt")).check("/private/public/page")
    assert allowed is True
    assert "Allow: /private/public/" in why


def test_robots_specific_agent_blocked_everywhere():
    from robots_check import RobotsRules
    allowed, _ = RobotsRules(read("robots.txt")).check("/blog/post", agent="BadBot/1.0")
    assert allowed is False


# --- change_monitor ---------------------------------------------------------------
def test_change_monitor_unchanged_then_changed(tmp_path):
    from change_monitor import check
    base = str(tmp_path / "base.json")
    status, _ = check(os.path.join(FIX, "page_v1.html"), base, init=True)
    assert status == "BASELINE"
    status, _ = check(os.path.join(FIX, "page_v1.html"), base)
    assert status == "UNCHANGED"
    status, detail = check(os.path.join(FIX, "page_v2.html"), base)
    assert status == "CHANGED"
    assert "Version 1.1" in detail


def test_normalize_strips_scripts_and_styles():
    from change_monitor import normalize_lines
    lines = normalize_lines(read("page_v1.html"))
    assert any("Version 1.0" in ln for ln in lines)
    assert not any("console.log" in ln or "color:#111" in ln for ln in lines)

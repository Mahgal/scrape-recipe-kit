# scrape-recipe-kit

**Five small, polite web-scraping recipes you can actually run — price watches, sitemap diffs, RSS digests, robots.txt checks, and page-change monitors — in plain Python, with no framework lock-in.**

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Dependencies](https://img.shields.io/badge/deps-requests%20only-orange) ![Tests](https://img.shields.io/badge/tests-14%20passing-brightgreen) ![Offline demos](https://img.shields.io/badge/demos-offline%20fixtures-lightgrey)

Anti-blocking headlines sell frameworks. Most real scraping jobs don't need one: they need a descriptive User-Agent, a timeout, a couple of retries, respect for `robots.txt`, and a script small enough to read in one sitting. That's exactly what's in this repo — five copy-pasteable recipes, one shared polite-fetching module, and fixtures so every demo runs offline.

## Recipes

| # | Script | What it does | Input | Output |
|---|--------|--------------|-------|--------|
| 1 | `price_watch.py` | Watches product pages, extracts the price (minimal hand-rolled finder, no parser dependency), reports changes | HTML pages (URL or local file), or a JSON watch-list | Price diff lines with delta and % change |
| 2 | `sitemap_diff.py` | Compares two sitemap XML documents | Two sitemaps (URL or local file) | Added / removed URL lists (`--json` available) |
| 3 | `rss_digest.py` | Merges RSS 2.0 and Atom feeds into one daily digest | One or more feeds (URL or local file) | A Markdown digest, stdout or `-o file` |
| 4 | `robots_check.py` | Answers "may I crawl this path?" and shows *which rule decided it* | A site URL, or a local `robots.txt` with `--robots` | `ALLOWED` / `DISALLOWED` + the matched rule (exit code 2 when disallowed) |
| 5 | `change_monitor.py` | Hashes a page's normalised visible text; on re-check reports change + first differing line | A page (URL or local file) + a baseline JSON | `UNCHANGED` / `CHANGED` + one-line diff summary |

All five share `common.py`: one place for the User-Agent, timeout (15 s), retries (3, with backoff), and inter-request delay (1 s). Tune politeness once, everywhere.

## Quick start

```bash
git clone https://github.com/Mahgal/scrape-recipe-kit.git && cd scrape-recipe-kit
pip install -r requirements.txt        # just requests

# 1 — price watch (offline demo, no real store is scraped)
python price_watch.py --demo

# 2 — sitemap diff (offline fixtures)
python sitemap_diff.py fixtures/sitemap_old.xml fixtures/sitemap_new.xml

# 3 — RSS digest (live, public feed)
python rss_digest.py https://news.ycombinator.com/rss --limit 5

# 4 — robots check (offline fixture)
python robots_check.py --robots fixtures/robots.txt --path /admin/panel

# 5 — change monitor (offline demo)
python change_monitor.py --demo

# Tests — fully offline, fixture-based
python -m pytest tests/ -q
```

Every script accepts local files anywhere it accepts a URL, and every script has `--help`.

## Real run output

Captured verbatim on 2026-11-09 from the commands above.

### `sitemap_diff.py` — bundled fixtures

```console
$ python sitemap_diff.py fixtures/sitemap_old.xml fixtures/sitemap_new.xml
Added (2):
  + https://example.com/blog/new-post
  + https://example.com/features
Removed (1):
  - https://example.com/blog/old-post
Summary: +2 / -1
```

### `rss_digest.py` — live Hacker News RSS

```console
$ python rss_digest.py https://news.ycombinator.com/rss --limit 5 --title "Hacker News Digest — live demo"
# Hacker News Digest — live demo

## Hacker News

- [Goldman Sachs Is Pulling Claude Code from Its Bankers and Traders](https://www.thestateofai.com/news/goldman-sachs-claude-code-traders-bankers) — Sun, 08 Nov 2026 18:16:07 +0000
- [Llama-modchip: 284B DeepSeek on 64GB RAM, no GPU](https://github.com/synchopate/llama-modchip) — Sun, 08 Nov 2026 10:22:04 +0000
- [The Reconstruction of Torn Documents](https://www.bundesarchiv.de/en/stasi-records-archive/the-reconstruction-of-torn-documents/) — Fri, 06 Nov 2026 09:05:18 +0000
- [UK House of Lords to propose mandatory CSAM detection software on smartphones](https://observer.co.uk/news/national/article/fight-to-block-child-sexual-abuse-images-unites-peers-and-mps-in-cross-party-campaign) — Sun, 08 Nov 2026 15:57:37 +0000
- [Writing as a thinking tool](http://muratbuffalo.blogspot.com/2026/11/writing-as-thinking-tool.html) — Sun, 08 Nov 2026 10:41:52 +0000

_5 item(s) from 1 feed(s)._
```

### The other three recipes

```console
$ python price_watch.py --demo
Price watch demo (fixture A → fixture B)
  before: Acme Widget Pro — $49.99
  after:  Acme Widget Pro — $39.99
Diff:
  Acme Widget Pro: $49.99 → $39.99 (▼ -10.00, -20.0%) [fixtures/product_b.html]

$ python robots_check.py --robots fixtures/robots.txt --path /admin/panel
DISALLOWED: /admin/panel
  robots: fixtures/robots.txt
  agent:  scrape-recipe-kit/1.0 (+https://example.com/scrape-recipe-kit; polite recipe demos)
  reason: matched rule: Disallow: /admin/

$ python change_monitor.py --demo
BASELINE: saved hash a2eb09c9fa58… (4 lines) from fixtures/page_v1.html
UNCHANGED: fixtures/page_v1.html — hash a2eb09c9fa58… matches baseline
CHANGED: fixtures/page_v2.html — line 3: - 'Version 1.0 ships the dashboard.' → + 'Version 1.1 ships the dashboard and exports.'
```

## Recipe notes

### 1. `price_watch.py` — price watching without a parser dependency
The extractor looks for an element whose `class` contains `price` and pulls the first currency amount (`$ ¥ € £`) out of it, falling back to the first amount on the page. Point it at pages with `--baseline prices.json` and it prints only changes, then rewrites the baseline — ready to run from cron. A JSON watch-list works too: `python price_watch.py --config fixtures/watch.json --baseline prices.json`. The demo uses fictional fixture products on purpose: don't learn scraping by hammering a real store.

### 2. `sitemap_diff.py` — the cheapest site-change detector you own
Sitemaps are a site's own changelog. Diff yesterday's against today's and you get new pages and silently deleted pages, with zero page fetches. Add `--json` for pipelines. Works on `<urlset>` documents (including namespaced ones).

### 3. `rss_digest.py` — many feeds, one Markdown page
Parses RSS 2.0 (`<channel>/<item>`) and Atom (`<entry>`) with the standard library, groups items by feed, and emits clean Markdown — drop it into a notes app, a static site, or a daily email. `--limit N` caps items per feed; `-o digest.md` writes to a file.

### 4. `robots_check.py` — check before you crawl, see the rule
Instead of hiding behind a boolean, this parser implements longest-match Allow/Disallow semantics itself and prints the exact rule that matched — including per-agent groups (try `--agent "BadBot/1.0"` against the fixture). Exit code is `2` when disallowed, so it can gate a crawl in shell scripts.

### 5. `change_monitor.py` — hash the text, not the HTML
Raw HTML changes on every ad rotation. This recipe strips scripts/styles/tags, normalises whitespace, hashes the remaining visible text (SHA-256), and — when it changes — shows the first differing line. That turns "something changed" into "this sentence changed".

## Politeness policy (built in, not bolted on)

- Descriptive User-Agent identifying the tool — see `USER_AGENT` in `common.py`; put your own contact in it before crawling anyone else's site.
- 15 s timeout, at most 3 retries with backoff, 1 s minimum delay between live requests.
- Check `robots.txt` first (recipe 4 exists for a reason). Never crawl pages that require login or that a site prohibits.
- All bundled demos run on local fixtures or one public RSS feed. No real store, no login-walled site, is touched.

## Project layout

```
common.py            # shared polite fetcher (UA / timeout / retry / delay)
price_watch.py       # recipe 1
sitemap_diff.py      # recipe 2
rss_digest.py        # recipe 3
robots_check.py      # recipe 4
change_monitor.py    # recipe 5
fixtures/            # offline demo data (HTML, sitemaps, feeds, robots.txt)
tests/test_recipes.py  # 14 pytest tests, all offline
```

## Need this wired into a real workflow?

These recipes are deliberately small starting points. If you need one of them turned into a scheduled monitor — price alerts to chat/email, sitemap diffs in CI, a digest delivered daily, change alerts for pages you depend on — that kind of small, well-scoped automation build is available as a service via the repository owner's profile. No promises beyond what's in this repo: working code, polite defaults, and tests you can run yourself.

## License

MIT — see `LICENSE`.

"""Shared polite-fetching helpers for scrape-recipe-kit.

Every recipe imports from here so the politeness policy lives in one
place: a descriptive User-Agent, a sane timeout, bounded retries with
backoff, and a minimum delay between requests to the same process.

Only the Python standard library and ``requests`` are used.
Local files are supported everywhere a URL is: pass a filesystem path
or a ``file://`` URL and it will be read from disk instead of the
network. That keeps the demos and the test-suite fully offline.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import requests

USER_AGENT = (
    "scrape-recipe-kit/1.0 "
    "(+https://example.com/scrape-recipe-kit; polite recipe demos)"
)
DEFAULT_TIMEOUT = 15  # seconds
DEFAULT_RETRIES = 3
DEFAULT_DELAY = 1.0  # seconds between live requests
DEFAULT_BACKOFF = 1.5  # multiplier between retries


@dataclass
class PoliteFetcher:
    """A tiny fetcher with retries, backoff, and inter-request delay."""

    user_agent: str = USER_AGENT
    timeout: float = DEFAULT_TIMEOUT
    retries: int = DEFAULT_RETRIES
    delay: float = DEFAULT_DELAY
    backoff: float = DEFAULT_BACKOFF
    _last_request_at: float = field(default=0.0, repr=False)
    _session: requests.Session = field(default_factory=requests.Session, repr=False)

    def __post_init__(self) -> None:
        self._session.headers.update(
            {"User-Agent": self.user_agent, "Accept": "*/*"}
        )

    def _respect_delay(self) -> None:
        if self.delay <= 0:
            return
        elapsed = time.monotonic() - self._last_request_at
        if self._last_request_at and elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def fetch_text(self, source: str) -> str:
        """Return text for a local path, file:// URL, or http(s) URL."""
        if source.startswith("file://"):
            path = source[len("file://"):]
            with open(path, encoding="utf-8") as fh:
                return fh.read()
        if os.path.exists(source):
            with open(source, encoding="utf-8") as fh:
                return fh.read()
        if not source.startswith(("http://", "https://")):
            # Treat unknown scheme-less strings as paths; raise clearly.
            raise FileNotFoundError(
                f"Source not found locally and not an http(s) URL: {source}"
            )

        last_exc: Exception | None = None
        for attempt in range(1, self.retries + 1):
            self._respect_delay()
            try:
                resp = self._session.get(source, timeout=self.timeout)
                self._last_request_at = time.monotonic()
                resp.raise_for_status()
                return resp.text
            except requests.RequestException as exc:  # noqa: BLE001 - re-raised below
                last_exc = exc
                if attempt < self.retries:
                    time.sleep(self.backoff ** attempt * 0.5)
        assert last_exc is not None
        raise last_exc


# Convenience shared instance / helper used by the recipes.
_default_fetcher = PoliteFetcher()


def fetch_text(source: str, **kwargs) -> str:
    """Fetch *source* (local path or URL) with the polite defaults."""
    if kwargs:
        return PoliteFetcher(**kwargs).fetch_text(source)
    return _default_fetcher.fetch_text(source)

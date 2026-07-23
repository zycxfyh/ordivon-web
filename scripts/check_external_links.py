#!/usr/bin/env python3
"""Sample stable external links and fail only on confirmed missing targets."""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MAX_LINKS = 12
IGNORED_DIRECTORY_NAMES = {".git", "node_modules", "artifacts", "playwright-report", "test-results"}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        parts = urlsplit(href)
        if parts.scheme in {"http", "https"} and parts.netloc != "ordivon.com":
            self.links.add(href)


def sample_links() -> list[str]:
    parser = LinkParser()
    for path in sorted(ROOT.rglob("*.html")):
        if not IGNORED_DIRECTORY_NAMES.intersection(path.parts):
            parser.feed(path.read_text(encoding="utf-8"))
    preferred = sorted(parser.links, key=lambda url: ("github.com" not in url, url))
    return preferred[:MAX_LINKS]


def status_for(url: str) -> int | None:
    headers = {"User-Agent": "ordivon-web-link-check/1.0"}
    for method in ("HEAD", "GET"):
        try:
            request = urllib.request.Request(url, headers=headers, method=method)
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.status
        except urllib.error.HTTPError as exc:
            if exc.code in {405, 501} and method == "HEAD":
                continue
            return exc.code
        except (urllib.error.URLError, TimeoutError):
            return None
    return None


def main() -> int:
    failures: list[tuple[str, int]] = []
    inconclusive: list[str] = []
    links = sample_links()
    if not links:
        print("EXTERNAL LINK SAMPLE FAILED: no external links found", file=sys.stderr)
        return 1
    for url in links:
        status = status_for(url)
        if status in {404, 410}:
            failures.append((url, status))
        elif status is None or status == 429 or status >= 500:
            inconclusive.append(url)
            print(f"INCONCLUSIVE {url} status={status}")
        else:
            print(f"OK {url} status={status}")
    if failures:
        for url, status in failures:
            print(f"BROKEN {url} status={status}", file=sys.stderr)
        return 1
    print(
        f"EXTERNAL LINK SAMPLE PASSED: checked={len(links)} "
        f"inconclusive={len(inconclusive)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

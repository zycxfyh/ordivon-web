#!/usr/bin/env python3
"""Verify the small, static contract of the Ordivon public site."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CNAME = "lab.ordivon.com"
REQUIRED_FILES = (
    "index.html",
    "404.html",
    "assets/styles.css",
    "assets/app.js",
    "assets/mark.svg",
    ".nojekyll",
    "CNAME",
)

REMOTE_SCHEMES = {"http", "https", "data", "javascript"}
RUNTIME_ASSET_ATTRIBUTES = {
    "script": ("src",),
    "img": ("src", "srcset"),
    "source": ("src", "srcset"),
    "video": ("src", "poster"),
    "audio": ("src",),
    "iframe": ("src",),
}
TRACKING_PATTERNS = {
    "Google Analytics": r"google-analytics|googletagmanager|\bgtag\s*\(",
    "Plausible": r"plausible\.io",
    "Segment": r"cdn\.segment\.com|analytics\.load\s*\(",
    "Mixpanel": r"\bmixpanel\b",
    "Hotjar": r"\bhotjar\b|static\.hotjar\.com",
    "Microsoft Clarity": r"clarity\.ms|\bclarity\s*\(",
    "Meta Pixel": r"connect\.facebook\.net|\bfbq\s*\(",
    "DoubleClick": r"doubleclick\.net",
    "cookie write": r"document\.cookie\s*=",
}
CSS_REMOTE_PATTERN = re.compile(
    r"(?:@import\s+|url\s*\()\s*[\"']?(?:https?:)?//", re.IGNORECASE
)


class SiteHTMLParser(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids: set[str] = set()
        self.fragment_links: list[str] = []
        self.local_links: list[str] = []
        self.runtime_assets: list[tuple[str, str, str]] = []
        self.has_lang = False
        self.has_title = False
        self.has_viewport = False
        self._inside_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()

        if tag == "html" and values.get("lang", "").strip():
            self.has_lang = True
        if tag == "title":
            self._inside_title = True
        if tag == "meta" and values.get("name", "").lower() == "viewport":
            self.has_viewport = bool(values.get("content", "").strip())

        element_id = values.get("id", "").strip()
        if element_id:
            if element_id in self.ids:
                fail(f"{self.path}: duplicate id #{element_id}")
            self.ids.add(element_id)

        href = values.get("href", "").strip()
        if tag == "a" and href:
            if href.startswith("#"):
                self.fragment_links.append(unquote(href[1:]))
            elif is_local_url(href):
                self.local_links.append(href)

        for attribute in RUNTIME_ASSET_ATTRIBUTES.get(tag, ()):
            raw = values.get(attribute, "").strip()
            if not raw:
                continue
            for value in split_srcset(raw) if attribute == "srcset" else (raw,):
                self.runtime_assets.append((tag, attribute, value))

        if tag == "link":
            rel = {part.lower() for part in values.get("rel", "").split()}
            href = values.get("href", "").strip()
            if href and rel.intersection({"stylesheet", "icon", "preload", "modulepreload"}):
                self.runtime_assets.append((tag, "href", href))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._inside_title = False
            self.has_title = bool("".join(self._title_parts).strip())

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self._title_parts.append(data)


def fail(message: str) -> None:
    raise AssertionError(message)


def is_local_url(value: str) -> bool:
    stripped = value.strip()
    if not stripped or stripped.startswith(("#", "mailto:", "tel:")):
        return False
    if stripped.startswith("//"):
        return False
    return urlsplit(stripped).scheme.lower() not in REMOTE_SCHEMES


def split_srcset(value: str) -> tuple[str, ...]:
    candidates: list[str] = []
    for candidate in value.split(","):
        url = candidate.strip().split(maxsplit=1)[0]
        if url:
            candidates.append(url)
    return tuple(candidates)


def resolve_local_reference(source: Path, value: str) -> Path:
    parts = urlsplit(value)
    clean_path = unquote(parts.path)
    if not clean_path:
        return source

    if clean_path.startswith("/"):
        candidate = ROOT / clean_path.lstrip("/")
    else:
        candidate = source.parent / clean_path

    resolved = candidate.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        fail(f"{source}: reference escapes repository root: {value}")
        raise AssertionError from exc

    if resolved.is_dir() or value.endswith("/"):
        resolved = resolved / "index.html"
    return resolved


def check_required_files() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.exists():
            fail(f"missing required file: {relative}")


def check_cname() -> None:
    value = (ROOT / "CNAME").read_text(encoding="utf-8").strip()
    if value != EXPECTED_CNAME:
        fail(f"CNAME must be exactly {EXPECTED_CNAME!r}; found {value!r}")


def check_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    parser = SiteHTMLParser(path.relative_to(ROOT))
    parser.feed(text)
    parser.close()

    if not parser.has_lang:
        fail(f"{path.relative_to(ROOT)}: <html> must declare lang")
    if not parser.has_title:
        fail(f"{path.relative_to(ROOT)}: non-empty <title> is required")
    if not parser.has_viewport:
        fail(f"{path.relative_to(ROOT)}: viewport meta tag is required")

    for fragment in parser.fragment_links:
        if fragment and fragment not in parser.ids:
            fail(f"{path.relative_to(ROOT)}: missing fragment target #{fragment}")

    for value in parser.local_links:
        target = resolve_local_reference(path, value)
        if not target.exists():
            fail(f"{path.relative_to(ROOT)}: broken local link {value!r}")

    for tag, attribute, value in parser.runtime_assets:
        parts = urlsplit(value)
        if value.startswith("//") or parts.scheme.lower() in REMOTE_SCHEMES:
            fail(
                f"{path.relative_to(ROOT)}: external runtime asset is not allowed: "
                f"<{tag} {attribute}={value!r}>"
            )
        target = resolve_local_reference(path, value)
        if not target.is_file():
            fail(
                f"{path.relative_to(ROOT)}: missing local runtime asset "
                f"<{tag} {attribute}={value!r}>"
            )


def check_no_tracking() -> None:
    candidates = [*ROOT.glob("*.html"), *ROOT.glob("assets/*.js")]
    for path in candidates:
        text = path.read_text(encoding="utf-8")
        for name, pattern in TRACKING_PATTERNS.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                fail(f"{path.relative_to(ROOT)}: prohibited tracking pattern: {name}")


def check_css() -> None:
    for path in ROOT.glob("assets/*.css"):
        text = path.read_text(encoding="utf-8")
        if CSS_REMOTE_PATTERN.search(text):
            fail(f"{path.relative_to(ROOT)}: external CSS asset/import is not allowed")


def main() -> int:
    checks = (
        check_required_files,
        check_cname,
        lambda: [check_html(path) for path in sorted(ROOT.glob("*.html"))],
        check_no_tracking,
        check_css,
    )

    try:
        for check in checks:
            check()
    except (AssertionError, OSError, UnicodeError) as exc:
        print(f"SITE CHECK FAILED: {exc}", file=sys.stderr)
        return 1

    html_count = len(list(ROOT.glob("*.html")))
    print(
        f"SITE CHECK PASSED: {html_count} HTML files; "
        f"CNAME={EXPECTED_CNAME}; local runtime assets only; no tracking patterns."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

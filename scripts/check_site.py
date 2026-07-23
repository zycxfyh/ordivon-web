#!/usr/bin/env python3
"""Verify the dependency-free contract of the Ordivon public site."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://ordivon.com"
EXPECTED_CNAME = "ordivon.com"
REQUIRED_FILES = (
    "index.html",
    "404.html",
    "work/index.html",
    "work/ordivon-runtime/index.html",
    "work/finharness/index.html",
    "work/ordivon-web/index.html",
    "notes/index.html",
    "notes/why-ordivon/index.html",
    "now/index.html",
    "about/index.html",
    "contact/index.html",
    "assets/styles.css",
    "assets/umbrella.css",
    "assets/app.js",
    "assets/mark.svg",
    "assets/social/default.png",
    "assets/social/runtime.png",
    "assets/social/finharness.png",
    "assets/social/web.png",
    "feed.xml",
    "site.webmanifest",
    "robots.txt",
    "sitemap.xml",
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
NETWORK_PATTERNS = {
    "external fetch": r"\bfetch\s*\(\s*[\"'](?:https?:)?//",
    "external dynamic import": r"\bimport\s*\(\s*[\"'](?:https?:)?//",
    "external WebSocket": r"\bWebSocket\s*\(\s*[\"'](?:wss?:)?//",
    "external EventSource": r"\bEventSource\s*\(\s*[\"'](?:https?:)?//",
    "external sendBeacon": r"\bsendBeacon\s*\(\s*[\"'](?:https?:)?//",
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
        self.has_description = False
        self.nav_count = 0
        self.has_desktop_navigation = False
        self.has_mobile_navigation = False
        self.has_mobile_summary = False
        self.canonical_href = ""
        self.manifest_href = ""
        self._inside_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()

        if tag == "html" and values.get("lang", "").strip():
            self.has_lang = True
        if tag == "title":
            self._inside_title = True
        classes = set(values.get("class", "").split())
        if tag == "nav":
            self.nav_count += 1
            if "desktop-navigation" in classes:
                self.has_desktop_navigation = True
        if tag == "details" and "mobile-navigation" in classes:
            self.has_mobile_navigation = True
        if tag == "summary" and "mobile-navigation-summary" in classes:
            self.has_mobile_summary = True
        if tag == "meta":
            name = values.get("name", "").lower()
            content = values.get("content", "").strip()
            if name == "viewport":
                self.has_viewport = bool(content)
            if name == "description":
                self.has_description = bool(content)

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
            if "canonical" in rel:
                self.canonical_href = href
            if "manifest" in rel:
                self.manifest_href = href
            if href and rel.intersection(
                {"stylesheet", "icon", "preload", "modulepreload", "manifest"}
            ):
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


def repository_files(suffix: str) -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob(f"*{suffix}")
        if ".git" not in path.parts and path.is_file()
    )


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


def html_route(path: Path) -> str:
    relative = path.relative_to(ROOT)
    if relative == Path("index.html"):
        return "/"
    if relative.name == "index.html":
        return "/" + relative.parent.as_posix().strip("/") + "/"
    return "/" + relative.as_posix()


def expected_canonical(path: Path) -> str:
    return BASE_URL + html_route(path)


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
    relative = path.relative_to(ROOT)
    parser = SiteHTMLParser(relative)
    parser.feed(text)
    parser.close()

    if not parser.has_lang:
        fail(f"{relative}: <html> must declare lang")
    if not parser.has_title:
        fail(f"{relative}: non-empty <title> is required")
    if not parser.has_viewport:
        fail(f"{relative}: viewport meta tag is required")
    if not parser.has_description:
        fail(f"{relative}: non-empty meta description is required")
    if parser.nav_count < 1:
        fail(f"{relative}: at least one navigation landmark is required")
    if not parser.has_desktop_navigation:
        fail(f"{relative}: desktop project navigation is required")
    if not parser.has_mobile_navigation or not parser.has_mobile_summary:
        fail(f"{relative}: keyboard-operable mobile navigation is required")
    if parser.canonical_href != expected_canonical(path):
        fail(
            f"{relative}: canonical must be {expected_canonical(path)!r}; "
            f"found {parser.canonical_href!r}"
        )
    if not parser.manifest_href:
        fail(f"{relative}: local site.webmanifest link is required")

    for fragment in parser.fragment_links:
        if fragment and fragment not in parser.ids:
            fail(f"{relative}: missing fragment target #{fragment}")

    resolved_local_links: list[Path] = []
    for value in parser.local_links:
        target = resolve_local_reference(path, value)
        resolved_local_links.append(target)
        if not target.exists():
            fail(f"{relative}: broken local link {value!r}")

    if (ROOT / "index.html").resolve() not in resolved_local_links:
        fail(f"{relative}: page must contain a local route back to Home")

    for tag, attribute, value in parser.runtime_assets:
        parts = urlsplit(value)
        if value.startswith("//") or parts.scheme.lower() in REMOTE_SCHEMES:
            fail(
                f"{relative}: external runtime asset is not allowed: "
                f"<{tag} {attribute}={value!r}>"
            )
        target = resolve_local_reference(path, value)
        if not target.is_file():
            fail(
                f"{relative}: missing local runtime asset "
                f"<{tag} {attribute}={value!r}>"
            )


def check_all_html() -> None:
    for path in repository_files(".html"):
        check_html(path)


def check_no_tracking_or_external_network() -> None:
    candidates = [*repository_files(".html"), *repository_files(".js")]
    patterns = {**TRACKING_PATTERNS, **NETWORK_PATTERNS}
    for path in candidates:
        text = path.read_text(encoding="utf-8")
        for name, pattern in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                fail(f"{path.relative_to(ROOT)}: prohibited runtime pattern: {name}")


def check_css() -> None:
    for path in repository_files(".css"):
        text = path.read_text(encoding="utf-8")
        if CSS_REMOTE_PATTERN.search(text):
            fail(f"{path.relative_to(ROOT)}: external CSS asset/import is not allowed")


def check_manifest() -> None:
    path = ROOT / "site.webmanifest"
    data = json.loads(path.read_text(encoding="utf-8"))
    for field in ("name", "short_name", "description", "start_url", "scope"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            fail(f"site.webmanifest: non-empty {field!r} is required")
    if data["start_url"] != "./" or data["scope"] != "./":
        fail("site.webmanifest: start_url and scope must both remain './'")
    icons = data.get("icons")
    if not isinstance(icons, list) or not icons:
        fail("site.webmanifest: at least one icon is required")
    for icon in icons:
        if not isinstance(icon, dict) or not isinstance(icon.get("src"), str):
            fail("site.webmanifest: every icon requires a string src")
        target = resolve_local_reference(path, icon["src"])
        if not target.is_file():
            fail(f"site.webmanifest: missing icon {icon['src']!r}")



def check_png_dimensions(path: Path, expected_width: int, expected_height: int) -> None:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"{path.relative_to(ROOT)}: valid PNG signature is required")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if (width, height) != (expected_width, expected_height):
        fail(
            f"{path.relative_to(ROOT)}: expected {expected_width}x{expected_height}; "
            f"found {width}x{height}"
        )


def check_distribution_metadata() -> None:
    required_meta = (
        'property="og:title"',
        'property="og:description"',
        'property="og:type"',
        'property="og:url"',
        'property="og:image"',
        'property="og:image:width" content="1200"',
        'property="og:image:height" content="630"',
        'property="og:image:alt"',
        'name="twitter:card" content="summary_large_image"',
        'name="twitter:title"',
        'name="twitter:description"',
        'name="twitter:image"',
        'type="application/atom+xml"',
    )
    for path in repository_files(".html"):
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)
        for marker in required_meta:
            if marker not in text:
                fail(f"{relative}: missing distribution metadata {marker!r}")
        match = re.search(r'property="og:image" content="([^"]+)"', text)
        if not match:
            fail(f"{relative}: og:image is required")
        image_url = match.group(1)
        expected_prefix = BASE_URL + "/"
        if not image_url.startswith(expected_prefix):
            fail(f"{relative}: og:image must use the canonical site origin")
        image_path = ROOT / image_url.removeprefix(expected_prefix)
        if not image_path.is_file():
            fail(f"{relative}: missing local social image for {image_url!r}")

    home = (ROOT / "index.html").read_text(encoding="utf-8")
    if '"@type":"WebSite"' not in home or '"@type":"Person"' not in home:
        fail("index.html: WebSite and Person JSON-LD are required")

    for relative in (
        "notes/ordivon-runtime-release/index.html",
        "notes/why-ordivon/index.html",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in (
            'property="article:published_time"',
            'property="article:modified_time"',
            'property="article:author"',
            '"@type":"Article"',
            'class="related-reading"',
        ):
            if marker not in text:
                fail(f"{relative}: missing article metadata {marker!r}")

    for name in ("default.png", "runtime.png", "finharness.png", "web.png"):
        check_png_dimensions(ROOT / "assets" / "social" / name, 1200, 630)


def check_atom_feed() -> None:
    path = ROOT / "feed.xml"
    tree = ET.parse(path)
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    root = tree.getroot()
    if root.tag != "{http://www.w3.org/2005/Atom}feed":
        fail("feed.xml: Atom feed root is required")
    self_links = [
        element.get("href")
        for element in root.findall("atom:link", namespace)
        if element.get("rel") == "self"
    ]
    if self_links != [f"{BASE_URL}/feed.xml"]:
        fail("feed.xml: canonical self link is required")
    entries = root.findall("atom:entry", namespace)
    if len(entries) != 2:
        fail(f"feed.xml: expected 2 entries; found {len(entries)}")
    expected_urls = {
        f"{BASE_URL}/notes/ordivon-runtime-release/",
        f"{BASE_URL}/notes/why-ordivon/",
    }
    actual_urls = {
        entry.find("atom:link", namespace).get("href")
        for entry in entries
        if entry.find("atom:link", namespace) is not None
    }
    if actual_urls != expected_urls:
        fail(f"feed.xml: entry links mismatch; found={sorted(actual_urls)}")

def check_sitemap() -> None:
    tree = ET.parse(ROOT / "sitemap.xml")
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = {
        element.text.strip()
        for element in tree.findall("sm:url/sm:loc", namespace)
        if element.text and element.text.strip()
    }
    expected = {
        expected_canonical(path)
        for path in repository_files(".html")
        if path.name != "404.html"
    }
    if locations != expected:
        missing = sorted(expected - locations)
        extra = sorted(locations - expected)
        fail(f"sitemap.xml mismatch; missing={missing}; extra={extra}")


def check_robots() -> None:
    text = (ROOT / "robots.txt").read_text(encoding="utf-8")
    expected = f"Sitemap: {BASE_URL}/sitemap.xml"
    if expected not in text:
        fail(f"robots.txt must contain {expected!r}")
    if re.search(r"^\s*Disallow:\s*/\s*$", text, flags=re.IGNORECASE | re.MULTILINE):
        fail("robots.txt must not disallow the entire public site")


def main() -> int:
    checks = (
        check_required_files,
        check_cname,
        check_all_html,
        check_no_tracking_or_external_network,
        check_css,
        check_manifest,
        check_distribution_metadata,
        check_atom_feed,
        check_sitemap,
        check_robots,
    )

    try:
        for check in checks:
            check()
    except (AssertionError, OSError, UnicodeError, ValueError, ET.ParseError) as exc:
        print(f"SITE CHECK FAILED: {exc}", file=sys.stderr)
        return 1

    html_count = len(repository_files(".html"))
    print(
        f"SITE CHECK PASSED: {html_count} HTML files; "
        f"CNAME={EXPECTED_CNAME}; sitemap/manifest/navigation consistent; "
        "local runtime assets only; no tracking/network patterns."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

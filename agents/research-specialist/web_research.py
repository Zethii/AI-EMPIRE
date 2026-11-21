"""Dependency-free DuckDuckGo HTML search adapter with explicit failure diagnostics."""
from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import re

SEARCH_URL = "https://html.duckduckgo.com/html/"
BLOCK_MARKERS = (
    "captcha", "anomaly-modal", "bots use duckduckgo", "unusual traffic",
    "automated requests", "verify you are human", "temporarily blocked",
)
EMPTY_MARKERS = (
    "no results found", "no results for", "did not match any results",
)


def clean(text: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", text).split())


def classify_response(page: str, parsed_count: int) -> str:
    """Classify an empty parse without treating every empty page as no demand."""
    if parsed_count:
        return "results"
    lowered = page.lower()
    if any(marker in lowered for marker in BLOCK_MARKERS):
        return "blocked"
    if any(marker in lowered for marker in EMPTY_MARKERS):
        return "empty"
    return "unrecognized"


class ResultsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self._title = None
        self._snippet = None
        self._url = ""
        self._mode = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = set(attributes.get("class", "").split())
        if tag == "a" and "result__a" in classes:
            self._title = ""
            self._url = attributes.get("href", "")
            self._mode = "title"
        elif tag in ("a", "div") and "result__snippet" in classes:
            self._snippet = ""
            self._mode = "snippet"

    def handle_data(self, data):
        if self._mode == "title" and self._title is not None:
            self._title += data
        elif self._mode == "snippet" and self._snippet is not None:
            self._snippet += data

    def handle_endtag(self, tag):
        if tag == "a" and self._mode == "title":
            title = clean(self._title or "")
            if title and self._url:
                self.items.append({
                    "title": title, "url": self._url, "snippet": ""
                })
            self._mode = None
        elif tag in ("a", "div") and self._mode == "snippet":
            snippet = clean(self._snippet or "")
            if snippet and self.items:
                self.items[-1]["snippet"] = snippet
            self._mode = None


def search(query: str, *, limit: int = 5, timeout: int = 15) -> list[dict]:
    if not query.strip():
        return []
    if limit < 1:
        raise ValueError("limit must be at least 1")

    url = SEARCH_URL + "?" + urlencode({"q": query})
    req = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; AI-EMPIRE research bot/0.1)"},
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            page = response.read(750_000).decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise RuntimeError(f"DuckDuckGo returned HTTP {exc.code}.") from None
    except (URLError, TimeoutError) as exc:
        reason = getattr(exc, "reason", exc)
        raise RuntimeError(f"DuckDuckGo request failed: {reason}") from None

    if status < 200 or status >= 300:
        raise RuntimeError(f"DuckDuckGo returned HTTP {status}.")

    parser = ResultsParser()
    parser.feed(page)
    classification = classify_response(page, len(parser.items))
    if classification == "blocked":
        raise RuntimeError(
            "DuckDuckGo returned a bot-check or blocked page; no search evidence was retrieved."
        )
    if classification == "unrecognized":
        title_match = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
        page_title = clean(title_match.group(1))[:100] if title_match else "(no title)"
        raise RuntimeError(
            "DuckDuckGo response contained no recognizable result markup "
            f"(received {len(page)} characters; page title: {page_title}). "
            "The provider markup may have changed."
        )
    # A recognized no-results page is a valid empty search, not a parser failure.
    if classification == "empty":
        return []

    valid = []
    for row in parser.items:
        link = row["url"]
        if link.startswith("//"):
            link = "https:" + link
        parsed = urlparse(link)
        if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
            target = parse_qs(parsed.query).get("uddg", [])
            if target:
                link = target[0]
        parsed = urlparse(link)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            continue
        if any(link == item["url"] for item in valid):
            continue
        row["url"] = link
        valid.append(row)
        if len(valid) >= limit:
            break
    return valid

"""Download a URL and turn it into readable plain text."""

import logging
import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.errors import FetchError

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; KnowledgeInbox/1.0)"

# Page chrome that is almost never the content the user meant to save.
_NOISE_TAGS = ["script", "style", "noscript", "svg", "nav", "header", "footer", "aside", "form", "iframe", "button"]

# Reference lists, citation markers, nav boxes etc. Wikipedia-style class names,
# but most CMSs and docs sites use similar ones.
_NOISE_SELECTORS = [
    "sup.reference", ".reflist", ".references", ".mw-references-wrap", ".mw-cite-backlink",
    ".mw-editsection", ".navbox", ".vertical-navbox", ".sidebar", ".toc", "#toc", ".hatnote",
    ".metadata", ".catlinks", ".noprint", "[role=navigation]", "[aria-hidden=true]",
]

# Elements that start a new paragraph / a new line. Everything else (a, i, b, span,
# cite, code...) is inline and must NOT break the text, or "see the [link] here"
# turns into three separate lines.
_PARAGRAPH_TAGS = [
    "p", "div", "section", "article", "main", "blockquote", "pre", "table", "ul", "ol", "dl",
    "h1", "h2", "h3", "h4", "h5", "h6", "figure", "figcaption",
]
_LINE_TAGS = ["li", "tr", "dt", "dd", "br"]

# Placeholders survive whitespace collapsing, then become real newlines.
_PARAGRAPH_MARK = ""
_LINE_MARK = ""
_MARK_RUN = re.compile(f"[\\s{_PARAGRAPH_MARK}{_LINE_MARK}]*[{_PARAGRAPH_MARK}{_LINE_MARK}][\\s{_PARAGRAPH_MARK}{_LINE_MARK}]*")


@dataclass
class FetchedPage:
    title: str | None
    text: str


async def fetch_page(url: str) -> FetchedPage:
    settings = get_settings()
    body, content_type = await _download(url, settings.fetch_timeout_seconds, settings.max_fetch_bytes)

    if "html" in content_type:
        page = extract_from_html(body)
    elif content_type.startswith("text/") or content_type == "":
        page = FetchedPage(title=None, text=_tidy(body))
    else:
        raise FetchError(f"Unsupported content type '{content_type}'. Only HTML and plain text pages can be saved.")

    if not page.text:
        raise FetchError("The page has no readable text (it may require JavaScript or a login).")

    logger.info("page fetched", extra={"url": url, "chars": len(page.text), "title": page.title})
    return page


async def _download(url: str, timeout: float, max_bytes: int) -> tuple[str, str]:
    try:
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        ) as client:
            async with client.stream("GET", url) as response:
                if response.status_code >= 400:
                    raise FetchError(f"The site responded with HTTP {response.status_code}.")

                chunks = bytearray()
                async for part in response.aiter_bytes():
                    chunks.extend(part)
                    if len(chunks) > max_bytes:
                        raise FetchError(f"The page is larger than {max_bytes // 1_000_000} MB.")

                content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
                encoding = response.encoding or "utf-8"
                return chunks.decode(encoding, errors="replace"), content_type
    except httpx.TimeoutException as exc:
        raise FetchError(f"Timed out after {timeout:.0f}s while fetching the page.") from exc
    except httpx.HTTPError as exc:
        raise FetchError(f"Could not reach the URL: {exc}") from exc


# Trailing sections that are lists of citations/links, not content.
_TRAILING_SECTIONS = re.compile(
    r"^(references|notes|citations|sources|bibliography|further reading|external links|see also)$",
    re.IGNORECASE | re.MULTILINE,
)


def extract_from_html(html: str) -> FetchedPage:
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else None

    for tag in soup(_NOISE_TAGS):
        tag.decompose()
    for tag in soup.select(", ".join(_NOISE_SELECTORS)):
        tag.decompose()

    # Prefer the main content region when the page marks one up.
    root = soup.find("article") or soup.find("main") or soup.find(attrs={"role": "main"}) or soup.body or soup

    # Mark block boundaries, then flatten. Inline tags simply concatenate.
    for tag in root.find_all(_PARAGRAPH_TAGS):
        tag.insert_before(_PARAGRAPH_MARK)
        tag.insert_after(_PARAGRAPH_MARK)
    for tag in root.find_all(_LINE_TAGS):
        # One mark per element, so "<br><br>" (two marks) can be told apart from "</li><li>" (one).
        tag.insert_before(_LINE_MARK)
    for cell in root.find_all(["td", "th"]):
        cell.insert_before(" | ")

    text =re.sub(r"\s+", " ", root.get_text())  # source-code newlines/indentation mean nothing in HTML
    text = _MARK_RUN.sub(_break_for, text)
    text = _drop_trailing_sections(_tidy(text))

    return FetchedPage(title=title or None, text=text)


def _break_for(run: re.Match) -> str:
    """A run of adjacent markers becomes ONE break: a blank line for a block boundary
    or a double <br>, otherwise a single newline (list items, table rows, one <br>)."""
    marks = run.group()
    if _PARAGRAPH_MARK in marks or marks.count(_LINE_MARK) >= 2:
        return "\n\n"
    return "\n"


def _drop_trailing_sections(text: str) -> str:
    """Cut at a 'References' / 'External links'... heading in the last part of the page."""
    for match in _TRAILING_SECTIONS.finditer(text):
        if match.start() > len(text) * 0.4:
            return text[: match.start()].rstrip()
    return text


def _tidy(text: str) -> str:
    """Collapse whitespace but keep paragraph breaks (the chunker relies on them)."""
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

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
_NOISE_TAGS = ["script", "style", "noscript", "svg", "nav", "header", "footer", "aside", "form", "iframe"]


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


def extract_from_html(html: str) -> FetchedPage:
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else None

    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    # Prefer the main content region when the page marks one up.
    root = soup.find("article") or soup.find("main") or soup.body or soup
    text = root.get_text(separator="\n")

    return FetchedPage(title=title or None, text=_tidy(text))


def _tidy(text: str) -> str:
    """Collapse whitespace but keep paragraph breaks (the chunker relies on them)."""
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

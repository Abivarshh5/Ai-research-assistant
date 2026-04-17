"""
Async web scraping tool using Playwright and BeautifulSoup.
Extracts clean, readable text from target URLs.
"""

from __future__ import annotations

import asyncio
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

async def scrape_url(url: str, timeout: int = 15000) -> str:
    """
    Scrape a single URL concurrently, extracting its meaningful text content.

    Parameters
    ----------
    url:
        The URL to scrape.
    timeout:
        Timeout in milliseconds for page load explicitly. (Default 15s)

    Returns
    -------
    str
        The cleaned text of the page. Empty if the scrape fails.
    """
    logger.info(f"Scraping URL: {url}")
    try:
        async with async_playwright() as p:
            # We use Chromium for maximum compat, headless by default
            browser = await p.chromium.launch(args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"])
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            try:
                # Wait until network is somewhat idle or DOM is loaded
                await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout while attempting to load {url}")
                await browser.close()
                return ""
            except Exception as e:
                logger.error(f"Failed to load {url}: {e}")
                await browser.close()
                return ""

            # Give a very brief moment for dynamic JS to inject essential elements
            await asyncio.sleep(1)

            html_content = await page.content()
            await browser.close()

            # Parse the text using bs4
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove noisy elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            # Get clean text
            text = soup.get_text(separator="\n")
            
            # Collapse multiple newlines/spaces
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = "\n".join(chunk for chunk in chunks if chunk)

            logger.info(f"Successfully scraped payload from {url} (length: {len(clean_text)})")
            return clean_text

    except Exception as exc:
        logger.error(f"Playwright error on {url}: {exc}")
        return ""

"""
Production-grade Multi-method Scraper Tool.
Combines Playwright (dynamic) with BeautifulSoup (fallback) for maximum reliability.
"""

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from crewai.tools import tool
from utils.config import SCRAPER_TIMEOUT

# Configuration
MAX_CONTENT_LENGTH = 5000   # Increased for richer reports

def playwright_scrape(url: str) -> dict:
    """Method 1: Dynamic scraping using Playwright."""
    result = {"content": None, "title": None, "error": None, "method": "playwright"}
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = context.new_page()
            
            # Use SCRAPER_TIMEOUT from config
            page.goto(url, timeout=SCRAPER_TIMEOUT, wait_until="domcontentloaded")
            
            result["title"] = page.title()
            result["content"] = page.content()
            browser.close()
            return result
    except PlaywrightTimeoutError:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)
    return result

def fallback_scrape(url: str) -> dict:
    """Method 2: Static fallback using requests + BS4."""
    result = {"content": None, "title": None, "error": None, "method": "fallback"}
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        result["title"] = soup.title.string if soup.title else "Unknown"
        result["content"] = response.text
        return result
    except Exception as e:
        result["error"] = str(e)
    return result

def clean_content(html: str, url: str) -> str:
    """Cleans HTML into meaningful text for LLM consumption."""
    if not html:
        return ""
        
    soup = BeautifulSoup(html, "html.parser")
    
    # Prune noise aggressively
    # Added common sidebar and ad classes/ids
    noise_selectors = [
        "script", "style", "nav", "footer", "header", "aside", "form",
        ".ads", ".sidebar", ".menu", ".nav", "#footer", "#header", "#sidebar"
    ]
    for selector in noise_selectors:
        for tag in soup.select(selector) if selector.startswith((".", "#")) else soup.find_all(selector):
            tag.decompose()
            
    # Extract structural content
    lines = []
    # Priority: article > main > content div > body
    main_area = soup.find("article") or soup.find("main") or soup.find(id="content") or soup.body
    
    if main_area:
        # Keep only paragraphs and headings to filter out list-heavy sidebars/menus
        for element in main_area.find_all(['h1', 'h2', 'h3', 'p']):
            text = element.get_text(separator=" ", strip=True)
            if len(text) > 40: # Skip fragments and short boilerplate
                lines.append(text)
    
    # If no structural elements found, just get body text but clean it
    if not lines and soup.body:
        lines = [soup.body.get_text(separator=" ", strip=True)]

    clean_text = "\n\n".join(lines)
    clean_text = clean_text[:MAX_CONTENT_LENGTH]
    
    if clean_text:
        clean_text += f"\n\n[Source: {url}]"
        
    return clean_text

def scrape_url(url: str) -> dict:
    """
    Main entry point for scraping.
    Attempts Playwright with 1 retry, then Fallback upon failure.
    """
    res = {"error": "Initial state"}
    
    # 1. Try Playwright with Retry Logic
    for attempt in range(2):
        res = playwright_scrape(url)
        if not res["error"] and res["content"]:
            break
        if attempt == 0:
            print(f"[Scraper] Playwright failed for {url}. Retrying once...")

    # 2. If Playwright failed, try Fallback
    if res["error"] or not res["content"]:
        error_reason = res["error"] or "Empty Content"
        res = fallback_scrape(url)
        res["prev_error"] = error_reason # Track why Playwright failed
        
    # 3. Clean and format the final result
    final_content = clean_content(res["content"], url)
    
    return {
        "url": url,
        "title": res["title"] or "Unknown",
        "content": final_content,
        "method": res["method"],
        "error": res["error"] if not final_content else None,
        "failure_reason": res.get("prev_error") if res["method"] == "fallback" else None
    }

@tool("Scraper Tool")
def scrape_tool(url: str) -> dict:
    """
    Extracts high-quality text content from a webpage.
    Args:
        url (str): The URL to scrape.
    """
    if isinstance(url, dict):
        url = url.get("url", "")
        
    if not url or not isinstance(url, str):
        return {"error": "Invalid URL"}
        
    return scrape_url(url)

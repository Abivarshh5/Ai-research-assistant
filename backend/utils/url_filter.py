import re
from urllib.parse import urlparse

# List of domains/keywords to de-prioritize or block from research scraping
BLOCKED_DOMAINS = [
    "youtube.com", "youtu.be",
    "reddit.com", "facebook.com", "instagram.com", "tiktok.com",
    "twitter.com", "x.com", "pinterest.com",
    "amazon.com", "ebay.com",
    "medium.com", "substack.com", "blog.", "blogspot.com"
]

# Domains that indicate high-quality research content
PREMIUM_TLDS = [".gov", ".edu", ".org"]
RESEARCH_KEYWORDS = ["researchgate.net", "scholar.google", "arxiv.org", "science.gov"]

def is_high_quality_url(url: str) -> bool:
    """
    Evaluates if a URL is likely to contain high-quality research data.
    """
    if not isinstance(url, str):
        return False
        
    parsed = urlparse(url.lower())
    domain = parsed.netloc
    
    if any(blocked in domain for blocked in BLOCKED_DOMAINS):
        return False
    
    return True

def filter_sources(urls: list) -> list:
    """
    Filters a list of URLs and returns only high-quality candidates.
    """
    return [u for u in urls if is_high_quality_url(u)]

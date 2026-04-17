from mcp_local.tool_registry import register_tool
from utils.tools.scraper_tool import scrape_url

@register_tool("Scraper Tool")
def scraper_adapter(url: str) -> dict:
    result = scrape_url(url)
    
    if result.get("error"):
        return {"error": f"ERROR: {result['error']}. SKIP THIS URL AND TRY ANOTHER."}
        
    content = result.get("content", "")
    if not content or len(content) < 100:
        return {"error": "ERROR: Content too short or missing. SKIP THIS URL AND TRY ANOTHER."}
        
    return {
        "url": result.get("url", url),
        "title": result.get("title", "Unknown"),
        "content": result.get("content"),
        "error": None
    }

from mcp_local.tool_registry import register_tool
from utils.tools.search_tool import search_serper

@register_tool("Search Tool")
def search_adapter(query: str) -> dict:
    results = search_serper(query)
    return {
        "results": results,
        "error": None if results else "ERROR: No results found. SKIP THIS SEARCH."
    }

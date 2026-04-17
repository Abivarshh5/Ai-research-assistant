from mcp_local.tool_registry import register_tool
from utils.tools.news_api_tool import news_api_tool

@register_tool("News API Tool")
def news_adapter(query: str) -> dict:
    result = news_api_tool(query)
    if result.get("error"):
        return {"error": f"ERROR: {result['error']}. SKIP THIS SOURCE."}
        
    return {
        "data": result.get("data"),
        "error": None
    }

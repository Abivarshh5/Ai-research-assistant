import os
from utils.tools.api_client import call_api

def news_api_tool(query: str) -> dict:
    """
    Fetches news articles related to a topic using a public API.
    
    Args:
        query (str): Search topic. MUST be a plain string.
    """
    endpoint = "https://newsapi.org/v2/everything"
    
    # In a real-world scenario, the API key should be in .env
    api_key = os.getenv("NEWS_API_KEY", "YOUR_API_KEY")

    params = {
        "q": query,
        "apiKey": api_key,
        "pageSize": 5
    }

    return call_api(endpoint, params)

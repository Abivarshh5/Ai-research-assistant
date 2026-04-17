import requests
import logging

logger = logging.getLogger(__name__)

def call_api(endpoint: str, params: dict) -> dict:
    """
    Generic API caller (MCP-style wrapper).
    Designed to be easily replaced by an MCP client call in the future.
    """
    try:
        logger.info(f"Calling API endpoint: {endpoint} with params: {params.keys()}")
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return {
            "data": response.json(),
            "error": None
        }
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return {
            "data": None,
            "error": str(e)
        }

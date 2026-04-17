from typing import Dict, Callable
import logging

logger = logging.getLogger(__name__)

# Registry mapping tool names to adapter functions
_REGISTRY: Dict[str, Callable] = {}

def register_tool(name: str):
    """Decorator to register a tool adapter."""
    def decorator(func: Callable):
        _REGISTRY[name] = func
        return func
    return decorator

def get_adapter(name: str) -> Callable:
    """Retrieve an adapter by its registered name."""
    adapter = _REGISTRY.get(name)
    if not adapter:
        raise ValueError(f"Tool '{name}' not found in MCP registry.")
    return adapter

def list_tools():
    """List all registered tools."""
    return list(_REGISTRY.keys())

# Import adapters to trigger registration
from mcp_local.adapters import search_adapter, scraper_adapter, news_adapter

import logging
from typing import Any, Dict
from mcp_local.tool_registry import get_adapter

logger = logging.getLogger(__name__)

def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    MCP-style tool executor.
    Standardizes tool execution and ensures a unified output format.
    """
    try:
        logger.info(f"[MCP] Executing Tool: {tool_name} with args: {kwargs}")
        
        adapter = get_adapter(tool_name)
        result = adapter(**kwargs)
        
        if not isinstance(result, dict):
             result = {"data": result, "error": None}
             
        if result.get("error"):
            logger.warning(f"[MCP] Tool '{tool_name}' returned error: {result['error']}")
        
        return result

    except Exception as e:
        error_msg = f"FATAL MCP ERROR while executing '{tool_name}': {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

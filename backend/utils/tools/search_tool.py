"""
Serper API Search Tool for the AI Research Assistant.

Provides a standalone ``search_serper`` function and a ready-to-use
CrewAI ``Tool`` instance (``serper_search_tool``) that any CrewAI agent
can include in its tool belt.

Usage (standalone)::

    from utils.tools.search_tool import search_serper
    results = search_serper("latest advances in LLM reasoning")

Usage (CrewAI agent)::

    from utils.tools.search_tool import serper_search_tool
    agent = Agent(tools=[serper_search_tool], ...)
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests
from crewai.tools import tool
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()  # loads .env from project root / cwd

logger = logging.getLogger(__name__)

_SERPER_API_URL = "https://google.serper.dev/search"
_REQUEST_TIMEOUT_SECONDS = 15
_MAX_RESULTS = 5


# ---------------------------------------------------------------------------
# Core search function
# ---------------------------------------------------------------------------


def search_serper(query: str) -> list[dict[str, str]]:
    """Call the Serper Google-search API and return structured results.

    Parameters
    ----------
    query:
        The search query string.

    Returns
    -------
    list[dict[str, str]]
        Up to ``_MAX_RESULTS`` dicts, each containing:
        - ``title``  – page title
        - ``url``    – page URL
        - ``snippet`` – short description / excerpt
        An empty list is returned when the request fails or no results
        are found.
    """
    print("[TOOL] Searching for:", query)
    
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        logger.error("SERPER_API_KEY is not set in environment variables.")
        return []

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {"q": query}

    try:
        response = requests.post(
            _SERPER_API_URL,
            json=payload,
            headers=headers,
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Serper API request timed out for query: %s", query)
        return []
    except requests.exceptions.ConnectionError:
        logger.error("Connection error reaching Serper API for query: %s", query)
        return []
    except requests.exceptions.HTTPError as exc:
        logger.error(
            "Serper API returned HTTP %s for query: %s — %s",
            exc.response.status_code if exc.response is not None else "???",
            query,
            exc,
        )
        return []
    except requests.exceptions.RequestException as exc:
        logger.error("Unexpected request error for query: %s — %s", query, exc)
        return []

    data: dict[str, Any] = response.json()
    organic: list[dict[str, Any]] = data.get("organic", [])

    results: list[dict[str, str]] = [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in organic[:_MAX_RESULTS]
    ]

    logger.info("Serper returned %d results for query: %s", len(results), query)
    return results


# ---------------------------------------------------------------------------
# CrewAI tool wrapper
# ---------------------------------------------------------------------------


@tool("Search Tool")
def search_tool(query: str) -> list[dict[str, str]]:
    """Searches the web for relevant sources using Serper API."""
    return search_serper(query)

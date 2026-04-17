"""
Research agent module using CrewAI to search and select candidate URLs.
The scraping loop is now handled deterministically by the LangGraph pipeline.
"""

import json
import logging
import os
import re
import yaml
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from mcp_local.executor import execute_tool
from utils.config import get_crew_llm

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MCP-Wrapped Tools for CrewAI
# ---------------------------------------------------------------------------

@tool("Search Tool")
def mcp_search_tool(query: str) -> str:
    """Searches the web for relevant sources."""
    res = execute_tool("Search Tool", query=query)
    return json.dumps(res)

@tool("News API Tool")
def mcp_news_tool(query: str) -> str:
    """Fetches news articles related to a topic."""
    res = execute_tool("News API Tool", query=query)
    return json.dumps(res)


def _load_config():
    """Helper to load agent and task configs."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agents_config_path = os.path.join(base_dir, 'config', 'agents.yaml')
    tasks_config_path = os.path.join(base_dir, 'config', 'tasks.yaml')
    
    with open(agents_config_path, 'r') as f:
        agents_config = yaml.safe_load(f)
    with open(tasks_config_path, 'r') as f:
        tasks_config = yaml.safe_load(f)
    return agents_config, tasks_config


def execute_search_discovery(topic: str) -> str:
    """
    Runs the Search Analyst agent to discover as many relevant URLs as possible.
    """
    agents_config, tasks_config = _load_config()
    llm = get_crew_llm()

    searcher_data = agents_config['search_analyst']
    searcher = Agent(
        role=searcher_data['role'],
        goal=searcher_data['goal'],
        backstory=searcher_data['backstory'],
        tools=[mcp_search_tool, mcp_news_tool],
        llm=llm,
        verbose=True
    )

    task_data = tasks_config['search_task']
    search_task = Task(
        description=task_data['description'].format(topic=topic),
        expected_output=task_data['expected_output'],
        agent=searcher
    )

    crew = Crew(agents=[searcher], tasks=[search_task], verbose=True)
    result = crew.kickoff()
    return result.raw if hasattr(result, 'raw') else str(result)


def select_top_urls(search_data: str) -> list:
    """
    Runs the URL Selector agent to pick the top 5 unique URLs from the raw search data.
    Returns a clean list of URL strings.
    """
    agents_config, tasks_config = _load_config()
    llm = get_crew_llm()

    selector_data = agents_config['url_selector']
    selector = Agent(
        role=selector_data['role'],
        goal=selector_data['goal'],
        backstory=selector_data['backstory'],
        llm=llm,
        verbose=True
    )

    task_data = tasks_config['selection_task']
    selection_task = Task(
        description=task_data['description'].format(search_data=search_data),
        expected_output=task_data['expected_output'],
        agent=selector
    )

    crew = Crew(agents=[selector], tasks=[selection_task], verbose=True)
    result = crew.kickoff()
    output_str = result.raw if hasattr(result, 'raw') else str(result)

    try:
        json_match = re.search(r'\[.*\]', output_str, re.DOTALL)
        if json_match:
            urls = json.loads(json_match.group(0))
            if isinstance(urls, list):
                return [str(u) for u in urls if u][:5]
    except Exception as e:
        logger.error(f"Failed to parse selected URLs: {e}")
    
    return []

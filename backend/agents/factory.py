import json
import logging
import os
import re
import yaml
from urllib.parse import urlparse
from crewai import Agent, Task, Crew
from utils.config import get_crew_llm
from mcp_local.executor import execute_tool
from crewai.tools import tool

logger = logging.getLogger(__name__)

# --- Tools for Agents ---

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

# --- Factory Helpers ---

def load_configs():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tasks_path = os.path.join(base_dir, 'tasks', 'tasks.yaml')
    agents_path = os.path.join(base_dir, 'tasks', 'agents.yaml')
    
    with open(tasks_path, 'r') as f:
        tasks = yaml.safe_load(f)
    with open(agents_path, 'r') as f:
        agents = yaml.safe_load(f)
    return tasks, agents

def run_search_agent(topic: str, include_news: bool = True) -> str:
    """
    Reasoning task: Discovers URLs for a given topic.
    """
    tasks_cfg, agents_cfg = load_configs()
    llm = get_crew_llm()
    
    tools = [mcp_search_tool]
    if include_news:
        tools.append(mcp_news_tool)
        
    agent_data = agents_cfg['search_analyst']
    searcher = Agent(
        role=agent_data['role'],
        goal=agent_data['goal'],
        backstory=agent_data['backstory'],
        tools=tools,
        llm=llm,
        verbose=True
    )
    
    task_data = tasks_cfg['search_task']
    task = Task(
        description=task_data['description'].format(topic=topic),
        expected_output=task_data['expected_output'],
        agent=searcher
    )
    
    crew = Crew(agents=[searcher], tasks=[task], verbose=True)
    result = crew.kickoff()
    return result.raw if hasattr(result, 'raw') else str(result)

def run_selector_agent(search_data: str) -> list:
    """
    Reasoning task: Selects exactly 5 URLs from raw search data.
    """
    tasks_cfg, agents_cfg = load_configs()
    llm = get_crew_llm()
    
    agent_data = agents_cfg['url_selector']
    selector = Agent(
        role=agent_data['role'],
        goal=agent_data['goal'],
        backstory=agent_data['backstory'],
        llm=llm,
        verbose=True
    )
    
    task_data = tasks_cfg['selection_task']
    task = Task(
        description=task_data['description'].format(search_data=search_data),
        expected_output=task_data['expected_output'],
        agent=selector
    )
    
    crew = Crew(agents=[selector], tasks=[task], verbose=True)
    result = crew.kickoff()
    output_str = result.raw if hasattr(result, 'raw') else str(result)
    
    try:
        json_match = re.search(r'\[.*\]', output_str, re.DOTALL)
        if json_match:
            urls = json.loads(json_match.group(0))
            if isinstance(urls, list):
                unique_urls = []
                seen_domains = set()
                for u in urls:
                    if not u: continue
                    domain = urlparse(str(u)).netloc
                    if domain not in seen_domains:
                        unique_urls.append(str(u))
                        seen_domains.add(domain)
                    if len(unique_urls) >= 5:
                        break
                return unique_urls
    except Exception as e:
        logger.error(f"Failed to parse selected URLs: {e}")
    
    return []

def run_report_agent(topic: str, sources_data: list, insights: str) -> str:
    """
    Reasoning task: Synthesizes a structured report from collected sources and aggregated insights.
    """
    tasks_cfg, agents_cfg = load_configs()
    llm = get_crew_llm()
    
    sources_list = ""
    for i, s in enumerate(sources_data):
        sources_list += f"[{i+1}] {s['url']}\n"
    
    agent_data = agents_cfg['report_writer']
    writer = Agent(
        role=agent_data['role'],
        goal=agent_data['goal'],
        backstory=agent_data['backstory'],
        llm=llm,
        verbose=True
    )
    
    task_data = tasks_cfg['report_task']
    task = Task(
        description=task_data['description'].format(topic=topic, sources=sources_list, insights=insights),
        expected_output=task_data['expected_output'],
        agent=writer
    )
    
    crew = Crew(agents=[writer], tasks=[task], verbose=True)
    result = crew.kickoff()
    return result.raw if hasattr(result, 'raw') else str(result)

def run_aggregator_agent(sources_data: list) -> str:
    """
    Reasoning task: Normalizes and extracts structured insights from sources.
    """
    tasks_cfg, agents_cfg = load_configs()
    llm = get_crew_llm()
    
    sources_text = ""
    for i, s in enumerate(sources_data):
        sources_text += f"\n[{i+1}] Source: {s['url']}\nTitle: {s['title']}\nContent: {s['content']}\n"
    
    agent_data = agents_cfg['lead_aggregator']
    aggregator = Agent(
        role=agent_data['role'],
        goal=agent_data['goal'],
        backstory=agent_data['backstory'],
        llm=llm,
        verbose=True
    )
    
    task_data = tasks_cfg['aggregation_task']
    task = Task(
        description=task_data['description'].format(sources=sources_text),
        expected_output=task_data['expected_output'],
        agent=aggregator
    )
    
    crew = Crew(agents=[aggregator], tasks=[task], verbose=True)
    result = crew.kickoff()
    return result.raw if hasattr(result, 'raw') else str(result)

def run_refinement_agent(original_report: str, feedback: str) -> str:
    """
    Reasoning task: Refines an existing report based on user feedback.
    """
    tasks_cfg, agents_cfg = load_configs()
    llm = get_crew_llm()
    
    agent_data = agents_cfg['refinement_editor']
    editor = Agent(
        role=agent_data['role'],
        goal=agent_data['goal'],
        backstory=agent_data['backstory'],
        llm=llm,
        verbose=True
    )
    
    task_data = tasks_cfg['refinement_task']
    task = Task(
        description=task_data['description'].format(report=original_report, feedback=feedback),
        expected_output=task_data['expected_output'],
        agent=editor
    )
    
    crew = Crew(agents=[editor], tasks=[task], verbose=True)
    result = crew.kickoff()
    return result.raw if hasattr(result, 'raw') else str(result)

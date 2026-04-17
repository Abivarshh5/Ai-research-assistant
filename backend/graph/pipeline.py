import logging
from langgraph.graph import StateGraph, END
from graph.state import ResearchState
from graph.nodes import (
    search_node, 
    url_selector_node, 
    scraper_node, 
    aggregator_node, 
    report_generator_node,
    refine_node,
    final_output_node as output_node
)

from utils.config import TARGET_SOURCES

logger = logging.getLogger(__name__)

def route_scraping(state: ResearchState) -> str:
    """
    Deterministic Router:
    - Stop if success_count >= TARGET_SOURCES
    - Stop if all URLs attempted
    - Otherwise continue scraping
    """
    success = state.get("success_count", 0)
    attempts = state.get("attempt_count", 0)
    urls = state.get("urls", [])
    
    if success >= TARGET_SOURCES:
        logger.info(f"🏁 [Router] Target reached: {success} successful sources.")
        return "aggregate"
    
    if attempts >= len(urls):
        logger.info(f"🏁 [Router] All URLs attempted ({attempts}).")
        return "aggregate"
    
    return "scrape"

def route_entry(state: ResearchState) -> str:
    """
    Entry Router: Directs to search for new reports or refine for feedback.
    """
    if state.get("status") == "refining":
        return "refine"
    return "search"

def build_graph():
    """
    Constructs the deterministic LangGraph pipeline.
    """
    workflow = StateGraph(ResearchState)

    # Add Nodes
    workflow.add_node("entry", lambda x: x) 
    workflow.add_node("search", search_node)
    workflow.add_node("selector", url_selector_node)
    workflow.add_node("scraper", scraper_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("report_generator", report_generator_node)
    workflow.add_node("refine", refine_node)
    workflow.add_node("output", output_node)

    # Set Entry Point with routing
    workflow.set_entry_point("entry")
    workflow.add_conditional_edges(
        "entry",
        route_entry,
        {
            "search": "search",
            "refine": "refine"
        }
    )
    
    # Linear Edges
    workflow.add_edge("search", "selector")
    workflow.add_edge("selector", "scraper")

    # Conditional Edges (Loop Control)
    workflow.add_conditional_edges(
        "scraper",
        route_scraping,
        {
            "scrape": "scraper",
            "aggregate": "aggregator"
        }
    )

    # Final Edges
    workflow.add_edge("aggregator", "report_generator")
    workflow.add_edge("report_generator", "output")
    
    # Refinement Path
    workflow.add_edge("refine", "output") # Refinement goes straight to output delivery
    
    workflow.add_edge("output", END)

    return workflow.compile()

# Exported graph instance
graph = build_graph()
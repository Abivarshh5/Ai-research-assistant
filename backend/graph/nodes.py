import logging
from typing import Dict, Any
from graph.state import ResearchState
from agents.factory import (
    run_search_agent, 
    run_selector_agent, 
    run_report_agent, 
    run_aggregator_agent
)
from agents.autogen_refiner import run_autogen_refiner, run_single_refiner
from mcp_local.executor import execute_tool
from utils.url_filter import filter_sources
from utils.config import get_llm, ENABLE_NEWS_API
from utils.notify import send_push_notification, send_email_report

logger = logging.getLogger(__name__)

def search_node(state: ResearchState) -> Dict[str, Any]:
    """
    Search Node (Agent): Performs the initial broad discovery.
    Includes a triage step to check for news relevance.
    """
    topic = state["topic"]
    logger.info(f"🔎 [Graph] Search Node: Discovering for topic: {topic}")
    
    include_news = False
    if ENABLE_NEWS_API:
        llm = get_llm()
        triage_prompt = (
            f"Topic: {topic}\n"
            "Is this topic recent, trending, or time-sensitive research? "
            "Reply with exactly 'YES' or 'NO'."
        )
        res = llm.invoke(triage_prompt)
        res_text = res.content if hasattr(res, 'content') else str(res)
        include_news = "YES" in res_text.upper()
        if include_news:
            logger.info(" [Triage] Status: Recent/Trending | News: Enabled")
        else:
            logger.info(" [Triage] Status: Stable Research | News: Disabled")

    # Retry Logic for Agent
    discovery_data = ""
    from utils.config import MAX_RETRIES
    for attempt in range(MAX_RETRIES + 1):
        try:
            discovery_data = run_search_agent(topic, include_news=include_news)
            if discovery_data: break
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"⚠️ [Search Agent] Failed. Retrying... ({e})")
            else:
                logger.error(f"❌ [Search Agent] Fatal error: {e}")

    return {
        **state,
        "include_news": include_news,
        "status": "discovery_complete",
        "collected_data": [{"raw_discovery": discovery_data}] 
    }

def url_selector_node(state: ResearchState) -> Dict[str, Any]:
    """
    URL Selector Node: Analyzes discovery data and selects best URLs.
    """
    logger.info(" [Graph] Selector Node: Ranking and selecting URLs...")
    
    raw_discovery = state["collected_data"][0].get("raw_discovery", "")
    
    # Retry Logic for Agent
    all_urls = []
    from utils.config import MAX_RETRIES
    for attempt in range(MAX_RETRIES + 1):
        try:
            all_urls = run_selector_agent(raw_discovery)
            if all_urls: break
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"⚠️ [Selector Agent] Failed. Retrying... ({e})")
            else:
                logger.error(f"❌ [Selector Agent] Fatal error: {e}")

    filtered_urls = filter_sources(all_urls)
    
    if len(filtered_urls) < len(all_urls):
        logger.info(f"🧹 [Filter] Action: Pruned | Removed: {len(all_urls) - len(filtered_urls)} low-quality URLs")
    
    return {
        **state,
        "urls": filtered_urls,
        "collected_data": [], 
        "attempt_count": 0,
        "success_count": 0,
        "status": "urls_selected"
    }

import concurrent.futures

def scraper_node(state: ResearchState) -> Dict[str, Any]:
    """
    Scraper Execution Node: Performs parallel scraping for all selected URLs.
    """
    urls = state.get("urls", [])
    new_collected_data = list(state.get("collected_data", []))
    new_success_count = state.get("success_count", 0)
    
    logger.info(f"🚀 [Graph] Scraper Node: Parallel scraping {len(urls)} URLs...")

    def scrape_single(url_info):
        idx, url = url_info
        try:
            result = execute_tool("Scraper Tool", url=url)
            return {**result, "url": url, "index": idx}
        except Exception as e:
            return {"url": url, "error": str(e), "index": idx}

    # Execute in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Use indexed URLs to maintain order if needed, though not strictly required
        results = list(executor.map(scrape_single, enumerate(urls)))

    for res in results:
        url = res.get("url")
        content = res.get("content")
        method = res.get("method", "playwright").capitalize()
        error = res.get("error")
        
        if content and not error:
            print(f"[Scraper] {url} | Method: {method} | Status: Success")
            new_collected_data.append({
                "url": url,
                "title": res.get("title", "Research Source"),
                "content": content
            })
            new_success_count += 1
        else:
            reason = error or "Empty Content"
            print(f"[Scraper] {url} | Method: {method} | Status: Failed | Reason: {reason}")

    return {
        **state,
        "collected_data": new_collected_data,
        "success_count": new_success_count,
        "attempt_count": len(urls),
        "status": "scraping"
    }

def aggregator_node(state: ResearchState) -> Dict[str, Any]:
    """
    Aggregator Node: Normalizes and extracts structured insights.
    """
    logger.info(f"📊 [Graph] Aggregator Node: Processing {len(state['collected_data'])} sources...")
    
    if not state["collected_data"]:
        return {**state, "status": "failed", "aggregated_insights": "No data collected."}

    # Retry Logic for Agent
    insights = ""
    from utils.config import MAX_RETRIES
    for attempt in range(MAX_RETRIES + 1):
        try:
            insights = run_aggregator_agent(state["collected_data"])
            if insights: break
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"⚠️ [Aggregator Agent] Failed. Retrying... ({e})")
            else:
                logger.error(f"❌ [Aggregator Agent] Fatal error: {e}")

    return {
        **state,
        "aggregated_insights": insights,
        "status": "aggregated"
    }

def report_generator_node(state: ResearchState) -> Dict[str, Any]:
    """
    Report Generator Node: Synthesize the final research report using aggregated insights.
    """
    logger.info("✍️ [Graph] Report Generator Node: Synthesizing final report...")
    
    insights = state.get("aggregated_insights", "")
    if not insights or "No data collected" in insights:
        return {
            **state,
            "report": "No valid insights were found to generate a report.",
            "status": "failed"
        }
        
    # Retry Logic for Agent
    report = ""
    from utils.config import MAX_RETRIES
    for attempt in range(MAX_RETRIES + 1):
        try:
            report = run_report_agent(state["topic"], state["collected_data"], insights)
            if report: break
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"⚠️ [Report Agent] Failed. Retrying... ({e})")
            else:
                logger.error(f"❌ [Report Agent] Fatal error: {e}")

    return {
        **state,
        "report": report,
        "status": "report_generated"
    }

def refine_node(state: ResearchState) -> Dict[str, Any]:
    """
    Refinement Node: Updates the report based on user feedback.
    """
    logger.info("⚡ [Graph] Refine Node: Refining report based on feedback...")
    
    current_report = state.get("report", "")
    feedback = state.get("user_feedback", "")
    
    # Track history
    history = state.get("report_history", [])
    if current_report:
        history.append(current_report)
    
    # Run Refinement Agent
    if len(history) <= 1:
        # First refinement turn (original report -> 2 variants)
        # run_autogen_refiner is now a generator for streaming
        final_variants = []
        for event_type, data in run_autogen_refiner(current_report, feedback):
            if event_type == "refine_done":
                # Convert the variants dict to the expected list format for the state
                variants_dict = data.get("variants", {})
                final_variants = [
                    {"type": "analytical", "content": variants_dict.get("variant_A")},
                    {"type": "applied", "content": variants_dict.get("variant_B")}
                ]
        
        return {
            **state,
            "refined_variants": final_variants,
            "report_history": history,
            "status": "refined"
        }
    else:
        # Subsequent turns (selected variant -> single update)
        # run_single_refiner is now a generator
        final_report = current_report
        for event_type, data in run_single_refiner(current_report, feedback):
            if event_type == "single_refinement_result":
                final_report = data.get("updated_report", current_report)
        
        return {
            **state,
            "report": final_report,
            "refined_variants": [],
            "report_history": history,
            "status": "refined"
        }

def final_output_node(state: ResearchState) -> Dict[str, Any]:
    """
    Final Output Node: Return the synthesized report and metadata.
    Notifications are manual-only (triggered via /deliver/push and /deliver/email).
    """
    logger.info("🏁 [Graph] Finalizing output...")
    
    return {
        **state,
        "status": "completed"
    }

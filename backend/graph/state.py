from typing import TypedDict, List, Dict, Optional

class ResearchState(TypedDict):
    topic: str
    urls: List[str]          
    attempt_count: int       
    success_count: int       
    collected_data: List[Dict] 
    final_output: List[Dict]   
    report: str
    error: Optional[str]
    status: str
    include_news: bool
    aggregated_insights: str
    refined_variants: List[Dict]
    
    # New fields for refinement and delivery
    session_id: Optional[str]
    user_feedback: Optional[str]
    report_history: List[str]
    push_enabled: bool
    email_enabled: bool
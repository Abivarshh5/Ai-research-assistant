from fastapi import APIRouter
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class FeedbackRequest(BaseModel):
    session_id: str
    feedback: str

@router.post("/")
async def submit_feedback(request: FeedbackRequest):
    """
    Endpoint to collect user feedback for refinement.
    """
    logger.info(f"Received feedback for session {request.session_id}: {request.feedback}")
    return {"status": "feedback_received"}

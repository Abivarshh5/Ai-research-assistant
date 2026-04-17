from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from graph.pipeline import graph
from services.memory import memory_store
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

class ResearchRequest(BaseModel):
    topic: str
    push_enabled: bool = True
    email_enabled: bool = True

class RefineRequest(BaseModel):
    session_id: str
    feedback: str

from fastapi.responses import StreamingResponse
import json

@router.post("/run")
async def run_research(request: ResearchRequest):
    """
    Endpoint to trigger the deterministic research pipeline.
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Received research request for topic: {request.topic} (Session: {session_id})")
    
    initial_state = {
        "topic": request.topic,
        "urls": [],
        "attempt_count": 0,
        "success_count": 0,
        "collected_data": [],
        "final_output": [],
        "status": "starting",
        "session_id": session_id,
        "report_history": [],
        "push_enabled": request.push_enabled,
        "email_enabled": request.email_enabled
    }
    
    try:
        final_state = graph.invoke(initial_state)
        
        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])
            
        memory_store.save_session(session_id, final_state)
        
        return {
            "session_id": session_id,
            "topic": final_state["topic"],
            "status": final_state["status"],
            "report": final_state.get("report", ""),
            "results": final_state.get("final_output", [])
        }
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
def stream_research(request: ResearchRequest):
    """
    Endpoint to trigger the pipeline and stream status updates to the client via SSE.
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Received streaming research request for topic: {request.topic} (Session: {session_id})")
    
    initial_state = {
        "topic": request.topic,
        "urls": [],
        "attempt_count": 0,
        "success_count": 0,
        "collected_data": [],
        "final_output": [],
        "status": "starting",
        "session_id": session_id,
        "report_history": [],
        "push_enabled": request.push_enabled,
        "email_enabled": request.email_enabled
    }
    
    def event_generator():
        # Yield the initial 'starting' status immediately
        yield f"data: {json.dumps({'status': 'starting'})}\n\n"
        
        try:
            for s in graph.stream(initial_state):
                node_name = list(s.keys())[0]
                current_state = s[node_name]
                status = current_state.get("status", "")
                
                # yield status update
                yield f"data: {json.dumps({'status': status})}\n\n"
                
                # If we've hit the final output node, save it to memory and send the final payload
                if node_name == "output":
                    memory_store.save_session(session_id, current_state)
                    final_payload = {
                        "type": "final",
                        "session_id": session_id,
                        "report": current_state.get("report", "")
                    }
                    yield f"data: {json.dumps(final_payload)}\n\n"
                    break
        except Exception as e:
            logger.error(f"Pipeline streaming failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/refine")
async def refine_report(request: RefineRequest):
    """
    Streaming endpoint to refine an existing report based on user feedback.
    """
    logger.info(f"Received refinement request for session: {request.session_id}")
    
    # Retrieve previous state
    state = memory_store.get_session(request.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    
    previous_report = state.get("report", "")
    feedback = request.feedback

    def event_generator():
        from agents.autogen_refiner import run_autogen_refiner, run_single_refiner
        
        # Determine refinement mode
        history = state.get("report_history", [])
        is_first_refinement = len(history) == 0
        
        status_msg = "Refining report based on user feedback..." if is_first_refinement else "Refining selected report..."
        yield f"data: {json.dumps({'type': 'refine_start', 'message': status_msg})}\n\n"

        try:
            if is_first_refinement:
                # Turn 1: original report -> 2 variants
                for event_type, data in run_autogen_refiner(previous_report, feedback):
                    if event_type == "refine_done":
                        # Update state in memory
                        state["user_feedback"] = feedback
                        state["report_history"] = history + [previous_report]
                        
                        variants_dict = data.get("variants", {})
                        state["refined_variants"] = [
                            {"type": "analytical", "content": variants_dict.get("variant_A")},
                            {"type": "applied", "content": variants_dict.get("variant_B")}
                        ]
                        state["status"] = "refined"
                        memory_store.save_session(request.session_id, state)
                        yield f"data: {json.dumps({'type': 'refine_done', 'data': data})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': event_type, **(data if isinstance(data, dict) else {'message': data})})}\n\n"
            else:
                # Turn 2+: selected variant -> single update
                for event_type, data in run_single_refiner(previous_report, feedback):
                    if event_type == "single_refinement_result":
                        # Update state in memory
                        state["user_feedback"] = feedback
                        state["report"] = data.get("updated_report")
                        state["report_history"] = history + [previous_report]
                        state["status"] = "refined"
                        memory_store.save_session(request.session_id, state)
                        yield f"data: {json.dumps({'type': 'single_refinement_result', 'data': data})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': event_type, **(data if isinstance(data, dict) else {'message': data})})}\n\n"

        except Exception as e:
            logger.error(f"Streaming refinement failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

class SelectVariantRequest(BaseModel):
    session_id: str
    selected_report: str

@router.post("/select_variant")
async def select_variant(request: SelectVariantRequest):
    logger.info(f"Received variant selection for session: {request.session_id}")
    state = memory_store.get_session(request.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    state["report"] = request.selected_report
    memory_store.save_session(request.session_id, state)
    
    return {"status": "success", "message": "Report updated."}

class DeliverRequest(BaseModel):
    session_id: str
    recipient_email: str = None

from utils.notify import send_push_notification, send_email_report

@router.post("/deliver/push")
async def deliver_push(request: DeliverRequest):
    state = memory_store.get_session(request.session_id)
    if not state or not state.get("report"):
        raise HTTPException(status_code=404, detail="Report not found.")
    success = send_push_notification(f"Research Report Ready: {state['topic']}")
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send push notification.")
    return {"status": "success"}

@router.post("/deliver/email")
async def deliver_email(request: DeliverRequest):
    state = memory_store.get_session(request.session_id)
    if not state or not state.get("report"):
        raise HTTPException(status_code=404, detail="Report not found.")
    success = send_email_report(state['topic'], state['report'], recipient_email=request.recipient_email)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email.")
    return {"status": "success"}

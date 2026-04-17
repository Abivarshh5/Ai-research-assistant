import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.research import router as research_router
from api.feedback import router as feedback_router
from api.ws import router as ws_router
import logging
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env', override=True)
logger = logging.getLogger(__name__)
logger.info(f"API Key loaded (prefix): {os.getenv('OPENAI_API_KEY')[:12]}...")
logging.getLogger("crewai").setLevel(logging.WARNING)
logging.getLogger("opentelemetry").setLevel(logging.WARNING)

app = FastAPI(
    title="Research Agent API",
    description="AI-powered research pipeline with LangGraph orchestration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router, prefix="/api", tags=["research"])
app.include_router(feedback_router, prefix="/api", tags=["feedback"])
app.include_router(ws_router, tags=["websocket"])


@app.get("/health")
async def health():
    return {"status": "ok"}
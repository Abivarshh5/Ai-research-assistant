import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from crewai import LLM as CrewLLM

from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent / '.env', override=True)

logger = logging.getLogger(__name__)

# --- Research Pipeline Constants ---
MAX_URLS = int(os.getenv("MAX_URLS", 15))
TARGET_SOURCES = int(os.getenv("TARGET_SOURCES", 3))
SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", 60000)) 
ENABLE_NEWS_API = os.getenv("ENABLE_NEWS_API", "true").lower() == "true"
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 1))

# --- Notification Config ---
ENABLE_NOTIFICATIONS = os.getenv("ENABLE_NOTIFICATIONS", "false").lower() == "true"
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER")  
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_TOKEN")  
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# --- LLM Provider ---
def get_model_provider() -> str:
    """Returns the configured model provider (openai or ollama)."""
    return os.getenv("MODEL_PROVIDER", "openai").lower()

def get_llm():
    """Returns a LangChain LLM instance."""
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2)

def get_crew_llm() -> CrewLLM:
    """Returns a CrewAI LLM instance."""
    provider = get_model_provider()
    if provider == "openai":
        return CrewLLM(
            model=f"openai/{os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.2
        )
    else:
        # Fallback to Ollama if explicitly requested
        return CrewLLM(
            model=f"ollama/{os.getenv('OLLAMA_MODEL', 'llama3')}",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.2
        )

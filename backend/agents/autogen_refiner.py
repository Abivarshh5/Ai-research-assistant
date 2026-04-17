import os
import autogen
import logging
from utils.config import get_model_provider

logger = logging.getLogger(__name__)

def get_autogen_llm_config():
    """
    Returns AutoGen-compatible LLM config.
    AutoGen uses the OpenAI API format, so for Ollama we must point
    to its OpenAI-compatible endpoint at /v1.
    """
    provider = get_model_provider()

    if provider == "openai":
        return {
            "config_list": [
                {
                    "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    "api_key": os.getenv("OPENAI_API_KEY", ""),
                }
            ],
            "temperature": 0,
            "top_p": 1,
        }
    else:
        ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
       
        if not ollama_base.rstrip("/").endswith("/v1"):
            ollama_base = ollama_base.rstrip("/") + "/v1"

        return {
            "config_list": [
                {
                    "model": os.getenv("OLLAMA_MODEL", "llama3"),
                    "base_url": ollama_base,
                    "api_key": "ollama", 
                }
            ],
            "temperature": 0,
            "top_p": 1,
        }

def clean_report_content(content: str) -> str:
    """
    Strips common LLM meta-commentary/intro text from the start of the report.
    More conservative approach to ensure no real content is lost.
    """
    if not content:
        return ""
    
    lines = content.strip().split("\n")
    cleaned_lines = []
    found_content = False
    
    meta_prefixes = [
        "here is the", "certainly", "as requested", "i have", 
        "updated report", "revised report", "this version"
    ]
    
    for line in lines:
        s_line = line.strip()
        lower_line = s_line.lower()
        
        if not found_content:
            if s_line.startswith("#") or s_line.startswith("*") or s_line.startswith("-") or (s_line and s_line[0].isdigit() and "." in s_line[:4]):
                found_content = True
            
            if not s_line:
                continue
                
            is_meta = any(lower_line.startswith(prefix) for prefix in meta_prefixes)
            if is_meta and len(s_line) < 100 and not found_content:
                continue
            
            found_content = True
            
        cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines).strip()

def run_single_refiner(selected_report: str, feedback: str):
    """
    Refines a SINGLE selected report based on new user feedback.
    Yields tuple: (event_type, message_or_data)
    """
    if not selected_report:
        yield "error", "No selected report provided."
        return

    if not feedback:
        yield "done", {"previous_report": selected_report, "updated_report": selected_report}
        return

    yield "refine_start", "Refining selected report based on iterative feedback..."

    try:
        llm_config = get_autogen_llm_config()
        
        user_proxy = autogen.UserProxyAgent(
            name="UserProxyAgent", human_input_mode="NEVER", code_execution_config=False
        )

        assistant = autogen.AssistantAgent(
            name="AssistantAgent",
            system_message=(
                "You are an AI Research Refinement Engine.\n\n"
                "CRITICAL: YOUR OUTPUT MUST BE THE COMPLETE REPORT.\n"
                "1. Treat the SELECTED report as the ONLY source of truth.\n"
                "2. Apply feedback across ALL relevant sections.\n"
                "3. DO NOT OMIT ANY SECTIONS. Every heading from the original must remain.\n"
                "4. NO INTRO TEXT. NO 'Here is the report'. NO labels.\n"
                "5. NO meta-commentary."
            ),
            llm_config=llm_config,
        )

        prompt = (
            f"SELECTED REPORT (PREVIOUS VERSION):\n{selected_report}\n\n"
            f"USER FEEDBACK:\n{feedback}\n\n"
            "### TASK: Refine the entire report. Preserve ALL sections. Start with Section 1."
        )

        chat_result = user_proxy.initiate_chat(
            assistant,
            message=prompt,
            max_turns=2,
            summary_method="last_msg"
        )
        
        updated_report = selected_report
        if chat_result and chat_result.chat_history:
            content = chat_result.chat_history[-1].get("content", "")
            if content and content.strip():
                updated_report = clean_report_content(content)
        
        yield "single_refinement_result", {
            "previous_report": selected_report,
            "updated_report": updated_report
        }

    except Exception as e:
        logger.error(f"[AutoGen] Single variant refinement failed: {e}", exc_info=True)
        yield "error", f"Refinement failed: {str(e)}"

def run_autogen_refiner(original_report: str, feedback: str):
    """
    Refines an existing report based on user feedback.
    Yields tuple: (event_type, message_or_data)
    """
    if not original_report:
        yield "error", "No original report provided."
        return

    if not feedback:
        yield "done", [{"type": "original", "content": original_report}]
        return

    yield "refine_start", "Refining report based on user feedback..."

    variants = {}
    variant_specs = [
        {
            "id": "A",
            "type": "analytical",
            "name": "Analytical / Conceptual",
            "prompt_instructions": (
                "- Focus on definitions and internal mechanisms\n"
                "- Use precise, technical, formal language\n"
                "- Explain how concepts work\n"
                "- Keep examples minimal"
            )
        },
        {
            "id": "B",
            "type": "applied",
            "name": "Applied / Practical",
            "prompt_instructions": (
                "- Focus on real-world usage and applications\n"
                "- Use intuitive and explanatory language\n"
                "- Include examples and use-cases\n"
                "- Explain how concepts are used"
            )
        }
    ]

    try:
        llm_config = get_autogen_llm_config()
        
        for spec in variant_specs:
            yield "refine_progress", {
                "variant": spec["id"],
                "message": f"Generating response {spec['id']} ({spec['name']})..."
            }

            user_proxy = autogen.UserProxyAgent(
                name="UserProxyAgent",
                human_input_mode="NEVER",
                code_execution_config=False,
            )

            assistant = autogen.AssistantAgent(
                name="AssistantAgent",
                system_message=(
                    "You are a Senior Research Editor.\n\n"
                    "CRITICAL: YOUR OUTPUT MUST BE THE COMPLETE REPORT.\n"
                    "1. Apply feedback COMPLETELY to the entire report.\n"
                    "2. Preserve EXACT section headings and structure. DO NOT OMIT SECTIONS.\n"
                    "3. Ensure both variants differ in explanation style, NOT structure.\n"
                    "4. NO INTRO TEXT. NO meta-commentary. NO labels.\n\n"
                    f"Variant {spec['id']}: {spec['name'].upper()}\n"
                    f"{spec['prompt_instructions']}"
                ),
                llm_config=llm_config,
            )

            prompt = (
                f"PREVIOUS REPORT:\n{original_report}\n\n"
                f"USER FEEDBACK:\n{feedback}\n\n"
                f"VARIANT TYPE: {spec['name']}. DO NOT OMIT ANY SECTIONS. Preserve structure exactly."
            )

            chat_result = user_proxy.initiate_chat(
                assistant,
                message=prompt,
                max_turns=2,
                summary_method="last_msg"
            )
            
            refined = original_report
            if chat_result and chat_result.chat_history:
                content = chat_result.chat_history[-1].get("content", "")
                if content and content.strip():
                    refined = clean_report_content(content)
            
            variants[f"variant_{spec['id']}"] = refined

        yield "refine_done", {
            "previous_report": original_report,
            "variants": variants
        }

    except Exception as e:
        logger.error(f"[AutoGen] Refinement failed: {e}", exc_info=True)
        yield "error", f"Refinement failed: {str(e)}"

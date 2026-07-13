import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from pie.config import settings

logger = logging.getLogger("wellmate_pie_llm")

def generate_llm_rationales_and_advice(
    twin_state: Dict[str, float], 
    user_context: Dict[str, Any], 
    missions: List[Dict[str, Any]],
    feared_subjects: List[str] = None,
    upcoming_exams: List[Dict[str, Any]] = None,
    programming_issues: List[str] = None,
    daily_screen_time_hours: float = None,
    sleep_bedtime_target: str = None
) -> Optional[Dict[str, Any]]:
    """
    Calls the big wellness model API (via GitHub Models endpoint) to generate 
    highly tailored, empathetic rationales for the recommended missions,
    rewrite missions with personalized details, and generate custom coach advice.
    """
    token = settings.GITHUB_TOKEN or os.getenv("GITHUB_TOKEN", None)
    if not token:
        logger.info("GITHUB_TOKEN not configured. Skipping LLM generation, falling back to heuristic templates.")
        return None
        
    url = "https://models.inference.ai.azure.com/chat/completions"
    
    # Format current state details
    state_desc = "\n".join([f"- {k.capitalize()}: {v:.2f}" for k, v in twin_state.items()])
    
    # Format context details
    ctx_desc = f"- Weekend: {'Yes' if user_context.get('is_weekend') else 'No'}\n" \
               f"- Screen Time Index: {user_context.get('screen_time_index', 0.5):.2f}\n" \
               f"- Steps relative to target: {user_context.get('steps_ratio', 1.0):.2f}\n" \
               f"- Calendar Availability: {user_context.get('calendar_availability', 0.6):.2f}"
               
    # Format academic & lifestyle cues
    academic_cues = ""
    if feared_subjects:
        academic_cues += f"- Feared Subjects (struggled with for last 7 days): {', '.join(feared_subjects)}\n"
    if upcoming_exams:
        exams_str = ", ".join([f"{e.get('subject')} on {e.get('date')}" for e in upcoming_exams])
        academic_cues += f"- Upcoming Exams: {exams_str}\n"
    if programming_issues:
        academic_cues += f"- Programming Blocks: {', '.join(programming_issues)}\n"
    if daily_screen_time_hours is not None:
        academic_cues += f"- Daily Screen Time: {daily_screen_time_hours} hours\n"
    if sleep_bedtime_target:
        academic_cues += f"- Sleep Bedtime Target: {sleep_bedtime_target}\n"

    # Format mission options
    missions_desc = ""
    for i, m in enumerate(missions):
        missions_desc += f"\n{i+1}. ID: '{m['mission_id']}' | Title: '{m['title']}' | Description: '{m['description']}'"
        
    prompt = (
        "You are WellMate, an empathetic and highly qualified academic wellness coach. "
        "Analyze the following student digital twin state, context, and custom academic/lifestyle parameters:\n\n"
        f"[STUDENT DIGITAL TWIN STATE]\n{state_desc}\n\n"
        f"[ENVIRONMENTAL & USER CONTEXT]\n{ctx_desc}\n\n"
        f"[STUDENT ACADEMIC & LIFESTYLE CUES]\n{academic_cues}\n\n"
        f"We have selected {len(missions)} wellness recovery missions for them:\n"
        f"{missions_desc}\n\n"
        "YOUR TASK:\n"
        "1. Write a single, highly personalized, and constructive rationale sentence for each mission explaining "
        "how it directly addresses their current state (e.g., 'Recommended to help you prepare for your upcoming Operating Systems exam and lower stress').\n"
        "2. Customize the TITLE and DESCRIPTION of each mission on the fly. Inject their specific feared subjects, upcoming exams, "
        "programming issues, target bedtimes, or screen time. For example:\n"
        "   - Instead of a generic 'Pomodoro Focus', rewrite it to focus on studying their feared subject or debugging their programming issue.\n"
        "   - Instead of generic 'App Timer Setup', write it specifically targeting their actual daily screen time hours.\n"
        "   - Instead of generic 'Bedtime Anchor', write it specifically targeting their bedtime target (e.g., 'Wind down by 11:00 PM').\n"
        "3. Write a highly personalized general advice report (3 sentences max) that is realistic and related to student well-being. "
        "For example:\n"
        "   - If they are less social (low social score), remind them to call a friend.\n"
        "   - Tell them specifically how many hours they need to study their feared subject (e.g., 'Study Operating Systems at least 2 hours today').\n"
        "   - Tell them to sleep early (by their target bedtime) and establish a digital curfew to limit screen usage.\n\n"
        "Return your response ONLY as a valid, parsable JSON payload matching this schema (do NOT use markdown wraps like ```json):\n"
        "{\n"
        "  \"rationales\": {\n"
        "    \"mission_id_1\": \"Rationale sentence...\",\n"
        "    \"mission_id_2\": \"Rationale sentence...\"\n"
        "  },\n"
        "  \"customized_missions\": {\n"
        "    \"mission_id_1\": {\n"
        "      \"title\": \"Custom Personalized Title...\",\n"
        "      \"description\": \"Custom Personalized Description...\"\n"
        "    },\n"
        "    \"mission_id_2\": {\n"
        "      \"title\": \"Custom Personalized Title...\",\n"
        "      \"description\": \"Custom Personalized Description...\"\n"
        "    }\n"
        "  },\n"
        "  \"advice\": \"General encouraging, realistic advice report...\"\n"
        "}"
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1200
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5.0) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            content_text = res_body["choices"][0]["message"]["content"].strip()
            
            # Clean up potential markdown wrappers
            if content_text.startswith("```"):
                lines = content_text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                content_text = "\n".join(lines).strip()
                
            data = json.loads(content_text)
            logger.info("Successfully fetched personalized wellness advice and customized missions from LLM model.")
            return data
    except Exception as e:
        logger.warning(f"Failed to generate LLM advice/rationales: {e}. Falling back to default heuristics.")
        return None

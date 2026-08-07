import os
import json
import logging
from typing import Dict, List, Any, Optional
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

# System Prompt Template
SYSTEM_PROMPT_TEMPLATE = """You are an expert AI Technical Interviewer conducting a personalized technical interview for a graduate of a 31-day AI engineering cohort.

CANDIDATE PROFILE:
- Name: {candidate_name}
- Job Role: {candidate_role}
- Experience: {candidate_years_experience} years
- Education: {candidate_education}

PERSONALIZED INTERVIEW PLAN:
{plan_details}

PROGRESS:
- Total questions asked so far: {questions_asked}
- Distinct days covered so far: {days_covered_list}
- Minimum Requirements: Ask at least 8 questions, covering at least 4 distinct days from the plan.

INSTRUCTIONS:
1. Conduct the interview conversationally. Be encouraging but rigorous, like a real senior interviewer.
2. Ask exactly ONE question at a time.
3. Keep track of the current topic/day you are testing.
4. Follow up on vague, incorrect, or interesting answers (up to 2-3 turns per day if needed to probe real understanding) before moving to the next day.
5. Only end the interview (set "done" to true) when:
   - You have asked at least 8 questions.
   - You have covered at least 4 distinct days from the plan.
6. When concluding the interview (done is true):
   - Set the "reply" to a friendly concluding message.
   - Populate the "feedback" JSON object with:
     - "summary": A concise high-level evaluation of their performance.
     - "strengths": A list of at least 2 concrete strengths demonstrated in the interview.
     - "gaps": A list of at least 2 concrete gaps/weaknesses identified.
     - "next": A list of at least 2 concrete recommended next steps/actions.
7. If the minimum requirements are not met, "done" MUST be false, and "feedback" MUST be null.

RESPONSE FORMAT:
You MUST respond with a single JSON object (no markdown formatting, no leading/trailing prose).
The schema is:
{{
  "reply": "Your question or final message to the candidate.",
  "done": false,
  "focus_day": 7, // The day number from the plan this turn focuses on. If it's a follow-up, use the same day. If it's a general intro/outro, use null.
  "feedback": null // Or the feedback object if done is true
}}
"""

def extract_json(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from the raw text response, handling markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```json") or lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)

async def call_llm(
    candidate: Dict[str, Any],
    plan: List[Dict[str, Any]],
    questions_asked: int,
    days_covered: List[int],
    history: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Call the Claude Fable 5 model to get the next interview turn.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY environment variable is not set. Falling back to Mock LLM response.")
        day_idx = len(days_covered) % len(plan) if plan else 0
        current_day = plan[day_idx]["day"] if plan else None
        
        if questions_asked < 7:
            return {
                "reply": f"Mock question about Day {current_day}: Can you explain the core concepts and tools you used for this curriculum day?",
                "done": False,
                "focus_day": current_day,
                "feedback": None
            }
        else:
            return {
                "reply": "Thank you for the conversation. We have completed the interview.",
                "done": True,
                "focus_day": None,
                "feedback": {
                    "summary": "Completed the technical interview across multiple curriculum topics.",
                    "strengths": [
                        "Demonstrated familiarity with cohort tools and objectives.",
                        "Good conceptual understanding of embeddings and database query mechanics."
                    ],
                    "gaps": [
                        "Requires further exploration of LoRA fine-tuning hyperparameters.",
                        "Deployment practices could be expanded with cloud configurations."
                    ],
                    "next": [
                        "Build more end-to-end multi-agent pipelines.",
                        "Practice deploying applications using custom Docker networks."
                    ]
                }
            }

    # Formulate plan details for prompt
    plan_details_list = []
    for item in plan:
        plan_details_list.append(
            f"- Day {item['day']} ({item['type'].upper()}): {item['title']}\n"
            f"  Reason: {item['reason']}\n"
            f"  Tools: {', '.join(item['tools'])}\n"
            f"  Objectives:\n  " + "\n  ".join([f"* {obj}" for obj in item['objectives']])
        )
    plan_details = "\n".join(plan_details_list)

    # Format the system prompt
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        candidate_name=candidate.get("member", {}).get("name", "Candidate"),
        candidate_role=candidate.get("member", {}).get("jobRole", "Software Engineer"),
        candidate_years_experience=candidate.get("member", {}).get("yearsExperience", 0),
        candidate_education=candidate.get("member", {}).get("education", "CS Graduate"),
        plan_details=plan_details,
        questions_asked=questions_asked,
        days_covered_list=", ".join([f"Day {d}" for d in days_covered]) if days_covered else "None yet",
    )

    # Format messages for Anthropic API
    anthropic_messages = []
    for msg in history:
        # Map user/assistant to Anthropic roles
        role = "user" if msg["role"] == "user" else "assistant"
        anthropic_messages.append({"role": role, "content": msg["content"]})

    # If the history is empty, add a starting prompt to kick off the conversation
    if not anthropic_messages:
        # In Anthropic API, the conversation must start with a user message or we can just send a system instruction
        # to ask the first question. Since we need to get the first reply, we can either pass an empty list of messages
        # and rely on the model or supply a user message representing the candidate starting the interview.
        # Let's supply a virtual candidate prompt: "Hi, I am ready to start the interview."
        anthropic_messages.append({"role": "user", "content": "Hi, I am ready to start the interview."})

    client = AsyncAnthropic(api_key=api_key)

    try:
        response = await client.messages.create(
            model="claude-fable-5",
            max_tokens=4000,
            system=system_prompt,
            messages=anthropic_messages,
            temperature=0.7
        )
        
        raw_content = response.content[0].text
        logger.info(f"Raw LLM response: {raw_content}")
        
        parsed_response = extract_json(raw_content)
        return parsed_response
        
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        # Return a fallback JSON response on error
        return {
            "reply": "I'm sorry, I encountered a technical issue. Let's continue. Can you tell me more about your recent project?",
            "done": False,
            "focus_day": None,
            "feedback": None
        }

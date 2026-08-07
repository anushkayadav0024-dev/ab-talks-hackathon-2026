import os
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app.plan_builder import load_data, build_plan_for_candidate, get_candidate_by_id
from app.session import session_manager
from app.llm import call_llm

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Interview Agent Backend")

# Request Model
class InterviewRequest(BaseModel):
    sessionId: str
    candidate: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

# Response Model
class FeedbackModel(BaseModel):
    summary: str
    strengths: List[str]
    gaps: List[str]
    next: List[str]

class InterviewResponse(BaseModel):
    reply: str
    done: bool
    feedback: Optional[FeedbackModel] = None

# Cache curriculum data on startup
CURRICULUM_DATA = None

@app.on_event("startup")
async def startup_event():
    global CURRICULUM_DATA
    try:
        _, CURRICULUM_DATA = load_data()
        logger.info("Curriculum data successfully loaded on startup.")
    except Exception as e:
        logger.error(f"Failed to load curriculum data on startup: {e}")

@app.post("/api/interview", response_model=InterviewResponse)
async def interview_endpoint(req: InterviewRequest):
    global CURRICULUM_DATA
    if CURRICULUM_DATA is None:
        try:
            _, CURRICULUM_DATA = load_data()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Curriculum data not loaded: {str(e)}"
            )

    session_id = req.sessionId
    session = session_manager.get_session(session_id)

    # 1. Start Session
    if session is None:
        if req.candidate is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session does not exist. Provide 'candidate' to start a new interview."
            )
        
        # Load candidate profiles to resolve candidate details
        try:
            candidates_data, _ = load_data()
        except Exception as e:
            logger.error(f"Failed to load candidate profiles: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load candidate data: {str(e)}"
            )

        candidate_id = req.candidate.get("candidateId") or req.candidate.get("id") or req.candidate.get("member", {}).get("id")
        full_candidate = None
        if candidate_id:
            full_candidate = get_candidate_by_id(candidates_data, candidate_id)

        if not full_candidate:
            if "missions" in req.candidate:
                full_candidate = req.candidate
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Candidate with ID '{candidate_id}' not found in candidates.json, and no missions data provided."
                )

        # Build candidate's personalized plan
        plan = build_plan_for_candidate(full_candidate, CURRICULUM_DATA)
        session = session_manager.create_session(session_id, full_candidate, plan)
        logger.info(f"Created new interview session {session_id} with {len(plan)} days in plan.")

        # If a starting message is supplied, record it in the history
        if req.message:
            session.history.append({"role": "user", "content": req.message})

        # Call LLM to generate the personalized opening question
        try:
            llm_res = await call_llm(
                candidate=session.candidate,
                plan=session.plan,
                questions_asked=session.questions_asked,
                days_covered=list(session.days_covered),
                history=session.history
            )
        except Exception as e:
            logger.error(f"Error calling LLM during start session: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LLM call failed: {str(e)}"
            )

        reply = llm_res.get("reply", "Welcome to your technical interview. Let's get started.")
        focus_day = llm_res.get("focus_day")
        
        # Record turn in state
        session.questions_asked += 1
        if focus_day is not None:
            session.days_covered.add(focus_day)
            
        session.history.append({"role": "assistant", "content": reply})

        return InterviewResponse(
            reply=reply,
            done=False,
            feedback=None
        )

    # 2. Conversation Turn
    else:
        if req.message is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview session is active. Provide 'message' to continue the turn."
            )
            
        if session.completed:
            # Session is already completed, return cached feedback
            return InterviewResponse(
                reply=session.history[-1]["content"] if session.history else "Interview completed.",
                done=True,
                feedback=FeedbackModel(**session.feedback) if session.feedback else None
            )

        # Record candidate response
        session.history.append({"role": "user", "content": req.message})

        # Loop to handle early-completion guardrails
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            # Call LLM for the next turn
            llm_res = await call_llm(
                candidate=session.candidate,
                plan=session.plan,
                questions_asked=session.questions_asked,
                days_covered=list(session.days_covered),
                history=session.history
            )

            reply = llm_res.get("reply", "Could you elaborate on that?")
            done = llm_res.get("done", False)
            focus_day = llm_res.get("focus_day")
            feedback = llm_res.get("feedback")

            # Check if LLM is attempting to complete
            if done:
                # Validate minimum requirements: 8 questions and 4 days
                if session.questions_asked >= 8 and len(session.days_covered) >= 4:
                    # Requirements met, finalize session
                    session.completed = True
                    # Validate feedback format
                    if not feedback:
                        feedback = {
                            "summary": "Completed the technical interview across multiple curriculum topics.",
                            "strengths": ["Demonstrated basic familiarity with AI cohort topics.", "Completed all 8 turns of the interview."],
                            "gaps": ["Further validation needed on specific deep dive areas.", "Response structure could be more detailed."],
                            "next": ["Practice whiteboarding architecture diagrams.", "Build more hands-on production pipelines."]
                        }
                    
                    # Ensure lists have >= 2 items
                    for list_field in ["strengths", "gaps", "next"]:
                        if len(feedback.get(list_field, [])) < 2:
                            feedback[list_field] = feedback.get(list_field, []) + ["Core objective understanding", "Continuous learning and building"]
                            
                    session.feedback = feedback
                    session.history.append({"role": "assistant", "content": reply})
                    
                    return InterviewResponse(
                        reply=reply,
                        done=True,
                        feedback=FeedbackModel(**feedback)
                    )
                else:
                    # Early termination denied. Re-prompt LLM by sending a system instruction as user turn.
                    logger.warning(
                        f"LLM tried to end interview early. Questions asked: {session.questions_asked}, "
                        f"Days covered: {len(session.days_covered)}. Forcing continuation."
                    )
                    # Add instruction back into history so LLM knows it must keep going
                    session.history.append({
                        "role": "user",
                        "content": (
                            "[SYSTEM REMINDER] You cannot end the interview yet. You must ask at least 8 questions "
                            "and cover at least 4 distinct curriculum days. Please ask a new question about one of "
                            "the remaining days or follow up on my previous answer."
                        )
                    })
                    # Loop will call LLM again with the updated history containing the system instruction
                    continue
            else:
                # LLM is continuing the interview
                session.questions_asked += 1
                if focus_day is not None:
                    session.days_covered.add(focus_day)
                    
                session.history.append({"role": "assistant", "content": reply})
                
                return InterviewResponse(
                    reply=reply,
                    done=False,
                    feedback=None
                )
        
        # If we broke the loop or hit max attempts, force a standard follow-up question
        session.questions_asked += 1
        fallback_reply = "Thank you. Let's move to another area: can you tell me about your capstone project experience?"
        session.history.append({"role": "assistant", "content": fallback_reply})
        return InterviewResponse(
            reply=fallback_reply,
            done=False,
            feedback=None
        )

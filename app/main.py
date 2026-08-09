import os
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app.plan_builder import load_data, build_plan_for_candidate, get_candidate_by_id
from app.session import session_manager
from app.llm import call_llm

# Load env variables on boot
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Interview Agent Backend")

frontend_url = os.environ.get("FRONTEND_URL")
frontend_port = os.environ.get("FRONTEND_PORT", "5173")
allowed_origins = [
    f"http://localhost:{frontend_port}",
    f"http://127.0.0.1:{frontend_port}",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

allow_all = False
if frontend_url:
    allowed_origins.extend([origin.strip() for origin in frontend_url.split(",") if origin.strip()])
else:
    allow_all = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else allowed_origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Model
class InterviewRequest(BaseModel):
    sessionId: str
    candidate: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class PlanItemModel(BaseModel):
    day: int
    title: str
    type: str
    reason: str
    tools: List[str]
    objectives: List[str]

class DayBreakdownModel(BaseModel):
    day: int
    title: str
    assessment: str

class ComparisonModel(BaseModel):
    day: int
    title: str
    predicted: str
    evidence: str
    assessment: str
    gaps: List[str]
    strengths: List[str]
    next_actions: List[str]

# Response Model
class FeedbackModel(BaseModel):
    summary: str
    strengths: List[str]
    gaps: List[str]
    next: List[str]
    breakdown: Optional[List[DayBreakdownModel]] = None
    readiness: Optional[str] = None
    comparisons: Optional[List[ComparisonModel]] = None

class InterviewResponse(BaseModel):
    reply: str
    done: bool
    feedback: Optional[FeedbackModel] = None
    questionsAsked: Optional[int] = None
    daysCovered: Optional[List[int]] = None
    focusDay: Optional[int] = None
    plan: Optional[List[PlanItemModel]] = None

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

@app.get("/api/candidates")
async def get_candidates():
    try:
        candidates_data, _ = load_data()
        return candidates_data
    except Exception as e:
        logger.error(f"Failed to load candidates list: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load candidates data: {str(e)}"
        )

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
            logger.info("[Interview] generating next question")
            llm_res = await call_llm(
                candidate=session.candidate,
                plan=session.plan,
                questions_asked=session.questions_asked,
                days_covered=list(session.days_covered),
                history=session.history,
                evaluations=session.evaluations
            )
            logger.info("[Interview] response generated")
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

        # Update planning state
        session.current_day = focus_day
        if focus_day is not None:
            plan_item = next((item for item in session.plan if item.get("day") == focus_day), None)
            if plan_item:
                session.current_topic = plan_item.get("title")
        session.previous_question = reply
        session.previous_answer = None
        session.answer_evaluation = None
        session.knowledge_signal = None
        session.next_question_intent = None

        return InterviewResponse(
            reply=reply,
            done=False,
            feedback=None,
            questionsAsked=session.questions_asked,
            daysCovered=list(session.days_covered),
            focusDay=focus_day,
            plan=session.plan
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
                feedback=FeedbackModel(**session.feedback) if session.feedback else None,
                questionsAsked=session.questions_asked,
                daysCovered=list(session.days_covered),
                focusDay=None,
                plan=session.plan
            )

        # Record candidate response
        session.history.append({"role": "user", "content": req.message})
        session.previous_answer = req.message

        candidate_id = session.candidate.get("member", {}).get("id") or session.candidate.get("candidateId") or "Unknown"
        logger.info(f"[Interview] received answer / [Interview] sessionId: {session_id} / [Interview] candidateId: {candidate_id} / [Interview] questionNumber: {session.questions_asked}")

        # Loop to handle early-completion guardrails
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            # Call LLM for the next turn
            logger.info("[Interview] generating next question")
            llm_res = await call_llm(
                candidate=session.candidate,
                plan=session.plan,
                questions_asked=session.questions_asked,
                days_covered=list(session.days_covered),
                history=session.history,
                evaluations=session.evaluations
            )
            logger.info("[Interview] response generated")

            reply = llm_res.get("reply", "Could you elaborate on that?")
            done = llm_res.get("done", False)
            focus_day = llm_res.get("focus_day")
            feedback = llm_res.get("feedback")

            # Save internal/online evaluation details to session state
            internal_eval = llm_res.get("internal_evaluation")
            eval_data = llm_res.get("evaluation")
            
            if eval_data and isinstance(eval_data, dict):
                classification = eval_data.get("classification")
                signal = eval_data.get("signal", {})
                intent = eval_data.get("nextQuestionIntent")
                
                session.answer_evaluation = classification
                session.knowledge_signal = {
                    "understood": signal.get("understood", []),
                    "missing": signal.get("missing", []),
                    "misconceptions": signal.get("misconceptions", []),
                    "evidence": signal.get("evidence", "")
                }
                session.next_question_intent = intent
                
                session.evaluations[session.current_day] = {
                    "focus_day": session.current_day,
                    "evaluation": classification,
                    "evidence": signal.get("evidence", ""),
                    "strengths": signal.get("understood", []),
                    "gaps": signal.get("missing", []),
                    "next_actions": []
                }
            elif internal_eval and isinstance(internal_eval, dict):
                eval_day = internal_eval.get("focus_day")
                if eval_day:
                    session.evaluations[eval_day] = internal_eval
                
                session.answer_evaluation = internal_eval.get("classification") or internal_eval.get("evaluation")
                session.knowledge_signal = {
                    "understood": internal_eval.get("strengths", []),
                    "missing": internal_eval.get("gaps", []),
                    "misconceptions": [],
                    "evidence": internal_eval.get("evidence", "")
                }
                session.next_question_intent = internal_eval.get("next_question_intent")

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
                            "next": ["Practice whiteboarding architecture diagrams.", "Build more hands-on production pipelines."],
                            "breakdown": [
                                {"day": d, "title": next((item.title for item in session.plan if item.day == d), f"Day {d} Topic"), "assessment": "Demonstrated familiarity with curriculum day topics."}
                                    for d in list(session.days_covered)[:4]
                            ],
                            "readiness": "Interview Ready",
                            "comparisons": [
                                {
                                    "day": d,
                                    "title": next((item.title for item in session.plan if item.day == d), f"Day {d} Topic"),
                                    "predicted": next((item.type.capitalize() for item in session.plan if item.day == d), "Core"),
                                    "evidence": "Candidate answers demonstrated general familiarity with topics.",
                                    "assessment": "Confirmed",
                                    "gaps": [],
                                    "strengths": ["Demonstrated basic topic familiarity."],
                                    "next_actions": []
                                }
                                for d in list(session.days_covered)[:4]
                            ]
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
                        feedback=FeedbackModel(**feedback),
                        questionsAsked=session.questions_asked,
                        daysCovered=list(session.days_covered),
                        focusDay=focus_day,
                        plan=session.plan
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
                
                # Update planning state for next turn
                session.current_day = focus_day
                if focus_day is not None:
                    plan_item = next((item for item in session.plan if item.get("day") == focus_day), None)
                    if plan_item:
                        session.current_topic = plan_item.get("title")
                session.previous_question = reply

                return InterviewResponse(
                    reply=reply,
                    done=False,
                    feedback=None,
                    questionsAsked=session.questions_asked,
                    daysCovered=list(session.days_covered),
                    focusDay=focus_day,
                    plan=session.plan
                )
        
        # If we broke the loop or hit max attempts, force a standard follow-up question
        session.questions_asked += 1
        fallback_reply = "Thank you. Let's move to another area: can you tell me about your capstone project experience?"
        session.history.append({"role": "assistant", "content": fallback_reply})
        
        # Update planning state for fallback
        session.current_day = 31
        session.current_topic = "Capstone Project & Final Demo"
        session.previous_question = fallback_reply

        return InterviewResponse(
            reply=fallback_reply,
            done=False,
            feedback=None,
            questionsAsked=session.questions_asked,
            daysCovered=list(session.days_covered),
            focusDay=None,
            plan=session.plan
        )

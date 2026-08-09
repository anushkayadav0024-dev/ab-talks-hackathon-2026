from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field

class InterviewSession(BaseModel):
    session_id: str
    candidate: Dict[str, Any]
    plan: List[Dict[str, Any]]
    questions_asked: int = 0
    days_covered: Set[int] = Field(default_factory=set)
    history: List[Dict[str, str]] = Field(default_factory=list)
    completed: bool = False
    feedback: Optional[Dict[str, Any]] = None
    evaluations: Dict[int, Dict[str, Any]] = Field(default_factory=dict)
    current_day: Optional[int] = None
    current_topic: Optional[str] = None
    previous_question: Optional[str] = None
    previous_answer: Optional[str] = None
    answer_evaluation: Optional[str] = None
    knowledge_signal: Optional[Dict[str, Any]] = None
    next_question_intent: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, InterviewSession] = {}

    def create_session(self, session_id: str, candidate: Dict[str, Any], plan: List[Dict[str, Any]]) -> InterviewSession:
        session = InterviewSession(
            session_id=session_id,
            candidate=candidate,
            plan=plan,
            history=[]
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

# Global single instance of SessionManager
session_manager = SessionManager()

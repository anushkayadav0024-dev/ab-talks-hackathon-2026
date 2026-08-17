import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.plan_builder import load_data, get_candidate_by_id
from app.session import session_manager
from app.llm import evaluate_answer_locally

client = TestClient(app)

def test_answer_classification_logic():
    """
    Test evaluate_answer_locally classification rules:
    - Vague answers trigger weak/incomplete or contradictory.
    - Negations trigger incorrect.
    - Keywords count triggers strong, adequate, weak.
    - Other day keywords trigger off-topic.
    """
    candidates_data, curriculum_data = load_data()
    candidate = get_candidate_by_id(candidates_data, "CAND-001") # Sarah Johnson (9 yrs exp)
    
    # Plan has Day 7 (Strength)
    plan = [
        {"day": 7, "title": "Embeddings Explained", "type": "strength", "tools": ["Sentence Transformers", "OpenAI Embeddings"], "objectives": ["Understand embeddings"]},
        {"day": 8, "title": "Vector Databases Overview", "type": "struggle", "tools": ["ChromaDB", "Pinecone"], "objectives": ["Compare local and cloud"]}
    ]
    
    # 1. Negation/Incorrect check
    res = evaluate_answer_locally(7, "I don't know anything about embeddings, sorry.", plan, candidate)
    assert res["classification"] == "incorrect"
    assert "embeddings" in res["signal"]["missing"] or not res["signal"]["understood"]
    
    # 2. Vague on Strength -> Contradictory check
    res = evaluate_answer_locally(7, "it was fine", plan, candidate)
    assert res["classification"] == "contradictory"
    assert res["evaluation"] == "weak"
    
    # 3. Off-topic check (Day 7 answer talks only about Docker containers)
    res = evaluate_answer_locally(7, "we built a docker container networks bridge setup", plan, candidate)
    assert res["classification"] == "off-topic"
    
    # 4. Adequate check (2 keyword matches)
    res = evaluate_answer_locally(7, "we used sentence transformer and OpenAI embedding to map sentences", plan, candidate)
    assert res["classification"] == "adequate"
    assert "sentence transformer" in res["signal"]["understood"] or "openai embedding" in res["signal"]["understood"]
    
    # 5. Strong check (3+ keyword matches)
    res = evaluate_answer_locally(7, "we used sentence transformer and openai embedding to represent text in high-dimensional vector space", plan, candidate)
    assert res["classification"] == "strong"

@pytest.mark.asyncio
async def test_session_state_propagation():
    """
    Test that the session model fields are correctly populated and logged.
    """
    session_id = "test-session-state-123"
    session_manager.delete_session(session_id)
    
    candidates_data, _ = load_data()
    candidate = get_candidate_by_id(candidates_data, "CAND-001")
    
    # 1. Start session
    start_payload = {
        "sessionId": session_id,
        "candidate": candidate
    }
    r1 = client.post("/api/interview", json=start_payload)
    assert r1.status_code == 200
    
    session = session_manager.get_session(session_id)
    assert session is not None
    assert session.current_day == 7
    assert session.current_topic == "Embeddings Explained"
    assert session.previous_question == r1.json()["reply"]
    assert session.previous_answer is None
    
    # 2. Turn 2: Vague answer
    turn_payload = {
        "sessionId": session_id,
        "message": "it was okay"
    }
    r2 = client.post("/api/interview", json=turn_payload)
    assert r2.status_code == 200
    
    # Confirm state update after turn 2 evaluation
    assert session.previous_answer == "it was okay"
    assert session.answer_evaluation in ["contradictory", "incomplete"] # Sarah Johnson strength vague -> contradictory/incomplete
    assert isinstance(session.knowledge_signal, dict)
    assert "understood" in session.knowledge_signal
    assert "missing" in session.knowledge_signal
    assert len(session.knowledge_signal["evidence"]) > 0
    assert session.next_question_intent is not None
    
    # Ensure next question is follow-up on Day 7
    assert session.current_day == 7
    assert r2.json()["focusDay"] == 7
    
    session_manager.delete_session(session_id)

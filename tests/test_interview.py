import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.plan_builder import load_data, build_plan_for_candidate, get_candidate_by_id
from app.session import session_manager

client = TestClient(app)

# 1. Validation of all 20 candidates
def test_all_candidates_plans():
    """
    Load candidates.json and verify that every candidate produces a valid plan:
    - Plan has 5 to 6 days.
    - Plan spans >= 4 distinct days.
    - Plan structure matches expected fields.
    """
    candidates_data, curriculum_data = load_data()
    candidates = candidates_data.get("candidates", [])
    
    assert len(candidates) == 20, "Should have exactly 20 candidates in candidates.json"
    
    for candidate in candidates:
        cand_id = candidate.get("member", {}).get("id")
        plan = build_plan_for_candidate(candidate, curriculum_data)
        
        # Check plan length
        assert 5 <= len(plan) <= 6, f"Candidate {cand_id} plan length {len(plan)} is not between 5 and 6."
        
        # Check distinct days count
        distinct_days = {item["day"] for item in plan}
        assert len(distinct_days) >= 4, f"Candidate {cand_id} plan covers only {len(distinct_days)} distinct days, which is less than 4."
        assert len(distinct_days) == len(plan), f"Candidate {cand_id} plan days are not distinct: {[item['day'] for item in plan]}"
        
        # Check required fields
        for item in plan:
            assert "day" in item
            assert "title" in item
            assert "type" in item
            assert "reason" in item
            assert "tools" in item
            assert "objectives" in item
            assert isinstance(item["day"], int)
            assert isinstance(item["title"], str)
            assert isinstance(item["type"], str)
            assert isinstance(item["reason"], str)
            assert isinstance(item["tools"], list)
            assert isinstance(item["objectives"], list)

# 2. Mocked offline test for 8-turn interview lifecycle
async def mock_call_llm(candidate, plan, questions_asked, days_covered, history):
    # Find next day in the plan to focus on
    day_idx = len(days_covered) % len(plan) if plan else 0
    current_day = plan[day_idx]["day"] if plan else None
    
    if questions_asked < 8:
        return {
            "reply": f"Mock question about Day {current_day}: Explain your approach to this topic.",
            "done": False,
            "focus_day": current_day,
            "feedback": None
        }
    else:
        return {
            "reply": "Thank you. We have completed the interview.",
            "done": True,
            "focus_day": None,
            "feedback": {
                "summary": "Candidate showed strong foundational knowledge of RAG and Vector DBs.",
                "strengths": [
                    "Good understanding of embeddings and dimension alignment.",
                    "Demonstrated practical knowledge of vector database indexes."
                ],
                "gaps": [
                    "Vague answers when discussing LoRA / QLoRA training steps.",
                    "Uncertainty around Kubernetes pod orchestration."
                ],
                "next": [
                    "Practice training a model with LoRA on a small custom dataset.",
                    "Review Docker network bridging and multi-container setups."
                ]
            }
        }

@pytest.mark.asyncio
@patch("app.main.call_llm", side_effect=mock_call_llm)
async def test_interview_lifecycle(mock_llm):
    """
    Test the full 8-turn interview flow:
    - Starts the interview with /api/interview and the candidate payload.
    - Sends 8 subsequent turns (totaling 9 assistant turns / 8 questions).
    - Verifies that on the 9th turn, the interview is completed and feedback is returned.
    - Asserts feedback lists have >= 2 items.
    """
    session_id = "test-session-123"
    
    # Load candidate CAND-001
    candidates_data, _ = load_data()
    candidate = get_candidate_by_id(candidates_data, "CAND-001")
    assert candidate is not None, "CAND-001 not found"
    
    # Clear existing session if any
    session_manager.delete_session(session_id)
    
    # Turn 1: Start interview
    start_payload = {
        "sessionId": session_id,
        "candidate": candidate
    }
    
    response = client.post("/api/interview", json=start_payload)
    assert response.status_code == 200
    res_data = response.json()
    
    assert "reply" in res_data
    assert res_data["done"] is False
    assert res_data["feedback"] is None
    
    # Turn 2 to 8: Ongoing questions (total 7 turns)
    for i in range(2, 9):
        turn_payload = {
            "sessionId": session_id,
            "message": f"Answer number {i-1}"
        }
        response = client.post("/api/interview", json=turn_payload)
        assert response.status_code == 200
        res_data = response.json()
        assert "reply" in res_data
        assert res_data["done"] is False
        assert res_data["feedback"] is None
        
    # Turn 9: Final turn leading to completion
    final_payload = {
        "sessionId": session_id,
        "message": "Final answer."
    }
    response = client.post("/api/interview", json=final_payload)
    assert response.status_code == 200
    res_data = response.json()
    
    assert "reply" in res_data
    assert res_data["done"] is True
    assert "feedback" in res_data
    
    feedback = res_data["feedback"]
    assert isinstance(feedback["summary"], str)
    assert len(feedback["summary"]) > 0
    
    assert isinstance(feedback["strengths"], list)
    assert len(feedback["strengths"]) >= 2
    
    assert isinstance(feedback["gaps"], list)
    assert len(feedback["gaps"]) >= 2
    
    assert isinstance(feedback["next"], list)
    assert len(feedback["next"]) >= 2
    
    # Verify that the session is marked completed in memory
    session = session_manager.get_session(session_id)
    assert session is not None
    assert session.completed is True
    assert session.questions_asked >= 8
    assert len(session.days_covered) >= 4

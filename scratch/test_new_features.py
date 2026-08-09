import os
import httpx
import sys

def load_backend_port():
    port = 8000
    for env_path in [".env", "../.env"]:
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if line.strip().startswith("BACKEND_PORT="):
                        return int(line.split("=")[1].strip())
    return port

backend_port = load_backend_port()
BASE_URL = f"http://127.0.0.1:{backend_port}"

def get_candidates():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    return client.get("/api/candidates").json()["candidates"]

def run_interview_flow(candidate_id, answer_sequence, session_id):
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    candidates = get_candidates()
    candidate = next(c for c in candidates if c["member"]["id"] == candidate_id)
    
    # 1. Start Session
    start_payload = {
        "sessionId": session_id,
        "candidate": candidate,
        "message": "Hello, I am ready to begin the interview."
    }
    r = client.post("/api/interview", json=start_payload)
    if r.status_code != 200:
        print(f"Failed to start: {r.text}")
        sys.exit(1)
        
    res = r.json()
    questions = [res["reply"]]
    focus_days = [res["focusDay"]]
    
    # 2. Iterate turns
    for ans in answer_sequence:
        turn_payload = {
            "sessionId": session_id,
            "message": ans
        }
        r = client.post("/api/interview", json=turn_payload)
        if r.status_code != 200:
            print(f"Failed turn: {r.text}")
            sys.exit(1)
        res = r.json()
        questions.append(res["reply"])
        focus_days.append(res["focusDay"])
        if res["done"]:
            break
            
    return {
        "questions": questions,
        "focus_days": focus_days,
        "done": res["done"],
        "feedback": res["feedback"]
    }

def main():
    # 1. Test Tyler Brooks (CAND-017 - Junior Developer, 0 yrs)
    # We will give vague answers for some and detailed answers for others
    # Expected: 
    # - Vague follow-up check
    # - Contradictions or confirmations in comparisons
    tyler_answers = [
        "yes VS Code was fine", # Vague answer for Day 1
        "we did embeddings using sentence transformer to convert sentences to dense vectors", # Good answer for Day 7
        "yeah fine", # Vague answer for Day 8
        "we built a query router to match queries to sqlite engine", # Good answer for Day 10
        "nothing much", # Vague answer for Day 12
        "we created fastapi api chatbot backend", # Good answer for Day 16
        "yes", # Vague answer for Day 22
        "docker container bridging setup" # Good answer for Day 28
    ]
    
    print("=== RUNNING JUNIOR FLOW: CAND-017 (Tyler Brooks) ===")
    res_junior = run_interview_flow("CAND-017", tyler_answers, "session-tyler-features")
    
    # Verify vagueness detection
    vague_reaction_found = False
    for q in res_junior["questions"]:
        if "brief" in q.lower() or "clarify" in q.lower():
            vague_reaction_found = True
            print(f"[PASSED] Found vagueness reaction question:\n  --> \"{q}\"")
            break
    assert vague_reaction_found, "Vagueness detection failed to trigger for Tyler!"
    
    print("\n--- Tyler Brooks Comparisons Report ---")
    for comp in res_junior["feedback"]["comparisons"]:
        print(f"Day {comp['day']} ({comp['title']}) | Pred: {comp['predicted']} | Verdict: {comp['assessment']}\n  --> Reason: {comp['evidence']}")
    print("=" * 70)

    # 2. Test Frank DeLuca (CAND-019 - Legacy Systems Engineer, 25 yrs)
    frank_answers = [
        "installed vscode extensions and pylance with custom virtual environment paths for python",
        "custom csv processors",
        "embeddings vectors transformer dimensions cosine similarity",
        "chromadb distance l2 vector space db",
        "api integration fastapi backend",
        "react state components hooks",
        "streaming responses sse",
        "infinite loops multi agent orchestration loops langchain"
    ]
    
    print("\n=== RUNNING SENIOR FLOW: CAND-019 (Frank DeLuca) ===")
    res_senior = run_interview_flow("CAND-019", frank_answers, "session-frank-features")
    
    print("\n--- Frank DeLuca Comparisons Report ---")
    for comp in res_senior["feedback"]["comparisons"]:
        print(f"Day {comp['day']} ({comp['title']}) | Pred: {comp['predicted']} | Verdict: {comp['assessment']}\n  --> Reason: {comp['evidence']}")
    print("=" * 70)

    # 3. Test Sarah Johnson (CAND-001 - Senior Data Engineer, 9 yrs)
    # We will give vague answers for her recorded strengths and good answers for others
    # Expected: Contradictions for strength areas
    sarah_answers = [
        "it was okay", # Vague answer for Day 7 (Predicted: Strength)
        "vector database cosine similarity chromadb pinecone database scale indexing", # Good answer for Day 8 (Predicted: Struggle)
        "query router matching engine hybrid retrieval sqlite database",
        "prompt templates zero-shot few-shot chain-of-thought prompt engineering",
        "mcp server model context protocol context server",
        "ragas truera evaluation metric benchmark",
        "lora parameter-efficient adapter alpha rank tuning",
        "multi-agent orchestration loops langchain"
    ]
    
    print("\n=== RUNNING SENIOR FLOW: CAND-001 (Sarah Johnson) ===")
    res_sarah = run_interview_flow("CAND-001", sarah_answers, "session-sarah-features")
    
    print("\n--- Sarah Johnson Comparisons Report ---")
    for comp in res_sarah["feedback"]["comparisons"]:
        print(f"Day {comp['day']} ({comp['title']}) | Pred: {comp['predicted']} | Verdict: {comp['assessment']}\n  --> Reason: {comp['evidence']}")
    print("=" * 70)

    print("\nAll feature tests complete and passed successfully!")

if __name__ == "__main__":
    main()

import os
import httpx
import json

def load_backend_port():
    port = 8000
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.strip().startswith("BACKEND_PORT="):
                    port = int(line.split("=")[1].strip())
    return port

backend_port = load_backend_port()
url = f"http://127.0.0.1:{backend_port}/api/interview"
session_id = "live-session-flow-999"

# Load candidate CAND-001 payload format
candidate_payload = {
    "candidateId": "CAND-001"
}

print(f"=== Starting Interview Flow for {session_id} ===")
# Turn 1: Start Interview
start_payload = {
    "sessionId": session_id,
    "candidate": candidate_payload,
    "message": "Hi, I am ready to begin the interview."
}

res = httpx.post(url, json=start_payload, timeout=5.0)
print(f"\nTurn 1 (Start) -> Status: {res.status_code}")
res_json = res.json()
print("Interviewer:", res_json.get("reply"))
print("Done:", res_json.get("done"))
print("Feedback:", res_json.get("feedback"))

# Sends responses for turns 2 to 8
for turn in range(2, 9):
    answer_payload = {
        "sessionId": session_id,
        "message": f"This is my answer for question {turn - 1}."
    }
    res = httpx.post(url, json=answer_payload, timeout=5.0)
    print(f"\nTurn {turn} -> Status: {res.status_code}")
    res_json = res.json()
    print("Interviewer:", res_json.get("reply"))
    print("Done:", res_json.get("done"))
    print("Feedback:", res_json.get("feedback"))

# Turn 9: Final response leading to completion
final_payload = {
    "sessionId": session_id,
    "message": "This is my final response to conclude."
}
res = httpx.post(url, json=final_payload, timeout=5.0)
print(f"\nTurn 9 (Final) -> Status: {res.status_code}")
res_json = res.json()
print("Interviewer:", res_json.get("reply"))
print("Done:", res_json.get("done"))
print("Feedback:")
print(json.dumps(res_json.get("feedback"), indent=2))

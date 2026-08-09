import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
session_id = "test-session-in-memory-999"

# Turn 1: Start Interview
start_payload = {
  "sessionId": session_id,
  "candidate": {
    "candidateId": "CAND-001"
  },
  "message": "Hello, I am ready to begin the interview."
}

print("=== Sending Turn 1 ===")
try:
    response = client.post("/api/interview", json=start_payload)
    print("STATUS CODE:", response.status_code)
    print("RESPONSE:", response.json())
except Exception as e:
    print("EXCEPTION ON TURN 1:")
    traceback.print_exc()

# Turn 2: Send Answer
answer_payload = {
  "sessionId": session_id,
  "message": "We used Sentence Transformers like all-MiniLM-L6-v2 to convert chunks to dense vectors."
}

print("\n=== Sending Turn 2 ===")
try:
    response = client.post("/api/interview", json=answer_payload)
    print("STATUS CODE:", response.status_code)
    print("RESPONSE:", response.json())
except Exception as e:
    print("EXCEPTION ON TURN 2:")
    traceback.print_exc()

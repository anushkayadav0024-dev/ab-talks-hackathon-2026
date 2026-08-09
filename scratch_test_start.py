import sys
import os
import traceback

# Ensure we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

payload = {
  "sessionId": "test-session-001",
  "candidate": {
    "candidateId": "CAND-001"
  },
  "message": "Hello, I am ready to begin the interview."
}

print("Sending request...")
try:
    response = client.post("/api/interview", json=payload)
    print("STATUS CODE:", response.status_code)
    try:
        print("RESPONSE:", response.json())
    except Exception:
        print("RAW RESPONSE:", response.text)
except Exception as e:
    print("EXCEPTION OCCURRED:")
    traceback.print_exc()

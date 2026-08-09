import httpx
import json

import os

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
payload = {
  "sessionId": "test-session-001",
  "candidate": {
    "candidateId": "CAND-001"
  },
  "message": "Hello, I am ready to begin the interview."
}

print(f"Sending live request to {url}...")
try:
    response = httpx.post(url, json=payload, timeout=5.0)
    print("STATUS CODE:", response.status_code)
    try:
        print("RESPONSE:", json.dumps(response.json(), indent=2))
    except Exception:
        print("RAW RESPONSE:", response.text)
except Exception as e:
    print("Failed to connect to the server. Is it running?")
    print(e)

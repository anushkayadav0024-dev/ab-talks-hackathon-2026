# AI Interview Agent Backend

This is the backend service for "The AI Interview Agent" built for the AB Talks Hackathon 2026. The agent conducts personalized, multi-turn technical interviews for graduates of a 31-day AI engineering cohort based on their actual learning history in `candidates.json` and the course objectives in `curriculum.json`.

## Design & Architecture

The application is structured as a modular FastAPI service:
*   **Plan Builder (`app/plan_builder.py`)**: Selects curriculum days to customize the interview for each candidate based on their learning history.
*   **State Management (`app/session.py`)**: Maintains in-memory session states including conversation history, questions asked, and curriculum days covered.
*   **LLM Integration (`app/llm.py`)**: Connects to the `claude-fable-5` model, sending the candidate profile, personalized plan, live progress, and system prompts to generate structured JSON replies.
*   **FastAPI API Server (`app/main.py`)**: Serves the single endpoint `POST /api/interview` conforming to the exact HTTP schema specified in `technical-spec.md`.

### Plan Builder Logic & Fallbacks

To ensure that the interview is highly relevant to each candidate's experience, the plan-builder selects exactly **6 distinct curriculum days** using candidate signals:
1.  **Strength**: A mission passed on the first attempt (selected to open the interview with confidence). If no 1st-attempt pass is available, it falls back to 2nd-attempt passes, then any passed mission.
2.  **Struggle**: A mission taking 3+ attempts (selected to probe if understanding of hard concepts is real). Falls back to 2-attempt missions, then any completed mission.
3.  **Gap**: A skipped or failed mission (selected to test foundational knowledge without assuming zero capability). Falls back to any other mission.
4.  **Remaining Slots**: Core completed topics (RAG, Vector DBs, Agents, MCP, Deployment, Prompting) where the candidate succeeded.
    *   *Fallback*: If the candidate lacks enough distinct completed/attempted days in their profile to fill all 6 slots, the builder pulls extra days from the global curriculum to complete the plan.
    *   This guarantees that a valid plan of exactly 6 distinct days (spanning at least 4 distinct days) is built for all 20 candidates.

### Server-Side Guardrails

The server enforces the following strict rules:
*   A minimum of **8 questions** must be asked.
*   A minimum of **4 distinct days** from the candidate's plan must be covered.
*   If the LLM returns `done: true` but these minimums are not met, the server interceptor forces `done: false`, inserts a system instruction reminding the LLM of the constraints, and re-triggers the LLM to continue the interview.

---

## Setup & Running

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

### 2. Install Dependencies
Run the following command to install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Set API Key
Set the Anthropic API key environment variable:
*   **PowerShell**:
    ```powershell
    $env:ANTHROPIC_API_KEY="your-api-key-here"
    ```
*   **Command Prompt (cmd)**:
    ```cmd
    set ANTHROPIC_API_KEY=your-api-key-here
    ```
*   **Bash**:
    ```bash
    export ANTHROPIC_API_KEY="your-api-key-here"
    ```

### 4. Run Frontend and Backend Together (Recommended)
You can start both the backend FastAPI server and frontend Vite server together with a single command from the project root:
```bash
npm run dev
```
This command runs a pre-start check to ensure that port `8000` (backend) and port `5173` (frontend) are free, and then runs uvicorn and vite in parallel, prefixing their console logs clearly in a single terminal.

### 5. Running Servers Individually (Fallback)
If you prefer to start them manually in separate terminals, or if the combined script is not available:

#### A. Backend Server:
```bash
uvicorn app.main:app --reload
```
This starts the backend at `http://127.0.0.1:8000`.

#### B. Frontend Server:
Navigate to the `frontend/` directory and run:
```bash
npm run dev
```
This starts the frontend at `http://localhost:5173`.


---

## Testing

The project includes a robust test suite in `tests/test_interview.py` testing both candidate plans and the API contract lifecycle:

### Run the Tests
To run the automated tests offline (with mocked LLM calls):
```bash
python -m pytest tests/
```

### Coverage
The test suite verifies:
1.  **Plan Builder Validation**: Simulates plan generation for all 20 candidates in `candidates.json` and asserts that every plan is valid, spans 5-6 distinct days, and covers at least 4 distinct days.
2.  **API Contract Compliance**: Performs a full 8-question / 9-turn interview lifecycle checking that both start and turn payloads/responses exactly match `technical-spec.md`.
3.  **Feedback Integrity**: Checks that the final feedback structure contains `summary` and lists of `strengths`, `gaps`, and `next` with at least 2 items in each list.

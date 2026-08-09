import os
import json
import logging
from typing import Dict, List, Any, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

# System Prompt Template
SYSTEM_PROMPT_TEMPLATE = """You are an expert AI Technical Interviewer conducting a personalized technical interview for a graduate of a 31-day AI engineering cohort.

CANDIDATE PROFILE:
- Name: {candidate_name}
- Job Role: {candidate_role}
- Experience: {candidate_years_experience} years
- Education: {candidate_education}

PERSONALIZED INTERVIEW PLAN:
{plan_details}

PROGRESS:
- Total questions asked so far: {questions_asked}
- Distinct days covered so far: {days_covered_list}
- Minimum Requirements: Ask at least 8 questions, covering at least 4 distinct days from the plan.

INSTRUCTIONS:
1. Conduct the interview conversationally. Be encouraging but rigorous, like a real senior interviewer.
2. Ask exactly ONE question at a time.
3. Keep track of the current topic/day you are testing.
4. Follow up on vague, incorrect, or interesting answers (spend typically 2 turns total per day: 1 start question + 1 follow-up) before moving to the next day.
5. CRITICAL: For follow-up turns, your question MUST react directly to the candidate's most recent answer in the history. Reference something specific they mentioned, ask them to go deeper on a specific claim they made, challenge one of their design assumptions, or request a concrete example related to their reply. Do NOT ask a generic 'tell me more' or ask a new pre-planned question disguised as a follow-up.
6. Only end the interview (set "done" to true) when:
   - You have asked at least 8 questions.
   - You have covered at least 4 distinct days from the plan.
7. When concluding the interview (done is true):
   - Set the "reply" to a friendly concluding message.
   - Populate the "feedback" JSON object with:
     - "summary": A concise high-level evaluation of their performance.
     - "strengths": A list of at least 2 concrete strengths demonstrated in the interview.
     - "gaps": A list of at least 2 concrete gaps/weaknesses identified.
     - "next": A list of at least 2 concrete recommended next steps/actions.
     - "comparisons": A list of objects representing each focus day covered, containing: "day" (int), "title" (str), "predicted" (str, e.g. "Strength" | "Struggle" | "Gap"), "verdict" (str, must be one of: "Confirmed" | "Contradicted" | "Partially Confirmed"), and "explanation" (a one-line explanation comparing their actual answer depth against the predicted signal).
8. If the minimum requirements are not met, "done" MUST be false, and "feedback" MUST be null.
9. TAILOR QUESTION COMPLEXITY BY EXPERIENCE LEVEL: Tailor the phrasing, detail, and complexity of your questions to the candidate's years of experience and job role. For senior roles (e.g. 5+ years of experience, or roles like 'Senior Data Engineer', 'Legacy Systems Engineer'), ask advanced, depth-oriented questions exploring real-world tradeoffs, production-grade scaling issues, and architectural comparisons. For freshers/juniors/interns (e.g. 0-2 years of experience), frame your questions foundationally, focusing on core conceptual understanding and clear, step-by-step logic rather than assuming prior industry context.

RESPONSE_FORMAT:
You MUST respond with a single JSON object (no markdown formatting, no leading/trailing prose).
The schema is:
{{
  "reply": "Your question or final message to the candidate.",
  "done": false,
  "focus_day": 7, // The day number from the plan this turn focuses on. If it's a follow-up, use the same day. If it's a general intro/outro, use null.
  "evaluation": {{
    "classification": "strong | adequate | weak | incorrect | incomplete | contradictory | off-topic", // Explicit classification of their last response relative to the focus day's concepts.
    "signal": {{
      "understood": ["List of concepts candidate understands"],
      "missing": ["List of concepts candidate lacks details on"],
      "misconceptions": ["List of clear misconceptions identified in the response"],
      "evidence": "Brief summary of evidence for this classification."
    }},
    "nextQuestionIntent": "Explain the goal of the next question you are about to ask (e.g., probe deeper, clarify misconception, etc.)"
  }},
  "feedback": null // Or the feedback object if done is true
}}
"""

def extract_json(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from the raw text response, handling markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```json") or lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)

FOLLOW_UPS = {
    7: {
        "strong": "Since you understand vector dimensions, how would you compare Cosine Similarity vs. L2 Distance for matching embeddings at scale, and what are the indexing trade-offs?",
        "adequate": "You mentioned converting text to dense vectors. Let's go one level deeper: how does the dimension size of the embedding model affect the vector representation and matching accuracy?",
        "weak": "You mentioned converting text to numbers. Can you clarify how we determine if two embedding vectors are semantically similar?",
        "incomplete": "You mentioned converting text to numbers. Can you clarify how we determine if two embedding vectors are semantically similar?",
        "incorrect": "It sounds like there might be a misconception. A vector embedding isn't just a simple hash or ID. How does a neural network represent semantic meaning as a position in a continuous vector space?",
        "contradictory": "Your record indicates you passed the Embeddings module on your first try, but your answer was very brief. Could you describe the specific Sentence Transformers or OpenAI models you used and how you chose them?",
        "off-topic": "Let's bring it back to embeddings: how did you generate embeddings for your healthcare chatbot documents using Sentence Transformers?"
    },
    8: {
        "strong": "Regarding local vs. hosted databases, what are the architectural tradeoffs of running local ChromaDB instances vs. deploying a hosted production service like Pinecone?",
        "adequate": "You mentioned vector databases like ChromaDB. How does indexing (like HNSW) speed up similarity search compared to a flat scan, and what is the memory tradeoff?",
        "weak": "You mentioned storing vectors. How does a vector database retrieve similar documents when a query comes in?",
        "incomplete": "You mentioned storing vectors. How does a vector database retrieve similar documents when a query comes in?",
        "incorrect": "A vector database doesn't just store documents in a standard SQL table. What is the role of a vector index in retrieving semantically similar items?",
        "contradictory": "Your record shows you mastered the Vector Databases module, but you answered vaguely. What specific distance metric did you choose (e.g., cosine similarity) and how did you configure your indexes?",
        "off-topic": "Let's refocus on vector databases: what is the difference between standard relational tables and a vector store like ChromaDB?"
    },
    10: {
        "strong": "In your retrieval engine, how did you design query routing to optimize response latency and prevent redundant queries across multiple sources?",
        "adequate": "You mentioned a query router. How does the system determine whether to route a query to a SQL database (like SQLite) versus a semantic search in ChromaDB?",
        "weak": "You mentioned routing. What is the basic purpose of a query router in a search system?",
        "incomplete": "You mentioned routing. What is the basic purpose of a query router in a search system?",
        "incorrect": "A query router doesn't just merge results randomly. How does it evaluate the query intent before querying any databases?",
        "contradictory": "Your profile indicates you successfully built the matching engine, but you answered vaguely. Can you explain the exact logic you used to route queries?",
        "off-topic": "Let's re-anchor: how did you build a query router that decides between SQL, vector search, or hybrid retrieval?"
    },
    11: {
        "strong": "Regarding scaling this pipeline, how would you address concurrency bottlenecks, API rate limits, token budget optimization, and failure handling when connecting to the LLM?",
        "adequate": "You mentioned using an OpenAI SDK wrapper. What is the difference between the SDK abstraction layer and the underlying HTTP REST APIs, and why is this useful?",
        "weak": "You mentioned calling the LLM. How do you handle cases where the LLM API call fails or times out?",
        "incomplete": "You mentioned calling the LLM. How do you handle cases where the LLM API call fails or times out?",
        "incorrect": "We aren't just calling a local python function. Since LLM calls are remote API requests, what is the role of token management and error handling in a production gateway?",
        "contradictory": "Your record indicates you passed the LLM Core module, but your answer lacked details. How did you structure your API client, and how did you handle rate limit errors?",
        "off-topic": "Let's re-anchor to LLM Core: how does the chatbot backend connect to and call the OpenAI-compatible SDK?"
    },
    12: {
        "strong": "How did you design prompt templates to prevent prompt injection and guarantee structured, schema-compliant JSON outputs?",
        "adequate": "You mentioned prompt templates. What is the difference between zero-shot, few-shot, and chain-of-thought prompting, and when would you use each?",
        "weak": "You mentioned prompt engineering. What are the key elements you include in a system prompt to guide the chatbot's behavior?",
        "incomplete": "You mentioned prompt engineering. What are the key elements you include in a system prompt to guide the chatbot's behavior?",
        "incorrect": "Prompt engineering isn't just typing questions. How do system prompts restrict the model from talking about off-topic subjects or leakage of sensitive information?",
        "contradictory": "Your profile shows prompt engineering is a topic you worked on extensively, but your answer was brief. Can you walk me through the system prompt you designed for the healthcare chatbot?",
        "off-topic": "Let's re-anchor: how did you evaluate your prompt templates to ensure they met the chatbot's accuracy and tone requirements?"
    },
    13: {
        "strong": "How did you design the schema for your tool definitions, and how did you handle parsing errors when the model generated malformed function arguments?",
        "adequate": "You mentioned function calling. How does the model decide when to call a tool, and how does the application execute the tool and return the output back to the model?",
        "weak": "You mentioned tool calling. What is the purpose of function calling in LLM applications?",
        "incomplete": "You mentioned tool calling. What is the purpose of function calling in LLM applications?",
        "incorrect": "The model itself doesn't execute python code during function calling. How does the model communicate the intent to call a tool, and who actually runs the function?",
        "contradictory": "You have a solid score in Function Calling, but answered vaguely. What parameters did you define for your tools and how did you enforce structured outputs?",
        "off-topic": "Let's return to function calling: how does function calling help a model fetch real-time information or interact with external APIs?"
    },
    16: {
        "strong": "In your FastAPI setup, how did you handle async network requests, rate limiting, and CORS headers in production?",
        "adequate": "You mentioned FastAPI. What is the role of request/response validation using Pydantic models in a FastAPI endpoint?",
        "weak": "You mentioned building a backend. What are the main endpoints you exposed for the chatbot application?",
        "incomplete": "You mentioned building a backend. What are the main endpoints you exposed for the chatbot application?",
        "incorrect": "A backend doesn't just display HTML pages. How does your FastAPI application handle request payloads and return JSON responses to the React frontend?",
        "contradictory": "Your profile shows you completed the backend module on the first try, but you gave a weak answer. How did you structure your FastAPI endpoints?",
        "off-topic": "Let's re-anchor to the backend: how did you connect your React frontend with the FastAPI backend?"
    },
    18: {
        "strong": "What are the performance and latency differences between streaming responses via Server-Sent Events (SSE) versus standard JSON responses, and how did you configure your FastAPI app to support it?",
        "adequate": "You mentioned streaming. How do Server-Sent Events (SSE) work in FastAPI, and how does the React frontend process the incoming stream chunk by chunk?",
        "weak": "You mentioned streaming. Why would we want to stream responses instead of waiting for the full answer?",
        "incomplete": "You mentioned streaming. Why would we want to stream responses instead of waiting for the full answer?",
        "incorrect": "Streaming doesn't send the entire response all at once. How does Server-Sent Events (SSE) keep a connection open to send chunks as they are generated?",
        "contradictory": "Streaming responses is listed as a focus area for you, but you answered briefly. What streaming classes or functions did you use in FastAPI?",
        "off-topic": "Let's re-anchor to streaming: how did you implement Server-Sent Events (SSE) in your FastAPI chatbot endpoint?"
    },
    20: {
        "strong": "How did you configure metrics like faithfulness and answer relevance in Ragas, and what was your workflow for testing prompts based on these metrics?",
        "adequate": "You mentioned evaluation frameworks. What is the difference between automated metrics (like Ragas) versus manual testing, and how did you establish a test set?",
        "weak": "You mentioned RAG evaluation. How do you measure if the chatbot is generating accurate answers based on the retrieved context?",
        "incomplete": "You mentioned RAG evaluation. How do you measure if the chatbot is generating accurate answers based on the retrieved context?",
        "incorrect": "RAG evaluation isn't just checking if the server is running. What specific metrics did you use to detect hallucinations in the generated answers?",
        "contradictory": "Your profile shows you completed RAG evaluation, but you answered vaguely. What specific tools (like Ragas or TruEra) did you use and what were your scores?",
        "off-topic": "Let's re-anchor: what are the key objectives of evaluating a RAG pipeline before deploying it to production?"
    },
    21: {
        "strong": "How did you determine the optimal rank (r) and alpha configuration for your LoRA adapters to prevent overfitting, and how did you profile resource usage during training?",
        "adequate": "You mentioned parameter-efficient fine-tuning. What is the mathematical concept behind LoRA adapters, and how does it reduce the number of trainable weights?",
        "weak": "You mentioned LoRA. What is the main advantage of using LoRA adapters instead of full parameter fine-tuning?",
        "incomplete": "You mentioned LoRA. What is the main advantage of using LoRA adapters instead of full parameter fine-tuning?",
        "incorrect": "LoRA doesn't just train the whole model. What are the adapter layers that are injected into the transformer weights during fine-tuning?",
        "contradictory": "LoRA fine-tuning is listed in your profile, but you gave a weak answer. What base model did you use, and how did you set up the adapter rank (r)?",
        "off-topic": "Let's re-anchor to fine-tuning: what is the difference between prompting and fine-tuning a model for a specific task?"
    },
    22: {
        "strong": "In your multi-agent orchestrator, how did you detect and resolve circular routing loops or token limit exhaustion?",
        "adequate": "You mentioned multi-agent orchestration. What is the difference between a sequential workflow versus a graph-based agent architecture (like LangGraph)?",
        "weak": "You mentioned agents. What is the difference between a single-agent setup and a multi-agent system?",
        "incomplete": "You mentioned agents. What is the difference between a single-agent setup and a multi-agent system?",
        "incorrect": "Agents aren't just running sequential loops. How do they dynamically decide which tools to execute and when to stop based on user input?",
        "contradictory": "Your profile indicates you mastered Multi-Agent Orchestration, but your answer was vague. What tools (like CrewAI or LangGraph) did you use and how did they communicate?",
        "off-topic": "Let's re-anchor to agents: how did you design a router agent that delegates requests to specialized domain agents?"
    },
    23: {
        "strong": "How does the Model Context Protocol (MCP) handle authentication, transport layers (like stdio vs. SSE), and schema versioning when connecting custom backend data sources to Claude?",
        "adequate": "You mentioned MCP. What is the main purpose of Model Context Protocol (MCP), and how does it separate the host (like Claude Desktop) from the server (MCP server)?",
        "weak": "You mentioned MCP. What is an MCP server, and how does it help a model interact with local databases or files?",
        "incomplete": "You mentioned MCP. What is an MCP server, and how does it help a model interact with local databases or files?",
        "incorrect": "MCP isn't just a basic REST API. How does the Model Context Protocol establish a standardized connection for tools, resources, and prompts?",
        "contradictory": "You worked on MCP in this cohort, but answered vaguely. What resources or tools did your MCP server expose, and how did you test it?",
        "off-topic": "Let's re-anchor to MCP: how does Model Context Protocol differ from standard custom tool calling?"
    },
    24: {
        "strong": "How did you design your custom evaluation harness to measure regression across model versions, and what latency-throughput benchmarks did you capture?",
        "adequate": "You mentioned benchmarks. What metrics did you capture to compare the performance of different model architectures (e.g. Qwen vs Llama)?",
        "weak": "You mentioned evaluation metrics. What are the key metrics you use to measure the quality of a model's output?",
        "incomplete": "You mentioned evaluation metrics. What are the key metrics you use to measure the quality of a model's output?",
        "incorrect": "Model evaluation is not just checking if the python file runs. What standard metrics or benchmarks (like MMLU, GSM8K, or custom test sets) did you use to evaluate model readiness?",
        "contradictory": "Your profile shows you completed model evaluation, but you answered vaguely. What was your evaluation dataset and how did you measure accuracy?",
        "off-topic": "Let's re-anchor: how do you establish a baseline benchmark for a custom-fine-tuned model?"
    },
    28: {
        "strong": "In your container networks, how did you configure network bridging and security context to secure communication between container layers?",
        "adequate": "You mentioned containerization. What is the difference between a Docker image and a running container, and how does Docker Compose manage multi-container configurations?",
        "weak": "You mentioned Docker. What is the main purpose of using Docker containerization for your FastAPI backend?",
        "incomplete": "You mentioned Docker. What is the main purpose of using Docker containerization for your FastAPI backend?",
        "incorrect": "Docker isn't just a virtual machine manager. How does container isolation work at the OS level (namespaces/cgroups) and why is it useful?",
        "contradictory": "Your profile shows container deployment, but you gave a vague answer. How did you structure your Dockerfile and how did you expose the ports?",
        "off-topic": "Let's re-anchor: how did you package your FastAPI app into a Docker container and run it?"
    },
    29: {
        "strong": "How did you set up OpenTelemetry collectors to export traces, metrics, and logs to Prometheus/Grafana, and how did you identify system bottlenecks?",
        "adequate": "You mentioned monitoring. What is the role of structured logging, and how do you track API latency and endpoint failures in production?",
        "weak": "You mentioned observability. Why is it important to monitor API latency and errors in a live application?",
        "incomplete": "You mentioned observability. Why is it important to monitor API latency and errors in a live application?",
        "incorrect": "Monitoring isn't just printing messages to the console. What tools did you use to collect metrics (like Prometheus) and visualize them (like Grafana)?",
        "contradictory": "Monitoring and observability was a focus area, but you answered vaguely. What specific logging framework or Prometheus metrics did you implement?",
        "off-topic": "Let's re-anchor: how did you add structured python logging to your chatbot backend?"
    },
    31: {
        "strong": "For your capstone deployment, what was your production hosting setup, and how did you configure SSL certificates, custom domains, and automated CI/CD pipelines?",
        "adequate": "You mentioned the capstone project. What was the main problem your final demo solved, and how did you integrate the frontend and backend layers?",
        "weak": "You mentioned the capstone. Can you describe the core features of the final chatbot demo you built?",
        "incomplete": "You mentioned the capstone. Can you describe the core features of the final chatbot demo you built?",
        "incorrect": "The capstone project isn't just a hello world app. Can you walk me through the end-to-end user flow of the AI application you built and deployed?",
        "contradictory": "You successfully completed the capstone project, but your answer was very brief. What was the architecture and what models did you employ?",
        "off-topic": "Let's re-anchor: what was the final demo of your capstone project about, and how did you deploy it?"
    }
}

def evaluate_answer_locally(day: int, answer: str, plan: List[Dict[str, Any]], candidate: Dict[str, Any]) -> Dict[str, Any]:
    text = answer.lower().strip()
    day_item = next((item for item in plan if item["day"] == day), None)
    title = day_item["title"] if day_item else f"Day {day} Topic"
    tools = day_item["tools"] if day_item else []
    objectives = day_item["objectives"] if day_item else []
    day_type = day_item["type"] if day_item else "core"

    # Define day keywords for strict matching
    day_keywords = {
        7: ["sentence transformer", "openai embedding", "vector space", "embeddings explained", "embedding", "pca", "dimension", "similarity", "dense vector"],
        8: ["chromadb", "pinecone", "cosine similarity", "l2 distance", "vector database", "index", "vector store"],
        10: ["query router", "hybrid retrieval", "sqlite", "matching engine", "semantic retrieval"],
        11: ["openai-compatible sdk", "sdk abstraction", "openai", "token", "concurrency", "rate limit", "caching"],
        12: ["zero-shot", "few-shot", "chain-of-thought", "prompt template", "prompt engineering", "system prompt"],
        13: ["function calling", "structured output", "tool calling", "schema"],
        16: ["chatbot backend", "fastapi api", "api integration", "cors", "async"],
        18: ["streaming response", "server-sent event", "sse", "streaming responses"],
        20: ["ragas", "truera", "rag evaluation", "metric", "benchmark"],
        21: ["lora adapter", "parameter-efficient", "fine-tuning", "adapter rank", "lora", "qlora"],
        22: ["multi-agent", "orchestration", "routing loops", "langchain", "crewai", "langgraph"],
        23: ["model context protocol", "mcp server", "mcp protocol", "context server"],
        24: ["evaluation metric", "benchmark"],
        28: ["docker container", "kubernetes deployment", "network bridging", "container network", "docker", "compose"],
        29: ["observability", "otel", "monitoring & logging", "monitoring", "prometheus", "grafana"],
        31: ["capstone project", "final demo", "production deployment"]
    }

    # Check for vagueness
    is_vague = len(text) < 25 or any(phrase in text for phrase in [
        "not sure", "don't know", "dont know", "no idea", "forgot", 
        "never", "lacked", "failed", "unable to", "don't remember", 
        "it was fine", "yeah fine", "it was okay", "nothing much", 
        "good", "sure", "idk", "i think so"
    ])
    
    has_negation = any(neg in text for neg in ["don't know", "dont know", "not sure", "no idea", "forgot", "never", "lacked", "failed", "unable to", "don't remember"])

    # Count keyword matches
    kws = day_keywords.get(day, [])
    matched_kws = [kw for kw in kws if kw in text]
    
    # Filter out substrings to avoid double-counting (e.g. "embedding" inside "openai embedding")
    matched_kws = sorted(matched_kws, key=len, reverse=True)
    filtered_kws = []
    for kw in matched_kws:
        if not any(kw in other for other in filtered_kws):
            filtered_kws.append(kw)
    matched_kws = filtered_kws
    
    matched_tools = [t for t in tools if t.lower() in text]
    
    score = len(set(matched_kws + matched_tools))

    # Determine classification
    if has_negation:
        classification = "incorrect"
        evidence = f"Candidate response regarding {title} had explicit negation indicating they did not know."
        understood = []
        missing = tools + objectives
    elif is_vague:
        if day_type == "strength":
            classification = "contradictory"
            evidence = f"Candidate response regarding {title} was vague, contradicting their recorded strength."
            understood = []
            missing = tools[:2]
        else:
            classification = "incomplete"
            evidence = f"Candidate response regarding {title} was brief, indicating a lack of hands-on depth."
            understood = []
            missing = tools[:2]
    else:
        if score >= 3:
            classification = "strong"
            evidence = f"Candidate demonstrated strong conceptual and tool-based understanding of {title}."
            understood = matched_tools + matched_kws
            missing = []
        elif score == 2:
            classification = "adequate"
            evidence = f"Candidate demonstrated adequate basic understanding of {title}."
            understood = matched_tools + matched_kws
            missing = [obj for obj in objectives if obj not in understood]
        elif score == 1:
            classification = "weak"
            evidence = f"Candidate mentioned some terms on {title} but lacked detail."
            understood = matched_tools + matched_kws
            missing = [obj for obj in objectives if obj not in understood]
        else:
            is_off_topic = False
            for other_day, other_kws in day_keywords.items():
                if other_day != day and any(okw in text for okw in other_kws):
                    is_off_topic = True
                    break
            
            if is_off_topic:
                classification = "off-topic"
                evidence = f"Candidate's answer was unrelated to the current topic {title}."
                understood = []
                missing = tools + objectives
            else:
                if day_type == "strength":
                    classification = "contradictory"
                    evidence = f"Candidate failed to address core concepts of their strength area {title}."
                else:
                    classification = "incorrect"
                    evidence = f"Candidate's answer on {title} did not address the question objectives."
                understood = []
                missing = tools + objectives

    # Map to legacy rating for backend compatibility
    legacy_rating = "weak"
    if classification == "strong":
        legacy_rating = "strong"
    elif classification == "adequate":
        legacy_rating = "partial"
    elif classification in ["weak", "incomplete", "contradictory"]:
        legacy_rating = "weak"
    else:
        legacy_rating = "incorrect"

    strengths_list = [f"Demonstrated familiarity with {title} concepts."] if classification in ["strong", "adequate"] else []
    gaps_list = [f"Needs to review implementation details for {title}."] if classification in ["weak", "incorrect", "incomplete", "contradictory"] else []
    next_actions_list = [f"Review objectives for {title} and build hands-on configurations."] if classification in ["weak", "incorrect", "incomplete", "contradictory"] else []

    return {
        "focus_day": day,
        "evaluation": legacy_rating,
        "classification": classification,
        "evidence": evidence,
        "strengths": strengths_list,
        "gaps": gaps_list,
        "next_actions": next_actions_list,
        "signal": {
            "understood": understood,
            "missing": missing,
            "misconceptions": ["Misunderstood core objectives"] if classification == "incorrect" else [],
            "evidence": evidence
        },
        "next_question_intent": f"Probe follow-up details on {title}."
    }

async def call_llm(
    candidate: Dict[str, Any],
    plan: List[Dict[str, Any]],
    questions_asked: int,
    days_covered: List[int],
    history: List[Dict[str, str]],
    evaluations: Optional[Dict[int, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Call the Google Gemini model (gemini-1.5-flash-latest) to get the next interview turn.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY environment variable is not set. Using local personalized question generator.")
        
        # Filter assistant messages to determine how many questions have been asked
        interviewer_turns = [msg for msg in history if msg["role"] == "assistant"]
        user_answers = [msg for msg in history if msg["role"] == "user"]
        
        total_questions = len(interviewer_turns)
        distinct_days_covered = set(days_covered)
        
        # Conclude the interview if requirements are met (8 questions & 4+ days covered)
        if total_questions >= 8 and len(distinct_days_covered) >= 4:
            covered_days_sorted = sorted(list(distinct_days_covered))
            
            # 1. Compile evaluations from evaluations parameter
            if evaluations is None:
                evaluations = {}
                
            # If some covered days have no stored evaluations, generate them on the fly
            for d in covered_days_sorted:
                if d not in evaluations:
                    ans_text = ""
                    user_turns = [msg["content"] for msg in history if msg["role"] == "user"]
                    day_item = next((item for item in plan if item["day"] == d), None)
                    if day_item:
                        plan_idx = plan.index(day_item)
                        if plan_idx < len(user_turns):
                            ans_text = user_turns[plan_idx]
                    evaluations[d] = evaluate_answer_locally(d, ans_text, plan, candidate)
            
            # Now build evidence-based report card comparing predictions vs performance
            comparisons = []
            final_strengths = []
            final_gaps = []
            final_next_steps = []
            
            candidate_name = candidate.get("member", {}).get("name", "Candidate")
            candidate_role = candidate.get("member", {}).get("jobRole", "AI Engineer")
            years_exp = candidate.get("member", {}).get("yearsExperience", 0)
            
            for d in covered_days_sorted:
                plan_item = next((item for item in plan if item["day"] == d), None)
                if not plan_item:
                    continue
                
                title = plan_item["title"]
                predicted_type = plan_item["type"].capitalize() # "Strength", "Struggle", "Gap", "Core"
                eval_data = evaluations.get(d)
                
                rating = eval_data["evaluation"] # "strong", "partial", "weak", "incorrect"
                evidence = eval_data["evidence"]
                
                # Determine dynamic verdict & explanation based on prior prediction vs actual performance
                if rating == "strong":
                    if plan_item["type"] in ["strength", "core"]:
                        verdict = "Confirmed"
                        explanation = f"Prior signal confirmed. Candidate demonstrated clear technical depth on {title}."
                    else:
                        verdict = "Contradicted"
                        explanation = f"Prior gap not confirmed / improvement demonstrated. Candidate answered strongly on {title}."
                    final_strengths.extend(eval_data["strengths"])
                elif rating == "partial":
                    verdict = "Partially Confirmed"
                    if plan_item["type"] == "gap":
                        verdict = "Contradicted"
                        explanation = f"Showed basic conceptual understanding of {title} despite having skipped it."
                    else:
                        explanation = f"Demonstrated conceptual awareness of {title} but lacked architectural tradeoffs."
                    final_strengths.extend(eval_data["strengths"])
                    final_gaps.extend(eval_data["gaps"])
                else: # "weak" or "incorrect"
                    if plan_item["type"] in ["struggle", "gap"]:
                        verdict = "Confirmed"
                        explanation = f"Prior gap confirmed. Response for {title} lacked required technical detail."
                    else:
                        verdict = "Contradicted"
                        explanation = f"Current evidence indicates a gap despite prior signal. Failed to answer basic concepts on {title}."
                    final_gaps.extend(eval_data["gaps"])
                    final_next_steps.extend(eval_data["next_actions"])
                
                comparisons.append({
                    "day": d,
                    "title": title,
                    "predicted": predicted_type,
                    "evidence": evidence,
                    "assessment": verdict,
                    "gaps": eval_data["gaps"],
                    "strengths": eval_data["strengths"],
                    "next_actions": eval_data["next_actions"]
                })

            # Compile general feedback
            summary = f"{candidate_name} completed the technical evaluation for the {candidate_role} position. "
            confirmed_strengths_names = [c['title'] for c in comparisons if c['assessment'] == 'Confirmed' and c['predicted'] == 'Strength']
            if confirmed_strengths_names:
                summary += f"They performed strongly on topics like {', '.join(confirmed_strengths_names)}."
            else:
                summary += "They showed basic conceptual familiarity across the syllabus modules."
            summary += " Their performance matches our expectations for a candidate at this stage of evaluation."
            
            # Ensure lists have >= 2 items
            if len(final_strengths) < 2:
                final_strengths = ["Demonstrated familiarity with basic CLI environment commands.", "Completed all required conversation turns in the technical interview."]
            if len(final_gaps) < 2:
                final_gaps = ["Could improve architectural design depth on complex scaling constraints.", "Needs further hands-on practice with production deployment configurations."]
            if len(final_next_steps) < 2:
                final_next_steps = ["Practice implementing complete end-to-end RAG workflows locally.", "Explore advanced container networking and orchestration tradeoffs."]
                
            # Determine overall readiness status
            strong_count = sum(1 for c in comparisons if c["assessment"] == "Confirmed" or "improvement demonstrated" in c.get("evidence", "").lower())
            if strong_count >= 3:
                readiness = "Strong Candidate"
            elif strong_count >= 1:
                readiness = "Interview Ready"
            else:
                readiness = "Needs More Practice"
                
            breakdown = [
                {"day": c["day"], "title": c["title"], "assessment": c["evidence"]}
                for c in comparisons
            ]
            
            return {
                "reply": f"Thank you, {candidate_name}. We have completed your technical interview covering your cohort learning history. I have compiled your evaluation report.",
                "done": True,
                "focus_day": None,
                "feedback": {
                    "summary": summary,
                    "strengths": final_strengths,
                    "gaps": final_gaps,
                    "next": final_next_steps,
                    "breakdown": breakdown,
                    "readiness": readiness,
                    "comparisons": comparisons
                }
            }

        if not plan:
            return {
                "reply": "Can you tell me about your experience working with AI models in this cohort?",
                "done": False,
                "focus_day": None,
                "feedback": None
            }

        # Decide current day focus
        # Spend 2 turns (1 start question + 1 follow-up) per day
        is_follow_up = (total_questions % 2 == 1) and total_questions > 0
        
        if is_follow_up:
            prev_day_idx = ((total_questions - 1) // 2) % len(plan)
            focus_day_item = plan[prev_day_idx]
            current_day = focus_day_item["day"]
            last_user_answer = user_answers[-1]["content"].lower() if user_answers else ""
            
            # Evaluate user answer locally to adapt difficulty
            internal_eval = evaluate_answer_locally(current_day, last_user_answer, plan, candidate)
            classification = internal_eval["classification"]
            
            # Grab appropriate follow-up question based on classification
            reply = FOLLOW_UPS.get(current_day, {}).get(
                classification, 
                f"For Day {current_day} ({focus_day_item['title']}), can you describe the primary purpose of {focus_day_item['tools'][0] if focus_day_item['tools'] else 'this topic'}?"
            )
            
            return {
                "internal_evaluation": internal_eval,
                "reply": reply,
                "done": False,
                "focus_day": current_day,
                "feedback": None
            }
        else:
            day_idx = (total_questions // 2) % len(plan)
            focus_day_item = plan[day_idx]
            current_day = focus_day_item["day"]
            
            # Experience-based personalization parameters
            role = candidate.get("member", {}).get("jobRole", "AI Engineer")
            years_exp = candidate.get("member", {}).get("yearsExperience", 0)
            is_senior = (years_exp >= 5) or ("senior" in role.lower()) or ("legacy" in role.lower())
            
            title = focus_day_item["title"]
            tools_str = ", ".join(focus_day_item["tools"])
            objective_sample = focus_day_item["objectives"][0] if focus_day_item["objectives"] else "implement the module"
            
            if total_questions == 0:
                if is_senior:
                    reply = f"Welcome! Let's start with your background on Day {current_day} ({title}). As a senior engineer with {years_exp} years of experience, you worked with {tools_str} to {objective_sample}. Can you describe the architectural design choices and production tradeoffs you made for what you built?"
                else:
                    reply = f"Welcome! Let's start with your background on Day {current_day} ({title}). In this module, you worked with {tools_str} to {objective_sample}. Can you explain what this module was about in your own words, and what you built?"
            else:
                if is_senior:
                    reply = f"Let's move on to Day {current_day}: {title}. Under this topic, you utilized {tools_str} to {objective_sample}. Given your professional background in scaling systems, can you explain how you designed this component to ensure production reliability, and how you compared it to industry alternatives?"
                else:
                    reply = f"Let's move on to Day {current_day}: {title}. Under this topic, you utilized {tools_str} to {objective_sample}. Can you walk me through the step-by-step logic you used to design this component?"
                
            return {
                "internal_evaluation": None,
                "reply": reply,
                "done": False,
                "focus_day": current_day,
                "feedback": None
            }

    # Formulate plan details for prompt
    plan_details_list = []
    for item in plan:
        plan_details_list.append(
            f"- Day {item['day']} ({item['type'].upper()}): {item['title']}\n"
            f"  Reason: {item['reason']}\n"
            f"  Tools: {', '.join(item['tools'])}\n"
            f"  Objectives:\n  " + "\n  ".join([f"* {obj}" for obj in item['objectives']])
        )
    plan_details = "\n".join(plan_details_list)

    # Format the system prompt
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        candidate_name=candidate.get("member", {}).get("name", "Candidate"),
        candidate_role=candidate.get("member", {}).get("jobRole", "Software Engineer"),
        candidate_years_experience=candidate.get("member", {}).get("yearsExperience", 0),
        candidate_education=candidate.get("member", {}).get("education", "CS Graduate"),
        plan_details=plan_details,
        questions_asked=questions_asked,
        days_covered_list=", ".join([f"Day {d}" for d in days_covered]) if days_covered else "None yet",
    )

    # Format messages for Gemini API
    gemini_messages = []
    for msg in history:
        # Map user/assistant to Gemini roles
        role = "user" if msg["role"] == "user" else "model"
        gemini_messages.append({
            "role": role,
            "parts": [msg["content"]]
        })

    # If the history is empty, add a starting prompt to kick off the conversation
    if not gemini_messages:
        gemini_messages.append({
            "role": "user",
            "parts": ["Hi, I am ready to start the interview."]
        })

    try:
        # Configure Google GenAI SDK
        genai.configure(api_key=api_key)
        
        # Initialize model with system instruction and JSON output constraint
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.7,
                "response_mime_type": "application/json"
            },
            system_instruction=system_prompt
        )
        
        response = await model.generate_content_async(contents=gemini_messages)
        
        raw_content = response.text
        logger.info(f"Raw LLM response: {raw_content}")
        
        parsed_response = extract_json(raw_content)
        return parsed_response
        
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        # Return a fallback JSON response on error
        return {
            "reply": "I'm sorry, I encountered a technical issue. Let's continue. Can you tell me more about your recent project?",
            "done": False,
            "focus_day": None,
            "feedback": None
        }

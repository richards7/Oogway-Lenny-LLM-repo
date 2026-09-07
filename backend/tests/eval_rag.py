import os
import sys
import httpx
import json
import uuid
import time
from typing import Dict, List, Any

# Environment & Config
BASE_URL = "http://localhost:5001"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY environment variable is not set.")
    sys.exit(1)

# The Evaluation Dataset
DATASET = [
    "What is Product-Led Growth?",
    "How does Brian Chesky define Founder Mode?",
    "What are the core principles of Empowered Product Teams according to Marty Cagan?"
]

JUDGE_PROMPT_TEMPLATE = """
You are an expert AI evaluator grading a Retrieval-Augmented Generation (RAG) system.
You will be provided with a QUESTION, the RETRIEVED CONTEXT, and the GENERATED ANSWER.
Your task is to grade the GENERATED ANSWER based on two metrics:

1. RELEVANCE (0 or 1): Does the GENERATED ANSWER directly address and answer the QUESTION?
2. FAITHFULNESS (0 or 1): Is the GENERATED ANSWER strictly grounded in the RETRIEVED CONTEXT? It should not contain hallucinations or external information not present in the context.

Respond ONLY with a JSON object in the following format, with no markdown formatting or extra text:
{{"relevance": 1, "faithfulness": 1, "reasoning": "Brief explanation here"}}

QUESTION: {question}

RETRIEVED CONTEXT:
{context}

GENERATED ANSWER:
{answer}
"""

def query_rag_system(question: str) -> tuple[str, str]:
    """Queries the local RAG backend and returns the generated answer and retrieved context."""
    print(f"\n[1] Querying App: '{question}'...")
    try:
        # Create a session
        session_res = httpx.post(f"{BASE_URL}/sessions", json={}, timeout=10.0)
        session_res.raise_for_status()
        session_id = session_res.json()["session_id"]
        
        # Send message
        payload = {"content": question}
        msg_res = httpx.post(f"{BASE_URL}/sessions/{session_id}/messages", json=payload, timeout=120.0)
        msg_res.raise_for_status()
        data = msg_res.json()
        
        answer = data.get("content", "")
        citations = data.get("citations", [])
        
        # Compile retrieved context
        context_snippets = "\n".join([f"- {c['snippet']}" for c in citations])
        return answer, context_snippets
    except Exception as e:
        print(f"❌ Error querying local app: {e}")
        return "", ""

def evaluate_with_judge(question: str, context: str, answer: str) -> Dict[str, Any]:
    """Uses Gemini API directly to evaluate the response."""
    print(f"[2] Asking Judge LLM to evaluate...")
    
    prompt = JUDGE_PROMPT_TEMPLATE.format(question=question, context=context, answer=answer)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json"
        }
    }
    
    try:
        res = httpx.post(url, json=payload, timeout=60.0)
        res.raise_for_status()
        response_data = res.json()
        
        # Extract the text response
        text_output = response_data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text_output)
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        return {"relevance": 0, "faithfulness": 0, "reasoning": f"Eval failed: {e}"}

def run_evaluation():
    print("========================================")
    print("🚀 STARTING RAG EVALUATION SUITE")
    print("========================================")
    
    total_relevance = 0
    total_faithfulness = 0
    
    for idx, question in enumerate(DATASET, 1):
        print(f"\n--- Test Case {idx}/{len(DATASET)} ---")
        answer, context = query_rag_system(question)
        if not answer:
            print("Skipping evaluation due to empty answer.")
            continue
            
        evaluation = evaluate_with_judge(question, context, answer)
        
        relevance = evaluation.get("relevance", 0)
        faithfulness = evaluation.get("faithfulness", 0)
        reasoning = evaluation.get("reasoning", "No reasoning provided.")
        
        total_relevance += relevance
        total_faithfulness += faithfulness
        
        print(f"✅ Grades Received:")
        print(f"  - Relevance:    {'PASS' if relevance == 1 else 'FAIL'}")
        print(f"  - Faithfulness: {'PASS' if faithfulness == 1 else 'FAIL'}")
        print(f"  - Reasoning:    {reasoning}")
        time.sleep(1) # Prevent rate limiting
        
    print("\n========================================")
    print("📊 FINAL EVALUATION SCORECARD")
    print("========================================")
    n = len(DATASET)
    print(f"Average Relevance:    {(total_relevance/n)*100:.1f}%")
    print(f"Average Faithfulness: {(total_faithfulness/n)*100:.1f}%")

if __name__ == "__main__":
    run_evaluation()

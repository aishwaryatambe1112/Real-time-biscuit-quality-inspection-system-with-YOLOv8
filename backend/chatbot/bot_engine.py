"""
=============================================================
BiscuitAI Chatbot — Bot Engine (Groq Version)
=============================================================
Uses Groq API with llama-3.1-8b-instant:
  - Completely FREE
  - 30 requests per minute
  - 14,400 requests per day
  - ~500ms response time (very fast)

Zero hallucinations: only answers from retrieved context.
=============================================================
"""

import os
import sys
import time
from groq import Groq
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.chatbot.knowledge_base import retrieve_context

# ── Groq client ────────────────────────────────────────────
_client = None

def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in .env file")
        _client = Groq(api_key=api_key)
    return _client


# ── System prompt ──────────────────────────────────────────
SYSTEM_PROMPT = """You are BiscuitBot, the official AI assistant for the Real-Time Biscuit Quality Inspection System (BiscuitAI) — a final year B.Tech project that uses YOLOv8m deep learning to inspect biscuit quality in real-time.

YOUR ROLE:
- Answer questions about the BiscuitAI project, its tech stack, architecture, and usage
- Guide users on how to set up and use the system
- Explain AI/ML concepts used in the project clearly
- Help with troubleshooting common issues

STRICT RULES:
1. ONLY answer based on the CONTEXT provided below. Do not use outside knowledge.
2. If the answer is NOT in the context, say: "I don't have that information in my knowledge base. Please check the README or raise an issue on GitHub."
3. NEVER make up facts, file names, commands, or technical details not in the context.
4. Keep answers concise but complete. Use bullet points for multi-step answers.
5. For commands, use code blocks.
6. Be friendly, professional, and encouraging.
7. You are visible on the home page before login — greet new users warmly.
8. If asked who built this, say it was built as a final year B.Tech project.
9. When explaining tech stack choices, explain the WHY not just the what.
10. Do not answer questions unrelated to BiscuitAI or its tech stack."""


# ── Conversation history ───────────────────────────────────
MAX_HISTORY_TURNS = 6

class ChatSession:
    def __init__(self):
        self.history: list[dict] = []

    def add_turn(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > MAX_HISTORY_TURNS * 2:
            self.history = self.history[-(MAX_HISTORY_TURNS * 2):]

    def get_messages(self, user_message: str) -> list[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_message})
        return messages


# ── Global session store ───────────────────────────────────
_sessions: dict[str, ChatSession] = {}

def _get_session(session_id: str) -> ChatSession:
    if session_id not in _sessions:
        _sessions[session_id] = ChatSession()
    return _sessions[session_id]

def clear_session(session_id: str):
    if session_id in _sessions:
        del _sessions[session_id]


# ── Main chat function ─────────────────────────────────────
def chat(user_query: str, session_id: str = "default") -> dict:
    start = time.time()

    # 1. Retrieve relevant context from ChromaDB
    try:
        context_chunks = retrieve_context(user_query, n_results=4)
    except Exception as e:
        return {
            "answer":     "I'm having trouble accessing my knowledge base. Please try again.",
            "latency_ms": int((time.time() - start) * 1000),
            "error":      str(e)
        }

    if not context_chunks:
        return {
            "answer":     "I don't have enough information to answer that. Please check the README.",
            "latency_ms": int((time.time() - start) * 1000),
            "error":      None
        }

    # 2. Build prompt with retrieved context
    context_text = "\n\n---\n\n".join(context_chunks)
    prompt_with_context = f"""CONTEXT FROM KNOWLEDGE BASE:
{context_text}

---

USER QUESTION: {user_query}

Answer strictly based on the context above. If the context does not contain the answer, say so clearly."""

    # 3. Get session and call Groq
    session = _get_session(session_id)
    messages = session.get_messages(prompt_with_context)

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model       = "llama-3.1-8b-instant",
            messages    = messages,
            max_tokens  = 1024,
            temperature = 0.3,
        )

        answer = response.choices[0].message.content.strip()

        session.add_turn("user",      user_query)
        session.add_turn("assistant", answer)

        return {
            "answer":     answer,
            "latency_ms": int((time.time() - start) * 1000),
            "error":      None
        }

    except Exception as e:
        err_str = str(e)
        if "rate_limit" in err_str.lower() or "429" in err_str:
            return {
                "answer":     "Please wait a moment and try again.",
                "latency_ms": int((time.time() - start) * 1000),
                "error":      "rate_limit"
            }
        if "api_key" in err_str.lower() or "authentication" in err_str.lower() or "401" in err_str:
            return {
                "answer":     "Invalid API key. Please check GROQ_API_KEY in the .env file.",
                "latency_ms": int((time.time() - start) * 1000),
                "error":      "auth_error"
            }
        return {
            "answer":     "I encountered an unexpected error. Please try again.",
            "latency_ms": int((time.time() - start) * 1000),
            "error":      err_str
        }


# ── Suggested starter questions ────────────────────────────
STARTER_QUESTIONS = [
    "What is BiscuitAI and what does it do?",
    "Which biscuit brands and defects does it detect?",
    "Why was YOLOv8m chosen over YOLOv8n or YOLOv8s?",
    "How does the stability buffer prevent false positives?",
    "How do I set up and run this project?",
    "What is RAG and how is it used in this chatbot?",
    "How does Python threading work in the detection engine?",
    "What is the batch workflow for inspecting biscuits?",
]

def get_starter_questions() -> list[str]:
    return STARTER_QUESTIONS


# ── CLI test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 56)
    print("  BiscuitBot — CLI Test (Groq llama-3.1-8b-instant)")
    print("=" * 56)
    print("Type 'quit' to exit\n")
    while True:
        query = input("You: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        result = chat(query, session_id="cli_test")
        print(f"\nBot ({result['latency_ms']}ms): {result['answer']}\n")
        if result["error"]:
            print(f"[ERROR] {result['error']}\n")
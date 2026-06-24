import os
import json
import httpx
import asyncio
import time
import nest_asyncio
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
nest_asyncio.apply()  # Allows nested event loops — prevents crash on Render/production

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

GROQ_URL           = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"

GROQ_MODEL         = "llama-3.1-8b-instant"
GROQ_MODEL_70B     = "llama-3.3-70b-versatile"  # 131K context, used for concept extraction
OPENROUTER_MODEL   = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"


# ─────────────────────────────────────────────────────────────
# RATE LIMITER — prevents Groq 429 errors
# ─────────────────────────────────────────────────────────────

class _RateLimiter:
    """
    Simple rate limiter for API calls.
    Ensures we never exceed Groq's 30 requests/minute limit.
    Uses 25 req/min for safety buffer.
    """
    def __init__(self, calls_per_minute: int = 25):
        self.min_interval = 60.0 / calls_per_minute  # ~2.4 seconds
        self.last_call_time = 0.0

    async def wait(self):
        now = time.monotonic()
        elapsed = now - self.last_call_time
        wait_time = self.min_interval - elapsed
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self.last_call_time = time.monotonic()

    def wait_sync(self):
        now = time.monotonic()
        elapsed = now - self.last_call_time
        wait_time = self.min_interval - elapsed
        if wait_time > 0:
            time.sleep(wait_time)
        self.last_call_time = time.monotonic()


# Shared limiters
_groq_limiter = _RateLimiter(calls_per_minute=25)
_openrouter_limiter = _RateLimiter(calls_per_minute=20)


# ─────────────────────────────────────────────────────────────
# CORE API CALLER — GROQ (with rate limiting + 429 retry)
# ─────────────────────────────────────────────────────────────

async def _call_groq(messages: list, max_tokens: int = 500, temperature: float = 0.3) -> str:
    """Calls Groq API with rate limiting. Retries once on 429."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env")

    await _groq_limiter.wait()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=30
        )

        # Handle rate limit — wait and retry once
        if response.status_code == 429:
            print("[Groq] Rate limited — waiting 15s and retrying...")
            await asyncio.sleep(15)
            _groq_limiter.last_call_time = time.monotonic()
            response = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=30
            )

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


# ─────────────────────────────────────────────────────────────
# CORE API CALLER — GROQ 70B (for concept extraction)
# ─────────────────────────────────────────────────────────────

async def _call_groq_70b(messages: list, max_tokens: int = 500, temperature: float = 0.1) -> str:
    """
    Calls Groq API with the 70B model (llama-3.3-70b-versatile).
    Used for concept extraction — needs the larger model for better
    instruction-following and semantic understanding.

    Uses lower temperature (0.1) for deterministic concept extraction
    and longer timeout (60s) for processing large transcripts.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env")

    await _groq_limiter.wait()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL_70B,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=60  # longer timeout for large transcripts
        )

        # Handle rate limit — wait and retry once
        if response.status_code == 429:
            print("[Groq-70B] Rate limited — waiting 15s and retrying...")
            await asyncio.sleep(15)
            _groq_limiter.last_call_time = time.monotonic()
            response = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL_70B,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=60
            )

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


# ─────────────────────────────────────────────────────────────
# CORE API CALLER — OPENROUTER (NVIDIA NEMOTRON)
# ─────────────────────────────────────────────────────────────

async def _call_openrouter(messages: list, max_tokens: int = 200) -> str:
    """
    Calls OpenRouter API using NVIDIA Nemotron free model.
    Used for: relevance checks only. Rate limited.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set in .env")

    await _openrouter_limiter.wait()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://evaluator.app",
                "X-Title": "Evaluator 2.0"
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.1
            },
            timeout=40
        )
        response.raise_for_status()
        data = response.json()

        message = data["choices"][0]["message"]

        # Try all possible fields Nemotron might use
        content = (
            message.get("content")              # standard OpenAI format
            or message.get("reasoning_content")  # Nemotron-specific
            or message.get("reasoning")           # some reasoning models
            or ""
        )

        if content and content.strip():
            return content.strip()

        raise ValueError(f"Empty response from Nemotron. Full message: {message}")


# ─────────────────────────────────────────────────────────────
# 1. RELEVANCE CHECK  →  OpenRouter (NVIDIA Nemotron free)
# ─────────────────────────────────────────────────────────────

async def _check_relevance_async(
    submission: str, problem_statement: str
) -> dict:
    prompt = f"""You are an academic evaluator checking if a student submission answers the problem.

Problem Statement:
{problem_statement}

Student Submission (first 1000 characters):
{submission[:1000]}

Reply with ONLY a JSON object:
{{"verdict": "RELEVANT", "reason": "brief one-line reason"}}

Rules for verdict:
- RELEVANT   → submission clearly answers the problem
- PARTIAL    → submission is related but incomplete
- UNCERTAIN  → cannot determine relevance confidently
- IRRELEVANT → submission is completely unrelated"""

    try:
        raw = await _call_openrouter(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        raw = raw.replace("```json", "").replace("```", "").strip()
        # Normalize whitespace/newlines inside JSON
        raw = " ".join(raw.split())

        start = raw.find("{")
        end   = raw.rfind("}") + 1

        if start != -1 and end > start:
            json_str = raw[start:end]
            parsed  = json.loads(json_str)
            verdict = parsed.get("verdict", "UNCERTAIN").upper().strip()
            if verdict not in ["RELEVANT", "PARTIAL", "UNCERTAIN", "IRRELEVANT"]:
                verdict = "UNCERTAIN"
            return {"verdict": verdict, "reason": parsed.get("reason", "")}

        # Regex fallback — look for verdict keyword
        import re
        match = re.search(r'"verdict"\s*:\s*"(RELEVANT|PARTIAL|UNCERTAIN|IRRELEVANT)"', raw, re.IGNORECASE)
        if match:
            return {"verdict": match.group(1).upper(), "reason": "Parsed from partial response"}

        print(f"[OpenRouter] Could not extract JSON from: {raw[:200]}")
        return {"verdict": "UNCERTAIN", "reason": "Could not parse model response"}

    except httpx.TimeoutException:
        print("[OpenRouter] Request timed out — returning UNCERTAIN")
        return {"verdict": "UNCERTAIN", "reason": "Request timed out"}
    except Exception as e:
        print(f"[OpenRouter] Relevance check failed: {e}")
        return {"verdict": "UNCERTAIN", "reason": "LLM unavailable"}


# ─────────────────────────────────────────────────────────────
# 2. FEEDBACK GENERATION  →  Groq (llama-3.1-8b-instant)
# ─────────────────────────────────────────────────────────────

async def _generate_feedback_async(
    submission: str,
    problem_statement: str,
    score: float,
    assignment_type: str = "code",
    matched_concepts: list = None,
    missing_concepts: list = None,
    word_count: int = 0,
    depth_score: float = 0,
) -> str:
    system_msg = """You are a university professor writing brief, personal feedback on a student's work. Your tone is warm but honest. You write in plain sentences — no bullet points, no numbered lists, no section headers, no emoji, no markdown formatting.

CRITICAL RULES:
- You MUST reference the specific topics this student covered and missed (provided below). Do NOT use generic phrases.
- Every student's feedback must be different. Focus on THEIR specific gaps and strengths.
- Never start with "I was impressed" or "Great job" — start by directly addressing what you noticed in their specific content.
- Do NOT repeat the score. The score is already shown separately.
- Write as if you're leaving a handwritten note on their paper."""

    # Build student-specific context
    context_parts = []
    if matched_concepts:
        context_parts.append(f"Topics this student covered well: {', '.join(matched_concepts[:8])}")
    if missing_concepts:
        context_parts.append(f"Topics this student MISSED: {', '.join(missing_concepts[:8])}")
    if word_count:
        context_parts.append(f"Word count: {word_count}")
    if depth_score:
        context_parts.append(f"Depth of explanation: {depth_score:.0f}/100")

    student_context = "\n".join(context_parts) if context_parts else "No specific concept data available."

    user_msg = f"""Assignment: "{problem_statement}"

STUDENT-SPECIFIC DATA:
{student_context}

--- STUDENT'S SUBMISSION ---
{submission[:800]}
--- END ---

Write 3-4 sentences of feedback for THIS specific student. You must:
1. Mention at least one specific topic they missed (from the missing list above) and briefly say WHY it matters.
2. Acknowledge something specific from their actual writing (quote or reference a phrase they used).
3. Give one concrete suggestion for how they can improve their next submission.

Keep it under 120 words. Write in second person ("you"). No emoji, no markdown, no formatting."""

    try:
        return await _call_groq(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=300,
            temperature=0.5
        )
    except Exception as e:
        print(f"[Groq] Feedback generation failed: {e}")
        return _rule_based_feedback(score, assignment_type)


# ─────────────────────────────────────────────────────────────
# 3. CHATBOT  →  Groq (llama-3.1-8b-instant)
# ─────────────────────────────────────────────────────────────

async def chat_with_student(
    conversation_history: list,
    system_prompt: str = None
) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    else:
        messages.append({
            "role": "system",
            "content": (
                "You are a helpful academic assistant for students using the Evaluator platform. "
                "You help students understand their scores, improve their code, and learn concepts. "
                "Keep responses clear, concise, and student-friendly. "
                "If asked about scores or feedback, explain them in simple terms. "
                "For programming questions, give short code examples when helpful."
            )
        })
    messages.extend(conversation_history)

    try:
        return await _call_groq(messages=messages, max_tokens=500)
    except Exception as e:
        print(f"[Groq] Chatbot failed: {e}")
        return "I'm having trouble connecting right now. Please try again in a moment."


# ─────────────────────────────────────────────────────────────
# 4. RULE-BASED FALLBACK  →  No API needed
# ─────────────────────────────────────────────────────────────

def _rule_based_feedback(score: float, assignment_type: str) -> str:
    """Conversational fallback when Groq is unavailable."""
    if score >= 80:
        return (
            "Your submission shows a solid understanding of the problem and a well-structured approach. "
            "The core logic is implemented correctly, which is great to see. "
            "To push this further, consider adding inline comments explaining your reasoning, "
            "and think about how your solution handles edge cases. Keep up the excellent work!"
        )
    elif score >= 60:
        return (
            "You've made a decent attempt here and clearly understand the core concept. "
            "Some parts of your implementation could use more attention — re-read the problem "
            "statement carefully and make sure every requirement is addressed. "
            "Testing with a few edge cases will help you catch the gaps. You're on the right track."
        )
    elif score >= 40:
        return (
            "I can see you've put effort into this, but the core approach needs some rework. "
            "Try starting with the simplest possible solution that works, then build from there. "
            "Make sure your output format matches exactly what's expected. "
            "Don't hesitate to look at similar examples for reference — that's how we all learn."
        )
    else:
        return (
            "This submission doesn't quite address the problem as stated. "
            "Take another look at the requirements and try to break the problem into smaller steps. "
            "Focus on getting a basic version working first — even a partial solution that handles "
            "the main case is a great starting point. You've got this, just give it another shot."
        )


# ─────────────────────────────────────────────────────────────
# LLMService CLASS WRAPPER
# (backward-compatible with existing agents that use LLMService)
# ─────────────────────────────────────────────────────────────

class LLMService:
    """
    Class wrapper for backward compatibility.
    Agents call: self.llm_service.check_relevance(...)
    """

    def __init__(self):
        self.enabled = os.getenv("LLM_ENABLED", "false").lower() == "true"

    def check_relevance(
        self,
        problem_statement: str,
        submission_content: str,
        context_type: str = "code"
    ) -> dict:
        """Synchronous relevance check — wraps async call."""
        if not self.enabled:
            return {"verdict": "UNCERTAIN", "reason": "LLM disabled"}

        try:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    _check_relevance_async(submission_content, problem_statement)
                )
            finally:
                loop.close()
        except Exception as e:
            print(f"[LLMService] check_relevance error: {e}")
            return {"verdict": "UNCERTAIN", "reason": str(e)}

    def generate_semantic_feedback(
        self,
        submission: str = "",
        problem_statement: str = "",
        score: float = 0,
        assignment_type: str = "code",
        # Old-style keyword args from agents:
        context_type: str = "",
        submission_content: str = "",
        rubric_context: str = "",
        deterministic_findings: list = None,
        missing_concepts: list = None,
        matched_concepts: list = None,
        word_count: int = 0,
        depth_score: float = 0,
        **kwargs
    ) -> str:
        """Synchronous feedback generation — wraps async call.
        
        Accepts both new-style (submission, problem_statement, score) and
        old-style (submission_content, rubric_context, deterministic_findings) args.
        """
        if not self.enabled:
            fb = _rule_based_feedback(score, assignment_type or context_type or "code")
            return [fb] if isinstance(fb, str) else fb

        # Normalize: old callers use submission_content, new callers use submission
        actual_submission = submission_content or submission
        actual_type = context_type or assignment_type

        # Build a combined problem context from rubric + deterministic findings
        problem_parts = []
        if problem_statement:
            problem_parts.append(problem_statement)
        if rubric_context:
            problem_parts.append(f"Rubric: {rubric_context[:300]}")
        
        combined_problem = "\n".join(problem_parts) if problem_parts else "General evaluation"

        try:
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(
                    _generate_feedback_async(
                        actual_submission,
                        combined_problem,
                        score,
                        actual_type,
                        matched_concepts=matched_concepts or [],
                        missing_concepts=missing_concepts or [],
                        word_count=word_count,
                        depth_score=depth_score,
                    )
                )
            finally:
                loop.close()
            # Agents expect a list of strings — wrap if needed
            if isinstance(result, str):
                return [result]
            return result
        except Exception as e:
            print(f"[LLMService] generate_semantic_feedback error: {e}")
            fb = _rule_based_feedback(score, actual_type)
            return [fb] if isinstance(fb, str) else fb


"""
AI Study Coach — Streaming chat endpoint for students.

Uses Groq (llama-3.1-8b-instant) for personalized study guidance
based on the student's evaluation history.
Streams responses token-by-token via Server-Sent Events (SSE).
"""

import json
import httpx
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.app.middleware.auth import require_student, TokenPayload
from backend.core.services.database import get_db
from backend.core.services.student_tracker import (
    get_score_history,
    get_skill_breakdown,
    get_class_percentile,
    get_student_summary,
)

load_dotenv()

router = APIRouter(prefix="/api/portal", tags=["student-coach"])

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"


# ---------------------------------------------------------------------------
# Request / helpers
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []


def _resolve_db_student_id(login_id: str) -> str:
    """Resolve login username to DB student_id (handles _Result suffix)."""
    db = get_db()
    if not db.available:
        return login_id
    for candidate in [login_id, f"{login_id}_Result"]:
        row = db.execute_one(
            "SELECT student_id FROM student_scores WHERE student_id = %s LIMIT 1",
            [candidate],
        )
        if row:
            return row["student_id"]
    row = db.execute_one(
        "SELECT student_id FROM student_scores WHERE student_id LIKE %s LIMIT 1",
        [f"{login_id}%"],
    )
    return row["student_id"] if row else login_id


def _build_student_context(login_id: str) -> str:
    """Build a rich context string from the student's evaluation data."""
    db_id = _resolve_db_student_id(login_id)
    summary = get_student_summary(db_id)
    history = get_score_history(db_id, limit=5)
    skills = get_skill_breakdown(db_id)
    rank = get_class_percentile(db_id)

    lines = [f"Student: {login_id}"]

    if summary.get("total_submissions", 0) > 0:
        lines.append(f"Total submissions: {summary['total_submissions']}")
        lines.append(f"Average score: {summary['average_score']:.1f}/100")
        lines.append(f"Best: {summary['best_score']:.1f}, Worst: {summary['worst_score']:.1f}")
        lines.append(f"Grade: {summary['cumulative_grade']} (GPA {summary['gpa']:.2f})")

    if rank.get("percentile"):
        lines.append(f"Class percentile: {rank['percentile']}th out of {rank.get('class_size', '?')} students")

    if skills:
        strong = sorted(skills, key=lambda s: s.get("avg_score", 0), reverse=True)
        lines.append("Topic scores: " + ", ".join(
            f"{s['topic_tag']}: {s['avg_score']:.0f}" for s in strong[:5]
        ))

    if history:
        lines.append("Recent submissions:")
        for h in history[:3]:
            lines.append(f"  - {h.get('assignment_id', 'assignment')} ({h.get('topic_tag', 'general')}): {h['score']:.1f}/100")

    # Pull recent feedback from evaluation_results
    db = get_db()
    if db.available:
        all_ids = [login_id, f"{login_id}_Result", db_id]
        placeholders = ", ".join(["%s"] * len(set(all_ids)))
        rows = db.execute(
            f"""SELECT feedback, final_score, file
               FROM evaluation_results
               WHERE submission_id IN ({placeholders})
               ORDER BY evaluated_at DESC LIMIT 2""",
            list(set(all_ids)),
        )
        if rows:
            lines.append("Recent AI feedback on submissions:")
            for r in rows:
                fb = r.get("feedback", "")
                if isinstance(fb, str):
                    try:
                        fb = json.loads(fb)
                    except Exception:
                        pass
                if isinstance(fb, list):
                    fb = " ".join(fb)
                if fb:
                    lines.append(f"  [{r.get('file', '?')} — {r.get('final_score', '?')}/100]: {str(fb)[:300]}")

    return "\n".join(lines)


SYSTEM_PROMPT = """You are an AI Study Coach for a student in Evaluator 2.0.

CRITICAL RULES:
- Use ONLY the student data provided below. NEVER invent fake names, scores, topics, or grades.
- If no data is available, say "I don't have enough data yet" instead of making things up.
- The student's ID is shown in the context below — use that, not a made-up name.

Your role:
- Answer any question the student asks — academic, coding, career, study strategies
- Give personalized advice using the ACTUAL scores and feedback shown below
- Create study plans with day-by-day breakdowns when asked
- Be encouraging but honest about areas needing improvement
- Use markdown: **bold**, bullet points, `code` for code references
- Keep responses focused (2-4 paragraphs for general questions, longer for plans)

Student context (USE THESE EXACT VALUES):
{context}
"""


# ---------------------------------------------------------------------------
# SSE Streaming endpoint — using Groq
# ---------------------------------------------------------------------------

async def _stream_groq(messages: list, max_tokens: int = 512):
    """Stream tokens from Groq's chat completions endpoint."""
    if not GROQ_API_KEY:
        yield "AI Coach requires GROQ_API_KEY to be set in .env"
        return

    async with httpx.AsyncClient() as client:
        try:
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
                    "temperature": 0.6,
                    "stream": True
                },
                timeout=60
            )
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    token = delta.get("content", "")
                    if token:
                        yield token
                except json.JSONDecodeError:
                    continue

        except Exception as e:
            yield f"\n\n_[Connection error: {e}]_"


@router.post("/chat")
async def student_chat(
    body: ChatRequest,
    user: TokenPayload = Depends(require_student),
):
    """Stream AI study coach response via Server-Sent Events (Groq)."""
    login_id = user.student_id
    if not login_id:
        raise HTTPException(400, "Student ID not found in token")

    message = body.message.strip()
    if not message:
        raise HTTPException(400, "Message cannot be empty")

    if not GROQ_API_KEY:
        raise HTTPException(
            503,
            "AI Coach requires GROQ_API_KEY to be set in .env file.",
        )

    # Build context from student data
    context = _build_student_context(login_id)
    system = SYSTEM_PROMPT.format(context=context)

    # Build messages list
    messages = [{"role": "system", "content": system}]

    # Include conversation history (last 6 messages)
    history = body.conversation_history[-6:]
    for h in history:
        messages.append({
            "role": h.get("role", "user"),
            "content": h.get("content", "")[:300]
        })
    messages.append({"role": "user", "content": message})

    async def event_stream():
        async for token in _stream_groq(messages):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Structured improvement plan (non-streaming)
# ---------------------------------------------------------------------------

def _build_improvement_plan_prompt(login_id: str) -> str:
    """Build an improvement plan prompt with REAL data pre-filled."""
    db_id = _resolve_db_student_id(login_id)
    summary = get_student_summary(db_id)
    skills = get_skill_breakdown(db_id)
    history = get_score_history(db_id, limit=5)
    rank = get_class_percentile(db_id)

    total = summary.get("total_submissions", 0)
    avg = summary.get("average_score", 0)
    grade = summary.get("cumulative_grade", "N/A")
    gpa = summary.get("gpa", 0)
    percentile = rank.get("percentile", "N/A")
    class_size = rank.get("class_size", "?")

    topic_lines = []
    if skills:
        sorted_skills = sorted(skills, key=lambda s: s.get("avg_score", 0))
        for i, s in enumerate(sorted_skills, 1):
            topic_lines.append(f"{i}. {s['topic_tag']} — current score: {s['avg_score']:.0f}/100 ({s.get('submission_count', 0)} submissions)")
    else:
        topic_lines.append("1. General — current score: {:.0f}/100".format(avg))

    recent_lines = []
    if history:
        for h in history[:3]:
            recent_lines.append(f"- {h.get('topic_tag', 'general')}: {h['score']:.0f}/100 on {str(h.get('submitted_at', ''))[:10]}")

    feedback_snippet = ""
    db = get_db()
    if db.available:
        all_ids = list(set([login_id, f"{login_id}_Result", db_id]))
        placeholders = ", ".join(["%s"] * len(all_ids))
        rows = db.execute(
            f"""SELECT feedback FROM evaluation_results
               WHERE submission_id IN ({placeholders})
               ORDER BY evaluated_at DESC LIMIT 1""",
            all_ids,
        )
        if rows:
            fb = rows[0].get("feedback", "")
            if isinstance(fb, str):
                try:
                    fb = json.loads(fb)
                except Exception:
                    pass
            if isinstance(fb, list):
                fb = " ".join(str(x) for x in fb)
            feedback_snippet = str(fb)[:400]

    prompt = f"""Create a 2-week improvement plan for this student. Use ONLY the data provided below.

STUDENT DATA:
- Student ID: {login_id}
- Total submissions: {total}
- Average score: {avg:.1f}/100
- Grade: {grade} | GPA: {gpa:.2f}
- Class rank: {percentile}th percentile out of {class_size} students

TOPIC SCORES (weakest first):
{chr(10).join(topic_lines)}

RECENT SUBMISSIONS:
{chr(10).join(recent_lines) if recent_lines else "No recent submissions"}

LATEST FEEDBACK:
{feedback_snippet if feedback_snippet else "No feedback available"}

---

Write the improvement plan in this format:

**Improvement Plan for {login_id}**
**Current Status:** {grade} | GPA {gpa:.2f} | {percentile}th percentile

**Priority Areas (weakest → strongest):**
{chr(10).join(topic_lines)}

**Week 1: Foundation Building**
(Day-by-day plan with checkboxes targeting weakest topics. Include specific exercises.)

**Week 2: Skill Deepening**
(Continue with harder exercises and self-tests.)

**Key Resources:**
(3-4 specific free online resources relevant to the topics above.)

**Target Goals:**
(Realistic score improvement targets based on current scores.)
"""
    return prompt


@router.post("/improvement-plan")
async def generate_improvement_plan(
    user: TokenPayload = Depends(require_student),
):
    """Generate a structured improvement plan via Groq (streamed)."""
    login_id = user.student_id
    if not login_id:
        raise HTTPException(400, "Student ID not found in token")

    if not GROQ_API_KEY:
        raise HTTPException(503, "GROQ_API_KEY is not set in .env")

    prompt = _build_improvement_plan_prompt(login_id)
    system = "You are an expert academic coach. Use ONLY the student data provided. Never invent fake names or scores. Use markdown formatting with checkboxes."

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]

    async def event_stream():
        async for token in _stream_groq(messages, max_tokens=1024):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/status")
def chat_status(user: TokenPayload = Depends(require_student)):
    """Check if the AI coach backend (Groq) is available."""
    groq_ok = bool(GROQ_API_KEY)

    return {
        "available": groq_ok,
        "backend": "groq" if groq_ok else "none",
        "model": GROQ_MODEL if groq_ok else "unavailable",
    }

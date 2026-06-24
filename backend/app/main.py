"""
FastAPI application entry point for assignment evaluation system v2.0.

Instructor REST API for evaluating student submissions with:
- Code execution via Judge0
- Tree-sitter unified parsing
- Semantic similarity scoring
- Plagiarism detection
- Human review queue
- Student profile tracking
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# ENV confirmation
LLM_ENABLED = os.getenv("LLM_ENABLED", "false").lower() == "true"
print(f"LLM_ENABLED = {LLM_ENABLED}")

from backend.app.routes import evaluate_router
from backend.app.routes.review_routes import router as review_router
from backend.app.routes.student_routes import router as student_router
from backend.app.routes.auth_routes import router as auth_router
from backend.app.routes.student_portal_routes import router as portal_router
from backend.app.routes.chat_routes import router as chat_router


# ---------------------------------------------------------------------------
# Lifespan: init database on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database schema and seed default accounts on startup."""
    try:
        from backend.core.services.database import init_db
        init_db()
        _seed_default_teacher()
    except Exception as e:
        print(f"⚠ Database initialization skipped: {e}")
    yield


def _seed_default_teacher():
    """Seed a default teacher account if none exists."""
    try:
        from backend.core.services.database import get_db
        from backend.app.middleware.auth import hash_password
        db = get_db()
        if not db.available:
            return
        # Check if any teacher exists
        existing = db.execute_one(
            "SELECT id FROM users WHERE role = 'teacher' LIMIT 1"
        )
        if not existing:
            db.execute(
                """
                INSERT INTO users (id, email, password_hash, role, display_name)
                VALUES (%s, %s, %s, 'teacher', %s)
                ON CONFLICT (email) DO NOTHING
                """,
                ["teacher-001", "teacher", hash_password("teacher"), "Instructor"],
            )
            print("✓ Default teacher account seeded (username: teacher, password: teacher)")
        else:
            print("✓ Teacher account already exists.")
    except Exception as e:
        print(f"⚠ Teacher seeding skipped: {e}")


app = FastAPI(
    title="Assignment Evaluation API",
    description="REST API for evaluating student code and content submissions",
    version="2.0.0",
    lifespan=lifespan,
)

# Build allowed origins list
_frontend_url = os.getenv("FRONTEND_URL", "")
_allowed_origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]
if _frontend_url:
    _allowed_origins.append(_frontend_url)

# CORS middleware (for frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_status = "unknown"
    try:
        from backend.core.services.database import get_db
        db_status = "connected" if get_db().available else "unavailable"
    except Exception:
        db_status = "unavailable"

    return {
        "status": "ok",
        "version": "2.0.0",
        "llm_enabled": LLM_ENABLED,
        "database": db_status,
    }


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Assignment Evaluation API v2.0",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "features": [
            "Judge0 test execution",
            "Tree-sitter parsing",
            "Semantic similarity",
            "Plagiarism detection",
            "Review queue",
            "Student tracking",
        ],
    }


# Include routers
app.include_router(auth_router)
app.include_router(evaluate_router)
app.include_router(review_router)
app.include_router(student_router)
app.include_router(portal_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

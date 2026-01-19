"""
FastAPI application entry point for assignment evaluation system.

Instructor-only REST API for evaluating student submissions.
No authentication, no database.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Step 1: ENV Confirmation
LLM_ENABLED = os.getenv("LLM_ENABLED", "false").lower() == "true"
print(f"LLM_ENABLED = {LLM_ENABLED}")

from backend.app.routes import evaluate_router

app = FastAPI(
    title="Assignment Evaluation API",
    description="REST API for evaluating student code and content submissions",
    version="1.0.0",
)

# CORS middleware (for frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Assignment Evaluation API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Include routers
app.include_router(evaluate_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

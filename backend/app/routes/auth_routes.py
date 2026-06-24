"""
Authentication routes for Evaluator 2.0.

Provides login/register endpoints for teachers and students.
Students can self-register with password = username.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from backend.app.middleware.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    TokenPayload,
)
from backend.core.services.database import get_db


router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    """Login request body."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class RegisterRequest(BaseModel):
    """Student self-registration request."""
    username: str = Field(..., description="Student ID / username")
    email: Optional[str] = Field(default=None, description="Email (optional)")
    display_name: Optional[str] = Field(default=None, description="Display name")


class AuthResponse(BaseModel):
    """Auth response with token."""
    status: str = "success"
    token: str
    user: dict


# ---------------------------------------------------------------------------
# Helper: ensure user exists or create on-the-fly
# ---------------------------------------------------------------------------

def _get_or_create_student(username: str, password: str) -> Optional[dict]:
    """
    Get a student user by username, or auto-create one.
    
    For MVP: any student can login. If the username exists, verify password.
    If it doesn't exist, create with password = username.
    """
    db = get_db()
    if not db.available:
        return None

    # Check if user exists
    row = db.execute_one(
        "SELECT * FROM users WHERE email = %s OR student_id = %s",
        [username, username],
    )

    if row:
        # User exists — verify password
        user = dict(row)
        if verify_password(password, user["password_hash"]):
            return user
        return None  # Wrong password

    # Auto-create student account (password = username for MVP)
    user_id = uuid.uuid4().hex[:16]
    password_hash = hash_password(password)
    display_name = username.replace("_", " ").replace("-", " ").title()

    db.execute(
        """
        INSERT INTO users (id, email, password_hash, role, student_id, display_name)
        VALUES (%s, %s, %s, 'student', %s, %s)
        """,
        [user_id, username, password_hash, username, display_name],
    )

    return {
        "id": user_id,
        "email": username,
        "role": "student",
        "student_id": username,
        "display_name": display_name,
    }


def _get_teacher(username: str, password: str) -> Optional[dict]:
    """Get teacher user by credentials."""
    db = get_db()
    if not db.available:
        return None

    row = db.execute_one(
        "SELECT * FROM users WHERE (email = %s OR student_id = %s) AND role = 'teacher'",
        [username, username],
    )

    if row:
        user = dict(row)
        if verify_password(password, user["password_hash"]):
            return user
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/login")
def login(body: LoginRequest):
    """
    Login for both teachers and students.
    
    - Teachers: must have a pre-created account
    - Students: auto-created on first login (password = username)
    """
    db = get_db()
    if not db.available:
        raise HTTPException(503, "Database unavailable")

    # First try teacher login
    teacher = _get_teacher(body.username, body.password)
    if teacher:
        token = create_access_token(
            user_id=str(teacher["id"]),
            email=teacher["email"],
            role="teacher",
            display_name=teacher.get("display_name", "Teacher"),
        )
        return AuthResponse(
            token=token,
            user={
                "id": str(teacher["id"]),
                "email": teacher["email"],
                "role": "teacher",
                "display_name": teacher.get("display_name", "Teacher"),
            },
        )

    # Try student login (auto-creates if not exists)
    student = _get_or_create_student(body.username, body.password)
    if student:
        token = create_access_token(
            user_id=str(student["id"]),
            email=student.get("email", body.username),
            role="student",
            student_id=student.get("student_id", body.username),
            display_name=student.get("display_name", body.username),
        )
        return AuthResponse(
            token=token,
            user={
                "id": str(student["id"]),
                "email": student.get("email", body.username),
                "role": "student",
                "student_id": student.get("student_id", body.username),
                "display_name": student.get("display_name", body.username),
            },
        )

    raise HTTPException(401, "Invalid credentials")


@router.get("/me")
def get_me(user: TokenPayload = Depends(get_current_user)):
    """Get current user info from token."""
    return {
        "status": "success",
        "user": {
            "id": user.user_id,
            "email": user.email,
            "role": user.role,
            "student_id": user.student_id,
            "display_name": user.display_name,
        },
    }

"""
JWT-based authentication middleware for Evaluator 2.0.

Provides FastAPI dependencies for:
- Extracting and validating JWT tokens
- Role-based access control (teacher / student)
- Auto-scoping student requests to their own data
"""

import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JWT_SECRET = os.getenv("JWT_SECRET", "evaluator-2-0-dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TokenPayload(BaseModel):
    """Decoded JWT token payload."""
    user_id: str
    email: str
    role: str  # "teacher" or "student"
    student_id: Optional[str] = None  # Only set for students
    display_name: str = ""
    exp: Optional[float] = None


class UserInfo(BaseModel):
    """User information returned to frontend."""
    user_id: str
    email: str
    role: str
    student_id: Optional[str] = None
    display_name: str = ""


# ---------------------------------------------------------------------------
# Password hashing (simple SHA-256 for MVP)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash password with SHA-256. For MVP only — use bcrypt in production."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(plain) == hashed


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def create_access_token(
    user_id: str,
    email: str,
    role: str,
    student_id: Optional[str] = None,
    display_name: str = "",
) -> str:
    """Create a JWT access token."""
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "student_id": student_id,
        "display_name": display_name,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------

def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )


# ---------------------------------------------------------------------------
# FastAPI Dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenPayload:
    """Extract and validate the current user from JWT token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


async def require_teacher(
    user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Require teacher role."""
    if user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required",
        )
    return user


async def require_student(
    user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Require student role."""
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return user

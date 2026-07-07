from fastapi import APIRouter, Depends, HTTPException, status, Form, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# ── Validation helper messages ─────────────────────────────────────
USERNAME_REGEX = r"^[a-zA-Z0-9_]{3,20}$"
PASSWORD_MIN_LENGTH = 8

# ── Register ──────────────────────────────────────────────────────
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
    responses={
        400: {"description": "Validation error or username already taken"},
    },
)
async def register(
    username: str = Form(..., min_length=3, max_length=20),
    password: str = Form(..., min_length=PASSWORD_MIN_LENGTH),
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    - **username**: 3–20 characters, alphanumeric + underscore only.
    - **password**: minimum 8 characters (you can add strength rules).
    """
    # Check if user exists
    # print(f"{username} and {password}")
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Hash password
    hashed = get_password_hash(password)

    # Create user (default role = "user")
    user = User(username=username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully"}


# ── Login ──────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=None,
    responses={
        400: {"description": "Invalid credentials"},
    },
)
async def login(
    response: Response,
    username: str = Form(..., min_length=1),
    password: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
):
    """
    Authenticate user and set JWT cookie.

    - **username**: your username.
    - **password**: your password.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Create JWT token
    token = create_access_token(data={"sub": user.username})

    # Set HTTP‑only cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,          # set to True in production with HTTPS
        samesite="lax",
        path="/",
        max_age=60 * 60 * 24 * 7,  # 7 days (adjust as needed)
    )
    return {"message": "Login successful"}


# ── Get current user ──────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """
    Get the authenticated user's info.
    """
    return user


# ── Logout ─────────────────────────────────────────────────────────
@router.get("/logout")
async def logout(response: Response):
    """
    Clear the access_token cookie.
    """
    response.delete_cookie("access_token")
    return {"message": "Logged out"}
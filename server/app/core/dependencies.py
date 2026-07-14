from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.core.security import decode_token

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Extract JWT from cookie and return the authenticated user.
    Raises 401 if missing/invalid.
    """
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    """
    Ensure the current user has admin privileges.
    Raises 403 if not.
    """
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
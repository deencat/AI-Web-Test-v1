from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.deps import get_db, get_current_active_user
from app.core.config import settings
from app.core.security import create_access_token
from app.core.rate_limit import limiter, STRICT_LIMITS, NORMAL_LIMITS
from app.crud.user import authenticate_user, create_user, get_user_by_username, get_user_by_email, update_user_password
from app.crud.password_reset import (
    create_password_reset_token, 
    get_valid_password_reset_token, 
    mark_token_as_used,
    invalidate_user_tokens
)
from app.crud.user_session import (
    get_user_sessions,
    get_user_session,
    logout_session,
    delete_session
)
from app.schemas.token import Token
from app.schemas.user import User, UserCreate
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)
from app.schemas.user_session import UserSessionResponse, UserSessionListResponse

router = APIRouter()


@router.post("/login", response_model=Token)
@limiter.limit(STRICT_LIMITS)
def login(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login.
    
    Frontend should send:
    - username: string
    - password: string
    
    Rate limited to 10 requests per minute.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout endpoint (stateless JWT - frontend handles token removal).
    """
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
def refresh_token(current_user: User = Depends(get_current_active_user)):
    """
    Refresh access token.
    
    Requires valid existing token. Returns new token with fresh expiration.
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user.
    """
    return current_user


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
@limiter.limit(STRICT_LIMITS)
def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    """
    Register new user.
    
    Rate limited to 10 requests per minute.
    """
    # Check if user already exists
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    return create_user(db, user)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit(STRICT_LIMITS)
def forgot_password(
    request_data: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request password reset token.
    
    Sends password reset email if user exists.
    Returns success message regardless to prevent email enumeration.
    
    Rate limited to 10 requests per minute.
    """
    user = get_user_by_email(db, email=request_data.email)
    
    if user:
        # Invalidate any existing unused tokens
        invalidate_user_tokens(db, user.id)
        
        # Create new reset token
        token = create_password_reset_token(
            db,
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            expires_in_hours=24
        )
        
        # TODO: Send email with reset link
        # reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
        # send_password_reset_email(user.email, reset_link)
        
        return ForgotPasswordResponse(
            message="If the email exists, a password reset link has been sent",
            token_expires_at=token.expires_at
        )
    
    # Return same message to prevent email enumeration
    return ForgotPasswordResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
@limiter.limit(STRICT_LIMITS)
def reset_password(
    request: Request,
    request_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using token.
    
    Validates token and updates user password.
    
    Rate limited to 10 requests per minute.
    """
    # Validate token
    reset_token = get_valid_password_reset_token(db, request_data.token)
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user = update_user_password(db, reset_token.user_id, request_data.new_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mark token as used
    mark_token_as_used(db, reset_token)
    
    # Invalidate all other tokens for this user
    invalidate_user_tokens(db, user.id)
    
    return ResetPasswordResponse(
        message="Password has been reset successfully"
    )


@router.get("/sessions", response_model=UserSessionListResponse)
def get_my_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all sessions for current user.
    """
    sessions = get_user_sessions(db, user_id=current_user.id)
    active_sessions = [s for s in sessions if s.is_valid()]
    
    return UserSessionListResponse(
        sessions=sessions,
        total=len(sessions),
        active_count=len(active_sessions)
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def logout_specific_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout a specific session.
    
    Users can only logout their own sessions.
    """
    session = get_user_session(db, session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check if session belongs to current user
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only logout your own sessions"
        )
    
    # Logout session
    logout_session(db, session)
    return None



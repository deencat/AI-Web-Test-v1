import logging
from typing import Callable, Generator, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer

from app.core.config import settings
from jose import JWTError
from sqlalchemy.orm import Session
from app.core.security import decode_token
from app.crud.user import get_user
from app.db.session import SessionLocal
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id: int = int(user_id_str)
    except ValueError:
        raise credentials_exception
    
    user = get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# Role hierarchy for Hermes QA Factory (HF-1)
_ROLE_RANK = {
    "viewer": 0,
    "user": 1,
    "tester": 1,
    "agent_operator": 2,
    "admin": 3,
    "superadmin": 4,
}

_FACTORY_OPERATOR_MIN_RANK = _ROLE_RANK["agent_operator"]


def _role_rank(role: Optional[str]) -> int:
    return _ROLE_RANK.get((role or "user").lower(), 0)


def require_role(min_rank: int, label: str) -> Callable:
    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if _role_rank(current_user.role) < min_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {label} role or higher",
            )
        return current_user

    return dependency


require_factory_operator = require_role(_FACTORY_OPERATOR_MIN_RANK, "agent_operator")
require_superadmin = require_role(_ROLE_RANK["superadmin"], "superadmin")

_optional_auth_bearer = HTTPBearer(auto_error=False)


def get_factory_operator_sse(
    db: Session = Depends(get_db),
    token: Optional[str] = Query(
        None,
        description="JWT for EventSource clients that cannot send Authorization headers",
    ),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_auth_bearer),
) -> User:
    """Factory operator auth for SSE (EventSource cannot send Authorization headers)."""
    raw = token or (credentials.credentials if credentials else None)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(raw)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user(db, user_id=user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if _role_rank(user.role) < _FACTORY_OPERATOR_MIN_RANK:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires agent_operator role or higher",
        )
    return user

_bridge_bearer = HTTPBearer(auto_error=False)
_bridge_logger = logging.getLogger(__name__)


def require_hermes_bridge_secret(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bridge_bearer),
) -> None:
    """Validate Bearer token for Hermes Bridge → AWT event POSTs (HF-6.2)."""
    secret = settings.HERMES_BRIDGE_SECRET
    if not secret:
        _bridge_logger.warning(
            "HERMES_BRIDGE_SECRET not set; accepting bridge events without auth (dev only)"
        )
        return
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.credentials != secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bridge secret",
            headers={"WWW-Authenticate": "Bearer"},
        )


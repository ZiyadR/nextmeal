from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app import models
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.config import settings
from app.database import get_db
from app import crud

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

_REFRESH_COOKIE = "refresh_token"


# --------------------------------------------------------------------------
# Request / Response schemas (auth-specific, not worth adding to schemas.py)
# --------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=False,       # set True behind HTTPS in production
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, path="/auth/refresh")


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
def register(request: Request, body: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    """Register a new user. Returns an access token and sets a refresh cookie."""
    existing = db.query(models.User).filter(models.User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = models.User(
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Seed the new user's categories and recipes from the global seed pool
    crud.seed_categories_for_user(db, user.id)
    crud.seed_recipes_for_user(db, user.id)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    # Persist refresh token so logout can invalidate it
    user.refresh_token = refresh_token
    db.commit()

    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(request: Request, body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate a user. Returns an access token and sets a refresh cookie."""
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    user.refresh_token = refresh_token
    db.commit()

    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    """Exchange a valid refresh cookie for a new access token."""
    token = request.cookies.get(_REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    user = verify_refresh_token(token, db)

    new_access = create_access_token({"sub": str(user.id)})
    new_refresh = create_refresh_token({"sub": str(user.id)})

    # Rotate refresh token
    user.refresh_token = new_refresh
    db.commit()

    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(access_token=new_access)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    """Invalidate the refresh token and clear the cookie."""
    token = request.cookies.get(_REFRESH_COOKIE)
    if token:
        user = db.query(models.User).filter(models.User.refresh_token == token).first()
        if user:
            user.refresh_token = None
            db.commit()
    _clear_refresh_cookie(response)

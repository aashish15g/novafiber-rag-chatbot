from secrets import token_urlsafe
from sqlite3 import IntegrityError

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.dependencies import check_origin, get_current_user
from app.services.auth import (
    ACCESS_COOKIE, CSRF_COOKIE, create_access_token, hash_password, verify_password)

router = APIRouter(prefix="/api/auth", tags=["Authentication"],
                   dependencies=[Depends(check_origin)])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(LoginRequest):
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    user_id: str
    email: str
    role: str
    created_at: str


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: RegisterRequest, request: Request):
    try:
        return request.app.state.users.create(str(body.email), hash_password(body.password))
    except IntegrityError:
        raise HTTPException(409, "This email is already registered.") from None


@router.post("/login", response_model=UserResponse)
def login(body: LoginRequest, request: Request, response: Response):
    user = request.app.state.users.by_email(str(body.email))
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Incorrect email or password.")
    settings = request.app.state.settings
    csrf = token_urlsafe(32)
    token = create_access_token(user["user_id"], settings.jwt_secret, csrf,
                                settings.access_token_expire_minutes)
    cookie_options = {"secure": settings.cookie_secure, "samesite": "lax",
                      "max_age": settings.access_token_expire_minutes * 60, "path": "/"}
    response.set_cookie(ACCESS_COOKIE, token, httponly=True, **cookie_options)
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, **cookie_options)
    response.headers["Cache-Control"] = "no-store"
    return user


@router.get("/me", response_model=UserResponse)
def me(response: Response, user=Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store"
    return user


@router.post("/logout", status_code=204)
def logout(response: Response, user=Depends(get_current_user)):
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")
    response.headers["Cache-Control"] = "no-store"

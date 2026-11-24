import os
from typing import Annotated
from uuid import UUID
from fastapi.security import APIKeyCookie

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, SecretStr, StringConstraints

from app.bot import SESSION_TTL
from app.providers.init_providers import BOT


router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE_NAME = "chat_session"
COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "true").lower() != "false"

Username = Annotated[str, StringConstraints(
    strip_whitespace=True, min_length=3, max_length=64, pattern=r"^[a-z0-9_]+$",
)]


class LoginRequest(BaseModel):
    username: Username
    password: SecretStr = Field(min_length=1, max_length=256)


class RegisterRequest(LoginRequest):
    password: SecretStr = Field(min_length=5, max_length=256)


class AuthUser(BaseModel):
    user_id: UUID
    username: str


class CurrentSession(AuthUser):
    session_id: UUID


session_cookie = APIKeyCookie(
    name=COOKIE_NAME,
    scheme_name="ChatSession",
    auto_error=False,
)

SessionCookie = Annotated[str | None, Depends(session_cookie)]


async def get_current_session(token: SessionCookie) -> CurrentSession:
    session = await BOT.get_auth_session(token) if token else None

    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Требуется вход")

    return CurrentSession(**session)


@router.post("/register", response_model=AuthUser, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest):
    """Регистрация пользователя"""

    user_id = await BOT.register_user(data.username, data.password.get_secret_value())

    if user_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Этот логин уже занят")

    return AuthUser(user_id=user_id, username=data.username)


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login(data: LoginRequest) -> Response:
    """Логин пользователя"""
    token = await BOT.login_user(data.username, data.password.get_secret_value())

    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный логин или пароль")

    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.set_cookie(
        key=COOKIE_NAME, value=token, max_age=int(SESSION_TTL.total_seconds()),
        path="/", httponly=True, secure=COOKIE_SECURE, samesite="strict",
    )
    return response


@router.get("/user", response_model=AuthUser)
async def user(response: Response, session: Annotated[CurrentSession, Depends(get_current_session)]):
    """Получение данных пользователя"""

    response.headers["Cache-Control"] = "no-store"
    return AuthUser(user_id=session.user_id, username=session.username)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(token: SessionCookie) -> Response:
    """Выход из лк"""

    if token:
        await BOT.logout_user(token)
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie(
        COOKIE_NAME, path="/", httponly=True, secure=COOKIE_SECURE, samesite="strict",
    )
    return response

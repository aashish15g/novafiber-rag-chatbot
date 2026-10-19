from secrets import compare_digest

from fastapi import Depends, HTTPException, Request
from jwt import InvalidTokenError

from app.services.auth import ACCESS_COOKIE, verify_access_token


def check_origin(request: Request):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        expected = f"{request.url.scheme}://{request.url.netloc}"
        if origin and origin != expected:
            raise HTTPException(403, "Cross-origin requests are not allowed.")


def get_current_user(request: Request):
    """Authenticate the cookie and read the user's current database role."""
    check_origin(request)
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(401, "Please sign in.")
    try:
        claims = verify_access_token(token, request.app.state.settings.jwt_secret)
    except InvalidTokenError:
        raise HTTPException(401, "Your session expired or is invalid. Please sign in again.") from None
    user = request.app.state.users.get(claims["sub"])
    if not user:
        raise HTTPException(401, "Account not found. Please sign in again.")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        supplied = request.headers.get("x-csrf-token", "")
        if not compare_digest(supplied, claims["csrf"]):
            raise HTTPException(403, "Invalid CSRF token. Reload the page and try again.")
    return user


def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Administrator access required.")
    return user

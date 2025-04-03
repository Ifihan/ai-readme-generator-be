import secrets
import jwt

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib import parse

from app.config import settings


def create_csrf_token() -> str:
    """
    Create a CSRF token using a secure random string.
    """
    return secrets.token_urlsafe(32)


def generate_oauth_state() -> str:
    """
    Generate a secure state parameter for OAuth flow to prevent CSRF attacks.
    """
    return secrets.token_urlsafe(32)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Creates JWT token for the given subject."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes == settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject)}

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm == "HS256")

    return encoded_jwt


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verifies the JWT token and returns the payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def is_valid_github_redirect_url(url: str) -> bool:
    """Checks if the given URL is a valid GitHub redirect URL."""
    allowed_domains = [
        "github.com",
        "www.github.com",
        "api.github.com",
        "www.api.github.com",
    ]

    parsed_url = parse.urlparse(url)

    return parsed_url.netloc in allowed_domains


# def is_valid_github_token_format(token: str) -> bool:
#     """Checks if the given token is a valid GitHub token."""
#     if not token or len(token) != 40:
#         return False

#     try:
#         int(token, 16)
#         return True
#     except ValueError:
#         return False


import re


def is_valid_github_token_format(token: str) -> bool:
    """Checks if the given token is a valid GitHub token."""
    if not token or len(token) < 10:
        return False

    # Check if token contains only alphanumeric characters and underscores
    # which is typical for GitHub tokens
    return bool(re.match(r"^[a-zA-Z0-9_]+$", token))

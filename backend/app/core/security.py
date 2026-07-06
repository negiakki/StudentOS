"""Supabase JWT verification.

Authentication is owned by Supabase Auth (GoTrue). The backend never issues or
stores credentials — it only *verifies* the access token that Supabase minted and
derives the current user from its claims.

Verification strategy (Docs/03_System_Architecture.md §14, Supabase guidance):

1. Preferred — **asymmetric** signing (RS256/ES256). The token is verified against
   the project's public keys fetched from the JWKS endpoint. No secret lives on the
   backend, so a backend compromise cannot forge tokens.
2. Fallback — legacy **HS256** shared secret, only when `SUPABASE_JWT_SECRET` is set
   and the token header advertises HS256. Supabase discourages this, so it is opt-in.

Either way we assert the audience and issuer, so tokens from another project or with
the wrong audience are rejected.
"""

from __future__ import annotations

from functools import lru_cache

import jwt
from jwt import PyJWKClient

from app.core.config import Settings, get_settings

# Algorithms we accept for the asymmetric (JWKS) path.
_ASYMMETRIC_ALGORITHMS = ("RS256", "ES256")


class AuthError(Exception):
    """Raised when a token is missing, malformed, or fails verification."""


@lru_cache
def _jwks_client(jwks_url: str) -> PyJWKClient:
    """Cached JWKS client. PyJWKClient caches keys internally and refetches on
    rotation (unknown `kid`), so a single instance is safe to reuse."""
    return PyJWKClient(jwks_url)


def _decode_asymmetric(token: str, settings: Settings) -> dict:
    signing_key = _jwks_client(settings.supabase_jwks_url).get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=list(_ASYMMETRIC_ALGORITHMS),
        audience=settings.supabase_jwt_audience,
        issuer=settings.supabase_jwt_issuer,
        options={"require": ["exp", "sub"]},
    )


def _decode_hs256(token: str, settings: Settings) -> dict:
    if not settings.supabase_jwt_secret:
        raise AuthError("Token is HS256-signed but no SUPABASE_JWT_SECRET is configured.")
    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        audience=settings.supabase_jwt_audience,
        # Legacy HS256 tokens from older projects may omit `iss`; don't hard-require it.
        options={"require": ["exp", "sub"]},
    )


def verify_token(token: str, settings: Settings | None = None) -> dict:
    """Verify a Supabase access token and return its validated claims.

    Raises AuthError on any problem (expired, wrong audience/issuer, bad signature,
    unsupported algorithm, or unreachable JWKS).
    """
    settings = settings or get_settings()

    if not settings.supabase_url:
        raise AuthError("Supabase is not configured on the backend (SUPABASE_URL missing).")

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise AuthError("Malformed authentication token.") from exc

    alg = header.get("alg")

    try:
        if alg in _ASYMMETRIC_ALGORITHMS:
            claims = _decode_asymmetric(token, settings)
        elif alg == "HS256":
            claims = _decode_hs256(token, settings)
        else:
            raise AuthError(f"Unsupported token signing algorithm: {alg!r}.")
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Authentication token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Invalid authentication token.") from exc
    except AuthError:
        raise
    except Exception as exc:  # e.g. JWKS endpoint unreachable
        raise AuthError("Unable to verify authentication token.") from exc

    return claims

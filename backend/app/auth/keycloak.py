"""
Keycloak JWKS-based JWT validator.

Flow:
1. Fetch OIDC discovery document at startup → extract jwks_uri
2. Cache JWKS in memory with 15-minute TTL
3. On each request: verify signature + standard claims against cached keys
"""
import time
from typing import Any

import httpx
import structlog
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode

from app.core.config import get_settings
from app.core.errors import AuthError

logger = structlog.get_logger(__name__)

_jwks_cache: dict[str, Any] = {}
_jwks_fetched_at: float = 0.0
_JWKS_TTL_SECONDS = 900  # 15 minutes


async def _fetch_jwks() -> dict[str, Any]:
    global _jwks_cache, _jwks_fetched_at

    now = time.monotonic()
    if _jwks_cache and (now - _jwks_fetched_at) < _JWKS_TTL_SECONDS:
        return _jwks_cache

    settings = get_settings()
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Fetch OIDC discovery document
        disc_resp = await client.get(settings.keycloak_oidc_config_url)
        disc_resp.raise_for_status()
        jwks_uri = disc_resp.json()["jwks_uri"]

        # Fetch JWKS
        jwks_resp = await client.get(jwks_uri)
        jwks_resp.raise_for_status()
        jwks = jwks_resp.json()

    # Index keys by kid for O(1) lookup
    _jwks_cache = {key["kid"]: key for key in jwks.get("keys", [])}
    _jwks_fetched_at = now
    logger.info("jwks_refreshed", key_count=len(_jwks_cache))
    return _jwks_cache


async def validate_token(token: str) -> dict[str, Any]:
    """
    Validate a JWT Bearer token against Keycloak JWKS.
    Returns decoded claims on success, raises AuthError on failure.
    """
    settings = get_settings()

    try:
        # Decode header only (no verification) to get kid
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise AuthError(f"Invalid token header: {exc}") from exc

    kid = unverified_header.get("kid")
    if not kid:
        raise AuthError("Token missing kid header")

    jwks = await _fetch_jwks()
    key_data = jwks.get(kid)

    if key_data is None:
        # kid not in cache — force refresh once and retry
        _jwks_fetched_at = 0.0
        jwks = await _fetch_jwks()
        key_data = jwks.get(kid)

    if key_data is None:
        raise AuthError("Token signed with unknown key")

    try:
        public_key = jwk.construct(key_data)
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.keycloak_audience,
            options={"verify_exp": True, "verify_aud": True},
        )
    except JWTError as exc:
        raise AuthError(f"Token validation failed: {exc}") from exc

    return claims

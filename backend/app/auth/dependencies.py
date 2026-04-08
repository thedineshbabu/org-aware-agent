from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.keycloak import validate_token
from app.auth.models import UserContext
from app.core.errors import AuthError

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UserContext:
    if credentials is None:
        raise AuthError("Missing Authorization header")

    claims = await validate_token(credentials.credentials)

    # Extract roles from Keycloak realm_access claim
    realm_access = claims.get("realm_access", {})
    roles: list[str] = realm_access.get("roles", [])

    # Filter out Keycloak internal roles (offline_access, uma_authorization, etc.)
    user_roles = [r for r in roles if not r.startswith(("offline_", "uma_", "default-"))]

    # Groups come from a custom Keycloak mapper
    groups: list[str] = claims.get("groups", [])

    # Department comes from a custom Keycloak attribute mapper
    department: str = claims.get("department", "")

    display_name = claims.get("name", "") or claims.get("preferred_username", "")

    return UserContext(
        user_id=claims["sub"],
        email=claims.get("email", ""),
        display_name=display_name,
        roles=user_roles,
        groups=groups,
        department=department,
    )

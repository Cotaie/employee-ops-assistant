from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.concurrency import run_in_threadpool

from agent_api.app.auth.models import AuthenticatedUser
from agent_api.app.auth.verifier import OidcTokenVerifier, TokenVerificationError
from agent_api.app.core.config import Settings
from agent_api.app.dependencies.settings import get_runtime_settings

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _token_verifier(issuer: str, audience: str, jwks_url: str) -> OidcTokenVerifier:
    return OidcTokenVerifier(
        issuer=issuer,
        audience=audience,
        jwks_url=jwks_url,
    )


async def get_authenticated_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> AuthenticatedUser:
    """Return the identity from a valid bearer token or reject the request."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if settings.oidc_audience is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC authentication is not configured.",
        )

    try:
        verifier = _token_verifier(
            settings.oidc_issuer,
            settings.oidc_audience,
            settings.oidc_jwks_url,
        )
        return await run_in_threadpool(verifier.verify, credentials.credentials)
    except TokenVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUserDependency = Annotated[AuthenticatedUser, Depends(get_authenticated_user)]

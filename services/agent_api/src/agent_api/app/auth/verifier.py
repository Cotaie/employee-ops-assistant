import logging
from collections.abc import Iterable
from typing import Any, Protocol

import jwt
from jwt import PyJWK, PyJWKClient
from jwt.exceptions import PyJWTError

from agent_api.app.auth.models import AuthenticatedUser

logger = logging.getLogger(__name__)

GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")


class TokenVerificationError(ValueError):
    """Raised when a bearer token cannot establish a trusted identity."""


class SigningKeyClient(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> PyJWK: ...


def _string_set(value: object) -> frozenset[str]:
    if isinstance(value, str):
        return frozenset(value.split())
    if isinstance(value, Iterable):
        return frozenset(item for item in value if isinstance(item, str))
    return frozenset()


class OidcTokenVerifier:
    """Validate signed OIDC ID tokens and map their trusted claims."""

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_url: str | None = None,
        jwks_client: SigningKeyClient | None = None,
    ) -> None:
        if jwks_client is None:
            if jwks_url is None:
                raise ValueError("jwks_url is required when no JWKS client is supplied")
            jwks_client = PyJWKClient(jwks_url, cache_keys=True)
        self._issuer: str | tuple[str, ...] = GOOGLE_ISSUERS if issuer in GOOGLE_ISSUERS else issuer
        self._audience = audience
        self._jwks_client = jwks_client

    def verify(self, token: str) -> AuthenticatedUser:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            claims: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["aud", "exp", "iat", "iss", "sub"]},
            )
            subject = claims["sub"]
            if not isinstance(subject, str) or not subject:
                raise TokenVerificationError("Token subject is invalid")
        except (PyJWTError, TokenVerificationError) as exc:
            logger.warning(
                "OIDC bearer token rejected (%s): %s",
                type(exc).__name__,
                exc,
            )
            raise TokenVerificationError("Bearer token verification failed") from exc

        email = claims.get("email")
        return AuthenticatedUser(
            subject=subject,
            email=email if isinstance(email, str) else None,
            email_verified=claims.get("email_verified") is True,
            roles=_string_set(claims.get("roles")),
            scopes=_string_set(claims.get("scope")),
        )

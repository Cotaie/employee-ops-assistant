from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from agent_api.app.auth.verifier import OidcTokenVerifier, TokenVerificationError

ISSUER = "https://accounts.google.com"
AUDIENCE = "employee-ops-client"


class StaticSigningKeyClient:
    def __init__(self, key: rsa.RSAPublicKey) -> None:
        self._key = key

    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK:
        del token
        return jwt.PyJWK.from_dict(
            {
                "kty": "RSA",
                "kid": "test-key",
                "use": "sig",
                "alg": "RS256",
                "n": jwt.utils.to_base64url_uint(self._key.public_numbers().n).decode(),
                "e": jwt.utils.to_base64url_uint(self._key.public_numbers().e).decode(),
            }
        )


@pytest.fixture
def signing_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def token_for(
    signing_key: rsa.RSAPrivateKey,
    *,
    audience: str = AUDIENCE,
    expires_at: datetime | None = None,
) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "iss": ISSUER,
            "aud": audience,
            "sub": "google-user-123",
            "email": "employee@example.com",
            "email_verified": True,
            "iat": now,
            "exp": expires_at or now + timedelta(minutes=5),
        },
        signing_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def verifier_for(signing_key: rsa.RSAPrivateKey) -> OidcTokenVerifier:
    return OidcTokenVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_client=StaticSigningKeyClient(signing_key.public_key()),
    )


def test_verifier_returns_authenticated_identity(
    signing_key: rsa.RSAPrivateKey,
) -> None:
    user = verifier_for(signing_key).verify(token_for(signing_key))

    assert user.subject == "google-user-123"
    assert user.email == "employee@example.com"
    assert user.email_verified is True


def test_verifier_rejects_wrong_audience(signing_key: rsa.RSAPrivateKey) -> None:
    with pytest.raises(TokenVerificationError):
        verifier_for(signing_key).verify(token_for(signing_key, audience="different-client"))


def test_verifier_rejects_untrusted_signature(
    signing_key: rsa.RSAPrivateKey,
) -> None:
    untrusted_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    with pytest.raises(TokenVerificationError):
        verifier_for(signing_key).verify(token_for(untrusted_key))


def test_verifier_rejects_expired_token(signing_key: rsa.RSAPrivateKey) -> None:
    with pytest.raises(TokenVerificationError):
        verifier_for(signing_key).verify(
            token_for(
                signing_key,
                expires_at=datetime.now(UTC) - timedelta(minutes=1),
            )
        )

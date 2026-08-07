from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Identity established from a verified OIDC ID token."""

    subject: str
    email: str | None = None
    email_verified: bool = False
    roles: frozenset[str] = field(default_factory=frozenset)
    scopes: frozenset[str] = field(default_factory=frozenset)

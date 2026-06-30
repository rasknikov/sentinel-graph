from typing import Protocol

from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, field_validator

from packages.common.config import settings
from packages.security.roles import normalize_roles
from packages.security.scopes import normalize_scopes


class TokenClaims(BaseModel):
    model_config = ConfigDict(frozen=True)

    sub: str
    tenant_id: str
    session_id: str
    roles: tuple[str, ...]
    scopes: tuple[str, ...]
    department: str
    clearance_level: str
    iss: str
    aud: str

    @field_validator("roles", mode="before")
    @classmethod
    def normalize_roles_claim(cls, value: object) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("roles must be a list of strings")

        return normalize_roles(tuple(str(item) for item in value))

    @field_validator("scopes", mode="before")
    @classmethod
    def normalize_scopes_claim(cls, value: object) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("scopes must be a list of strings")

        return normalize_scopes(tuple(str(item) for item in value))


class TokenValidator(Protocol):
    def validate(self, token: str) -> TokenClaims:
        ...

        
class JwtTokenValidator:
    def validate(self, token: str) -> TokenClaims:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                issuer=settings.jwt_issuer,
                audience=settings.jwt_audience,
            )
        except JWTError as exc:
            raise ValueError("invalid authentication token") from exc
        
        return TokenClaims(**payload)
    
class JwksTokenValidator:
    def validate(self, token: str) -> TokenClaims:
        raise NotImplementedError("JWKS validation is not implemented yet.")

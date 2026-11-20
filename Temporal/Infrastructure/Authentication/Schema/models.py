"""JWT claims with Pydantic validation but without a class hierarchy."""
from __future__ import annotations
from dataclasses import fields
from typing import Any
from pydantic import ConfigDict, TypeAdapter, Field
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="allow"))
class TokenPayload:
    """Validated JWT claims. Extra issuer/audience claims are preserved."""
    sub: str = Field(description="Authenticated subject identifier")
    email: str | None = None
    name: str | None = None
    picture_url: str | None = None
    jti: str | None = None
    type: str | None = None
    family: str | None = None
    iat: int | None = None
    exp: int | None = None

    def model_dump(self, *, exclude: set[str] | None = None) -> dict[str, Any]:
        """Backward-compatible claim extraction for JWTHandler.

        Unlike TypeAdapter.dump_python, preserve extra claims too.
        """
        omitted = exclude or set()
        return {key: value for key, value in vars(self).items() if key not in omitted}

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "TokenPayload":
        return TypeAdapter(cls).validate_python(payload)

    @classmethod
    def model_json_schema(cls) -> dict[str, Any]:
        return TypeAdapter(cls).json_schema()

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TokenPayload":
        return cls.model_validate(payload)

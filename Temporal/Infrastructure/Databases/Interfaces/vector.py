"""Validated vector document DTO without model inheritance."""
from __future__ import annotations
from typing import Any
from pydantic import ConfigDict, Field, TypeAdapter
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(json_schema_extra={
    "example": {
        "id": "db-generated-id-123",
        "content": "A sample document",
        "vector": [0.1, 0.2],
        "payload": {"source": "web"},
        "score": 0.95,
    }
}))
class VectorDocument:
    """Vector content plus metadata, validated by Pydantic."""
    content: str = Field(description="Document text")
    vector: list[float] = Field(description="Embedding values")
    id: str | None = Field(default=None, description="Optional document ID")
    payload: dict[str, Any] = Field(default_factory=dict)
    score: float | None = None

    def model_dump(self, *, exclude: set[str] | None = None) -> dict[str, Any]:
        return TypeAdapter(type(self)).dump_python(self, exclude=exclude)

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "VectorDocument":
        return TypeAdapter(cls).validate_python(payload)

    @classmethod
    def model_json_schema(cls) -> dict[str, Any]:
        return TypeAdapter(cls).json_schema()

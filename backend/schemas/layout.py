from pydantic import BaseModel, field_validator
from typing import Any, Dict, List, Optional


class BlockConfig(BaseModel):
    id: str
    block_type: str
    order_index: int
    config: Dict[str, Any]
    is_visible: bool = True


class AIGenerateRequest(BaseModel):
    prompt: str

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El prompt no puede estar vacío")
        if len(v) > 1000:
            raise ValueError("El prompt es demasiado largo (máx 1000 caracteres)")
        return v


class LayoutUpdate(BaseModel):
    blocks: List[BlockConfig]


class BlockResponse(BaseModel):
    id: str
    block_type: str
    order_index: int
    config: Dict[str, Any]
    is_visible: bool

    class Config:
        from_attributes = True
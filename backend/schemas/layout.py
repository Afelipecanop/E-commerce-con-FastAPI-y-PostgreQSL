from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class BlockConfig(BaseModel):
    id: str
    block_type: str
    order_index: int
    config: Dict[str, Any]
    is_visible: bool = True


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
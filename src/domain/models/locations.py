from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
import uuid

class DivisionBase(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    is_active: bool = True

class DivisionCreate(DivisionBase):
    pass

class DivisionUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class DivisionResponse(DivisionBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class BlockBase(BaseModel):
    division_id: uuid.UUID
    code: str = Field(..., max_length=20)
    planting_year: Optional[int] = None
    area_ha: Optional[float] = None
    is_active: bool = True

class BlockCreate(BlockBase):
    pass

class BlockUpdate(BaseModel):
    division_id: Optional[uuid.UUID] = None
    code: Optional[str] = Field(None, max_length=20)
    planting_year: Optional[int] = None
    area_ha: Optional[float] = None
    is_active: Optional[bool] = None

class BlockResponse(BlockBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class CollectionPointBase(BaseModel):
    block_id: uuid.UUID
    point_number: int
    is_active: bool = True

class CollectionPointCreate(CollectionPointBase):
    pass

class CollectionPointUpdate(BaseModel):
    block_id: Optional[uuid.UUID] = None
    point_number: Optional[int] = None
    is_active: Optional[bool] = None

class CollectionPointResponse(CollectionPointBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime

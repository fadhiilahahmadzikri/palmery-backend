from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class ConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    config_key: str
    config_value: float
    description: Optional[str]

class ConfigCreateRequest(BaseModel):
    config_key: str = Field(..., min_length=1)
    config_value: float = Field(..., ge=0)
    description: Optional[str] = None

class ConfigUpdateRequest(BaseModel):
    value: float = Field(..., ge=0)

class TierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tier_level: int
    min_kg: float
    max_kg: Optional[float]
    rate_per_kg: float

class TierCreateRequest(BaseModel):
    tier_level: int = Field(..., gt=0)
    min_kg: float = Field(..., ge=0)
    max_kg: Optional[float] = None
    rate_per_kg: float = Field(..., ge=0)

class TierUpdateRequest(BaseModel):
    min_kg: Optional[float] = Field(None, ge=0)
    max_kg: Optional[float] = None
    rate_per_kg: Optional[float] = Field(None, ge=0)

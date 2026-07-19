from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime
import uuid

class FineConfigBase(BaseModel):
    mode: str = Field(..., pattern="^(rupiah|kg)$")
    rate_per_bunch_rupiah: Optional[float] = None
    effective_from: date
    effective_until: Optional[date] = None

class FineConfigCreate(FineConfigBase):
    pass

class FineConfigResponse(FineConfigBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime

class LooseFruitConfigBase(BaseModel):
    flat_percentage: float = Field(..., ge=0, le=1)
    rate_per_kg_rupiah: float = Field(..., ge=0)
    effective_from: date
    effective_until: Optional[date] = None

class LooseFruitConfigCreate(LooseFruitConfigBase):
    pass

class LooseFruitConfigResponse(LooseFruitConfigBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime

class EligibilityConfigBase(BaseModel):
    basis_kg: float = Field(..., ge=0)
    min_bunch_count: int = Field(..., ge=0)
    effective_from: date
    effective_until: Optional[date] = None

class EligibilityConfigCreate(EligibilityConfigBase):
    pass

class EligibilityConfigResponse(EligibilityConfigBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime

class TierBase(BaseModel):
    tier_level: int = Field(..., gt=0)
    min_kg: float = Field(..., ge=0)
    max_kg: Optional[float] = None
    rate_per_kg: float = Field(..., ge=0)
    effective_from: date
    effective_until: Optional[date] = None

class TierCreate(TierBase):
    pass

class TierResponse(TierBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    updated_at: datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import date, datetime
import uuid

class HarvestRecordCreate(BaseModel):
    harvester_id: uuid.UUID
    collection_point_id: uuid.UUID
    harvest_date: Optional[date] = None
    valid_bunch_count: int = Field(..., ge=0)
    unripe_bunch_count: int = Field(0, ge=0)
    avg_bunch_weight_kg: float = Field(..., gt=0)
    notes: Optional[str] = None
    recorded_by: Optional[str] = None

class HarvestRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    harvester_id: uuid.UUID
    block_id: uuid.UUID
    collection_point_id: uuid.UUID
    harvest_date: date
    
    valid_bunch_count: int
    unripe_bunch_count: int
    avg_bunch_weight_kg: float
    
    gross_tonnage_kg: float
    
    loose_fruit_percentage_snapshot: float
    loose_fruit_rate_snapshot_rupiah: float
    loose_fruit_deduction_kg: float
    loose_fruit_premium_rupiah: float
    
    fine_mode_snapshot: str
    fine_amount_rupiah: float
    weight_deduction_kg: float
    
    net_tonnage_kg: float
    
    notes: Optional[str]
    recorded_by: Optional[str]
    payroll_period_id: Optional[uuid.UUID]
    created_at: datetime

class PaginatedHarvestRecordResponse(BaseModel):
    data: List[HarvestRecordResponse]
    total: int

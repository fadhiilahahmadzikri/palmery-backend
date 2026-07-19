from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime, date
import uuid

class PayrollPeriodBase(BaseModel):
    year: int
    month: int = Field(..., ge=1, le=12)
    status: str = Field(default="open")

class PayrollPeriodCreate(PayrollPeriodBase):
    pass

class PayrollPeriodResponse(PayrollPeriodBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    closed_at: Optional[datetime] = None
    created_at: datetime

class PayrollTierDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tier_level: int
    kg_in_tier: float
    rate_per_kg: float
    subtotal_rupiah: float

class PayrollBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    payroll_period_id: uuid.UUID
    status: str
    generated_at: datetime
    generated_by: str

class DailyHarvestBreakdownResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    harvest_date: date
    valid_bunch_count: int
    unripe_bunch_count: int
    net_tonnage_kg: float
    loose_fruit_premium_rupiah: float
    fine_amount_rupiah: float
    fine_mode_snapshot: str

class PayrollSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[uuid.UUID] = None
    payroll_batch_id: Optional[uuid.UUID] = None
    harvester_id: uuid.UUID
    
    total_valid_bunch_count: int
    total_unripe_bunch_count: int
    total_net_tonnage_kg: float
    total_loose_fruit_premium_rupiah: float
    
    fine_mode_used: str
    total_fine_rupiah: float
    
    total_tier_premium_rupiah: float
    total_net_pay_rupiah: float
    
    generated_at: datetime
    tier_details: List[PayrollTierDetailResponse] = []
    daily_records: List[DailyHarvestBreakdownResponse] = []

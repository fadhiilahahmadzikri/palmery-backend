from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
import uuid

class HarvestRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    harvest_date: date
    harvester_name: str
    
    input_total_bunches: int
    input_avg_bunch_weight: float
    input_unripe_penalty: float
    
    calc_total_tonnage: float
    calc_loose_fruit_kg: float
    calc_net_ffb: float
    
    premium_loose_fruit: float
    premium_ffb: float
    total_final_premium: float
    tier_status: Optional[str] = None
    
class HarvestRecordUpdateRequest(BaseModel):
    harvester_name: Optional[str] = None
    input_total_bunches: Optional[int] = None
    input_avg_bunch_weight: Optional[float] = None
    input_unripe_penalty: Optional[float] = None

from typing import List

class PaginatedHarvestRecordResponse(BaseModel):
    data: List[HarvestRecordResponse]
    total: int

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.domain.engine.premium_calculator import (
    calculate_premium, 
    HarvestConfig, 
    TierConfig, 
    PremiumResult
)
from src.domain.repositories.config_repo_interface import IConfigRepository
from src.domain.repositories.harvest_repo_interface import IHarvestRepository
from src.api.dependencies import get_config_repo, get_harvest_repo

router = APIRouter(prefix="/api/v1", tags=["calculator"])

class CalculatePremiumRequest(BaseModel):
    harvester_name: str = Field(..., min_length=2)
    total_bunches: int = Field(..., gt=0)
    avg_bunch_weight: float = Field(..., gt=0)
    unripe_penalty: float = Field(0.0, ge=0)

@router.post("/calculate", response_model=PremiumResult)
async def calculate_endpoint(
    req: CalculatePremiumRequest,
    config_repo: IConfigRepository = Depends(get_config_repo),
    harvest_repo: IHarvestRepository = Depends(get_harvest_repo)
):
    
    # Fetch Config
    db_configs = await config_repo.get_all_configs()
    config_map = {c.config_key: float(c.config_value) for c in db_configs}
    
    config = HarvestConfig(
        flat_rate_percentage=config_map.get("FLAT_RATE_PERCENTAGE", 0.10),
        loose_fruit_rate=config_map.get("LOOSE_FRUIT_RATE", 75.0),
        base_target_kg=config_map.get("BASE_TARGET_KG", 1000.0),
        min_bunches_required=int(config_map.get("MIN_BUNCHES_REQUIRED", 100))
    )
    
    # Fetch Tiers
    db_tiers = await config_repo.get_all_tiers()
    tiers = [
        TierConfig(min_kg=float(t.min_kg), max_kg=float(t.max_kg) if t.max_kg else None, rate=float(t.rate_per_kg))
        for t in db_tiers
    ]
    
    # Run calculation
    result = calculate_premium(
        harvester_name=req.harvester_name,
        total_bunches=req.total_bunches,
        avg_bunch_weight=req.avg_bunch_weight,
        unripe_penalty=req.unripe_penalty,
        config=config,
        tiers=tiers
    )
    
    # Save to database
    record_data = {
        "harvester_name": req.harvester_name,
        "harvest_date": datetime.now().date(),
        "input_total_bunches": req.total_bunches,
        "input_avg_bunch_weight": req.avg_bunch_weight,
        "input_unripe_penalty": req.unripe_penalty,
        "calc_total_tonnage": result.total_tonnage,
        "calc_loose_fruit_kg": result.loose_fruit_kg,
        "calc_net_ffb": result.net_ffb,
        "premium_loose_fruit": result.premium_loose_fruit,
        "premium_ffb": result.premium_ffb,
        "total_final_premium": result.total_final_premium,
        "tier_status": result.tier_status
    }
    await harvest_repo.create_record(record_data)
    
    return result

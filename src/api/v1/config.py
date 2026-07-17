from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.domain.repositories.config_repo_interface import IConfigRepository
from src.api.dependencies import get_config_repo
from src.domain.models.config import (
    ConfigResponse, ConfigUpdateRequest, ConfigCreateRequest,
    TierResponse, TierUpdateRequest, TierCreateRequest
)

router = APIRouter(prefix="/api/v1/config", tags=["config"])

@router.get("", response_model=List[ConfigResponse])
async def get_all_configs(repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.get_all_configs()

@router.put("/{key}", response_model=ConfigResponse)
async def update_config(key: str, req: ConfigUpdateRequest, repo: IConfigRepository = Depends(get_config_repo)):
    updated = await repo.update_config(key.upper(), req.value)
    if not updated:
        # Upsert if not found
        return await repo.create_config({
            "config_key": key.upper(),
            "config_value": req.value,
            "description": "Auto-created via upsert"
        })
    return updated

@router.get("/tiers", response_model=List[TierResponse])
async def get_tiers(repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.get_all_tiers()

@router.post("", response_model=ConfigResponse)
async def create_config(req: ConfigCreateRequest, repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.create_config(req.model_dump(exclude_unset=True))

@router.delete("/{config_id}", status_code=204)
async def delete_config(config_id: int, repo: IConfigRepository = Depends(get_config_repo)):
    success = await repo.delete_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Config not found")
    return None

@router.post("/tiers", response_model=TierResponse)
async def create_tier(req: TierCreateRequest, repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.create_tier(req.model_dump(exclude_unset=True))

@router.put("/tiers/{tier_id}", response_model=TierResponse)
async def update_tier(tier_id: int, req: TierUpdateRequest, repo: IConfigRepository = Depends(get_config_repo)):
    updated = await repo.update_tier(tier_id, req.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Tier not found")
    return updated

@router.delete("/tiers/{tier_id}", status_code=204)
async def delete_tier(tier_id: int, repo: IConfigRepository = Depends(get_config_repo)):
    success = await repo.delete_tier(tier_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tier not found")
    return None

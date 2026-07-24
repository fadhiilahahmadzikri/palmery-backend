from fastapi import APIRouter, Depends
from typing import List, Optional

from src.domain.models.config import (
    FineConfigCreate, FineConfigResponse,
    LooseFruitConfigCreate, LooseFruitConfigResponse,
    EligibilityConfigCreate, EligibilityConfigResponse,
    TierCreate, TierUpdate, TierResponse
)
from src.domain.repositories.config_repo_interface import IConfigRepository
from src.api.dependencies import get_config_repo

router = APIRouter(prefix="/api/v1/config", tags=["config"])

@router.get("/fine/active", response_model=FineConfigResponse)
async def get_active_fine_config(repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.get_active_fine_config()

@router.post("/fine", response_model=FineConfigResponse, status_code=201)
async def create_fine_config(req: FineConfigCreate, repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.create_fine_config(req.model_dump())

@router.get("/loose-fruit/active", response_model=LooseFruitConfigResponse)
async def get_active_loose_fruit_config(repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.get_active_loose_fruit_config()

@router.post("/loose-fruit", response_model=LooseFruitConfigResponse, status_code=201)
async def create_loose_fruit_config(req: LooseFruitConfigCreate, repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.create_loose_fruit_config(req.model_dump())

@router.get("/eligibility/active", response_model=Optional[EligibilityConfigResponse])
async def get_active_eligibility_config(repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.get_active_eligibility_config()

@router.post("/eligibility", response_model=EligibilityConfigResponse, status_code=201)
async def create_eligibility_config(req: EligibilityConfigCreate, repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.create_eligibility_config(req.model_dump())

@router.get("/tiers/active", response_model=List[TierResponse])
async def get_active_tiers(repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.get_active_tiers()

@router.post("/tiers", response_model=TierResponse, status_code=201)
async def create_tier(req: TierCreate, repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.create_tier(req.model_dump())

@router.put("/tiers/{tier_id}", response_model=TierResponse)
async def update_tier(tier_id: int, req: TierUpdate, repo: IConfigRepository = Depends(get_config_repo)):
    from fastapi import HTTPException
    updated = await repo.update_tier(tier_id, req.model_dump(exclude_none=True))
    if updated is None:
        raise HTTPException(status_code=404, detail="Tier tidak ditemukan")
    return updated

@router.delete("/tiers/{tier_id}", status_code=204)
async def delete_tier(tier_id: int, repo: IConfigRepository = Depends(get_config_repo)):
    from fastapi import HTTPException
    deleted = await repo.delete_tier(tier_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tier tidak ditemukan")

from pydantic import BaseModel
import uuid

class BulkDeleteTiersReq(BaseModel):
    tier_ids: List[int]

@router.post("/tiers/bulk-delete")
async def bulk_delete_tiers(req: BulkDeleteTiersReq, repo: IConfigRepository = Depends(get_config_repo)):
    return await repo.bulk_delete_tiers(req.tier_ids)

@router.delete("/fine/{config_id}", status_code=204)
async def delete_fine_config(config_id: uuid.UUID, repo: IConfigRepository = Depends(get_config_repo)):
    from fastapi import HTTPException
    deleted = await repo.delete_fine_config(config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Konfigurasi denda tidak ditemukan")

@router.delete("/loose-fruit/{config_id}", status_code=204)
async def delete_loose_fruit_config(config_id: uuid.UUID, repo: IConfigRepository = Depends(get_config_repo)):
    from fastapi import HTTPException
    deleted = await repo.delete_loose_fruit_config(config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Konfigurasi brondolan tidak ditemukan")

@router.delete("/eligibility/{config_id}", status_code=204)
async def delete_eligibility_config(config_id: uuid.UUID, repo: IConfigRepository = Depends(get_config_repo)):
    from fastapi import HTTPException
    deleted = await repo.delete_eligibility_config(config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Konfigurasi syarat premi tidak ditemukan")

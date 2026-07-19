from fastapi import APIRouter, Depends
from typing import List

from src.domain.models.config import (
    FineConfigCreate, FineConfigResponse,
    LooseFruitConfigCreate, LooseFruitConfigResponse,
    EligibilityConfigCreate, EligibilityConfigResponse,
    TierCreate, TierResponse
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

@router.get("/eligibility/active", response_model=EligibilityConfigResponse)
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

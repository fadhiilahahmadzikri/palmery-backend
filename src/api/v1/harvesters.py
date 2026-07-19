from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
import uuid

from src.domain.models.harvester import HarvesterCreate, HarvesterUpdate, HarvesterResponse
from src.domain.repositories.harvester_repo_interface import IHarvesterRepository
from src.api.dependencies import get_harvester_repo

router = APIRouter(prefix="/api/v1/harvesters", tags=["harvesters"])

@router.get("", response_model=List[HarvesterResponse])
async def list_harvesters(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repo: IHarvesterRepository = Depends(get_harvester_repo)
):
    return await repo.get_harvesters(skip=skip, limit=limit)

@router.get("/{harvester_id}", response_model=HarvesterResponse)
async def get_harvester(harvester_id: uuid.UUID, repo: IHarvesterRepository = Depends(get_harvester_repo)):
    harvester = await repo.get_harvester_by_id(harvester_id)
    if not harvester:
        raise HTTPException(status_code=404, detail="Harvester not found")
    return harvester

@router.post("", response_model=HarvesterResponse, status_code=201)
async def create_harvester(req: HarvesterCreate, repo: IHarvesterRepository = Depends(get_harvester_repo)):
    return await repo.create_harvester(req.model_dump())

@router.put("/{harvester_id}", response_model=HarvesterResponse)
async def update_harvester(harvester_id: uuid.UUID, req: HarvesterUpdate, repo: IHarvesterRepository = Depends(get_harvester_repo)):
    updated = await repo.update_harvester(harvester_id, req.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Harvester not found")
    return updated

@router.delete("/{harvester_id}", status_code=204)
async def delete_harvester(harvester_id: uuid.UUID, repo: IHarvesterRepository = Depends(get_harvester_repo)):
    success = await repo.delete_harvester(harvester_id)
    if not success:
        raise HTTPException(status_code=404, detail="Harvester not found")

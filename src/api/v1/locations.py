from fastapi import APIRouter, Depends, HTTPException
from typing import List
import uuid

from src.domain.models.locations import (
    DivisionCreate, DivisionResponse, DivisionUpdate,
    BlockCreate, BlockResponse, BlockUpdate,
    CollectionPointCreate, CollectionPointResponse, CollectionPointUpdate
)
from src.domain.repositories.location_repo_interface import ILocationRepository
from src.api.dependencies import get_location_repo

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])

@router.get("/divisions", response_model=List[DivisionResponse])
async def list_divisions(repo: ILocationRepository = Depends(get_location_repo)):
    return await repo.get_divisions()

@router.post("/divisions", response_model=DivisionResponse, status_code=201)
async def create_division(req: DivisionCreate, repo: ILocationRepository = Depends(get_location_repo)):
    return await repo.create_division(req.model_dump())

@router.get("/divisions/{division_id}/blocks", response_model=List[BlockResponse])
async def list_blocks(division_id: uuid.UUID, repo: ILocationRepository = Depends(get_location_repo)):
    return await repo.get_blocks_by_division(division_id)

@router.post("/blocks", response_model=BlockResponse, status_code=201)
async def create_block(req: BlockCreate, repo: ILocationRepository = Depends(get_location_repo)):
    return await repo.create_block(req.model_dump())

@router.get("/blocks/{block_id}/points", response_model=List[CollectionPointResponse])
async def list_collection_points(block_id: uuid.UUID, repo: ILocationRepository = Depends(get_location_repo)):
    return await repo.get_points_by_block(block_id)

@router.post("/points", response_model=CollectionPointResponse, status_code=201)
async def create_collection_point(req: CollectionPointCreate, repo: ILocationRepository = Depends(get_location_repo)):
    return await repo.create_collection_point(req.model_dump())

@router.delete("/divisions/{division_id}", status_code=204)
async def delete_division(division_id: uuid.UUID, repo: ILocationRepository = Depends(get_location_repo)):
    success = await repo.delete_division(division_id)
    if not success: raise HTTPException(status_code=404, detail="Divisi tidak ditemukan")

@router.delete("/blocks/{block_id}", status_code=204)
async def delete_block(block_id: uuid.UUID, repo: ILocationRepository = Depends(get_location_repo)):
    success = await repo.delete_block(block_id)
    if not success: raise HTTPException(status_code=404, detail="Blok tidak ditemukan")

@router.delete("/points/{point_id}", status_code=204)
async def delete_collection_point(point_id: uuid.UUID, repo: ILocationRepository = Depends(get_location_repo)):
    success = await repo.delete_collection_point(point_id)
    if not success: raise HTTPException(status_code=404, detail="TPH tidak ditemukan")

@router.put("/divisions/{division_id}", response_model=DivisionResponse)
async def update_division(division_id: uuid.UUID, req: DivisionUpdate, repo: ILocationRepository = Depends(get_location_repo)):
    div = await repo.update_division(division_id, req.model_dump(exclude_unset=True))
    if not div: raise HTTPException(status_code=404, detail="Divisi tidak ditemukan")
    return div

@router.put("/blocks/{block_id}", response_model=BlockResponse)
async def update_block(block_id: uuid.UUID, req: BlockUpdate, repo: ILocationRepository = Depends(get_location_repo)):
    block = await repo.update_block(block_id, req.model_dump(exclude_unset=True))
    if not block: raise HTTPException(status_code=404, detail="Blok tidak ditemukan")
    return block

@router.put("/points/{point_id}", response_model=CollectionPointResponse)
async def update_collection_point(point_id: uuid.UUID, req: CollectionPointUpdate, repo: ILocationRepository = Depends(get_location_repo)):
    point = await repo.update_collection_point(point_id, req.model_dump(exclude_unset=True))
    if not point: raise HTTPException(status_code=404, detail="TPH tidak ditemukan")
    return point

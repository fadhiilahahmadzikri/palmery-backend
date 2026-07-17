from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from src.domain.repositories.harvest_repo_interface import IHarvestRepository
from src.domain.repositories.config_repo_interface import IConfigRepository
from src.api.dependencies import get_harvest_repo, get_config_repo
from src.domain.models.harvest import HarvestRecordResponse, HarvestRecordUpdateRequest, PaginatedHarvestRecordResponse
from src.domain.engine.premium_calculator import calculate_premium, HarvestConfig, TierConfig

router = APIRouter(prefix="/api/v1/records", tags=["records"])

@router.get("", response_model=PaginatedHarvestRecordResponse)
async def list_records(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=100), 
    search: str = Query(None, description="Search term for harvester name or tier status"),
    repo: IHarvestRepository = Depends(get_harvest_repo)
):
    records, total = await repo.get_records(skip=skip, limit=limit, search=search)
    return {"data": records, "total": total}

from fastapi.responses import StreamingResponse
from src.domain.services.exporter import ExcelExporter, WordExporter, PdfExporter

from datetime import datetime

@router.get("/export", response_class=StreamingResponse)
async def export_records(format: str = Query("xlsx", pattern="^(xlsx|docx|pdf)$"), repo: IHarvestRepository = Depends(get_harvest_repo)):
    records, _ = await repo.get_records(skip=0, limit=1000)
    
    date_str = datetime.now().strftime("%d-%b-%Y")
    base_filename = f"Laporan_Premi_{date_str}"
    
    if format == "xlsx":
        exporter = ExcelExporter()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{base_filename}.xlsx"
    elif format == "docx":
        exporter = WordExporter()
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{base_filename}.docx"
    elif format == "pdf":
        exporter = PdfExporter()
        media_type = "application/pdf"
        filename = f"{base_filename}.pdf"
    
    file_stream = exporter.generate(records)
    
    return StreamingResponse(
        file_stream,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{record_id}", response_model=HarvestRecordResponse)
async def get_record(record_id: uuid.UUID, repo: IHarvestRepository = Depends(get_harvest_repo)):
    record = await repo.get_record_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.put("/{record_id}", response_model=HarvestRecordResponse)
async def update_record(record_id: uuid.UUID, req: HarvestRecordUpdateRequest, repo: IHarvestRepository = Depends(get_harvest_repo)):
    # Note: A real app might re-run the calculation engine here if inputs change.
    updated = await repo.update_record(record_id, req.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Record not found")
    return updated

from pydantic import BaseModel

class BulkDeleteRequest(BaseModel):
    record_ids: List[uuid.UUID]

@router.delete("/{record_id}", status_code=204)
async def delete_record(record_id: uuid.UUID, repo: IHarvestRepository = Depends(get_harvest_repo)):
    success = await repo.delete_record(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    return None

@router.patch("/{record_id}", response_model=HarvestRecordResponse)
async def patch_record(
    record_id: uuid.UUID, 
    req: dict, 
    repo: IHarvestRepository = Depends(get_harvest_repo),
    config_repo: IConfigRepository = Depends(get_config_repo)
):
    record = await repo.get_record_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    safe_fields = {"harvester_name", "input_total_bunches", "input_avg_bunch_weight", "input_unripe_penalty", "harvest_date"}
    updates = {k: v for k, v in req.items() if k in safe_fields}
    
    if not updates:
        return record
        
    calculation_fields = {"input_total_bunches", "input_avg_bunch_weight", "input_unripe_penalty"}
    needs_recalc = any(k in calculation_fields for k in updates)
    
    if needs_recalc:
        total_bunches = updates.get("input_total_bunches", record.input_total_bunches)
        avg_bunch_weight = updates.get("input_avg_bunch_weight", record.input_avg_bunch_weight)
        unripe_penalty = updates.get("input_unripe_penalty", record.input_unripe_penalty)
        harvester_name = updates.get("harvester_name", record.harvester_name)
        
        db_configs = await config_repo.get_all_configs()
        config_map = {c.config_key: float(c.config_value) for c in db_configs}
        config = HarvestConfig(
            flat_rate_percentage=config_map.get("FLAT_RATE_PERCENTAGE", 0.10),
            loose_fruit_rate=config_map.get("LOOSE_FRUIT_RATE", 75.0),
            base_target_kg=config_map.get("BASE_TARGET_KG", 1000.0),
            min_bunches_required=int(config_map.get("MIN_BUNCHES_REQUIRED", 100))
        )
        
        db_tiers = await config_repo.get_all_tiers()
        tiers = [
            TierConfig(min_kg=float(t.min_kg), max_kg=float(t.max_kg) if t.max_kg else None, rate=float(t.rate_per_kg))
            for t in db_tiers
        ]
        
        result = calculate_premium(
            harvester_name=harvester_name,
            total_bunches=int(total_bunches),
            avg_bunch_weight=float(avg_bunch_weight),
            unripe_penalty=float(unripe_penalty),
            config=config,
            tiers=tiers
        )
        
        updates.update({
            "calc_total_tonnage": result.total_tonnage,
            "calc_loose_fruit_kg": result.loose_fruit_kg,
            "calc_net_ffb": result.net_ffb,
            "premium_loose_fruit": result.premium_loose_fruit,
            "premium_ffb": result.premium_ffb,
            "total_final_premium": result.total_final_premium,
            "tier_status": result.tier_status
        })

    updated = await repo.update_record(record_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Record not found")
    return updated

@router.delete("/bulk/delete", status_code=204)
async def bulk_delete_records(req: BulkDeleteRequest, repo: IHarvestRepository = Depends(get_harvest_repo)):
    # Using loop for demo provider, real DB would use IN clause
    for rid in req.record_ids:
        await repo.delete_record(rid)
    return None

class BulkExportRequest(BaseModel):
    record_ids: List[uuid.UUID]
    format: str = "xlsx"

@router.post("/bulk/export", response_class=StreamingResponse)
async def bulk_export_records(req: BulkExportRequest, repo: IHarvestRepository = Depends(get_harvest_repo)):
    records = []
    for rid in req.record_ids:
        record = await repo.get_record_by_id(rid)
        if record:
            records.append(record)
            
    if not records:
        raise HTTPException(status_code=404, detail="No records found for the given IDs")
        
    date_str = datetime.now().strftime("%d-%b-%Y")
    base_filename = f"Laporan_Terpilih_{date_str}"
    
    if req.format == "xlsx":
        exporter = ExcelExporter()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{base_filename}.xlsx"
    elif req.format == "docx":
        exporter = WordExporter()
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{base_filename}.docx"
    elif req.format == "pdf":
        exporter = PdfExporter()
        media_type = "application/pdf"
        filename = f"{base_filename}.pdf"
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
    
    file_stream = exporter.generate(records)
    
    return StreamingResponse(
        file_stream,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


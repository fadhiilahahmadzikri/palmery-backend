from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
import uuid

from src.domain.models.harvest import HarvestRecordCreate, HarvestRecordResponse, PaginatedHarvestRecordResponse
from src.domain.repositories.harvest_repo_interface import IHarvestRepository
from src.api.dependencies import get_harvest_repo

from src.domain.engine.ledger_calculator import calculate_daily_ledger
from src.domain.repositories.config_repo_interface import IConfigRepository
from src.api.dependencies import get_config_repo

router = APIRouter(prefix="/api/v1/records", tags=["harvest-records"])

@router.get("", response_model=PaginatedHarvestRecordResponse)
async def get_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: str = Query(None),
    repo: IHarvestRepository = Depends(get_harvest_repo)
):
    records, total = await repo.get_records(skip=skip, limit=limit, search=search)
    return PaginatedHarvestRecordResponse(data=records, total=total)

from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Tuple
from datetime import date, timedelta
import calendar
from src.domain.services.exporter.excel_exporter import ExcelExporter
from src.domain.services.exporter.pdf_exporter import PdfExporter
from src.domain.services.exporter.word_exporter import WordExporter

class ExportFilterRequest(BaseModel):
    format: str = "xlsx"  # "xlsx" | "pdf" | "docx"
    period_mode: str = "all"  # "all" | "current_week" | "last_week" | "current_month" | "last_month" | "current_year" | "last_year" | "specific_month" | "specific_year" | "custom"
    year: Optional[int] = None
    month: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    division_id: Optional[uuid.UUID] = None
    block_id: Optional[uuid.UUID] = None
    search: Optional[str] = None

def resolve_export_period(req: ExportFilterRequest) -> Tuple[Optional[date], Optional[date], Optional[str]]:
    today = date.today()
    mode = req.period_mode

    if mode == "current_week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        label = f"{start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')} (Minggu Ini)"
        return start, end, label
    elif mode == "last_week":
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        label = f"{start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')} (Minggu Lalu)"
        return start, end, label
    elif mode == "current_month":
        start = date(today.year, today.month, 1)
        _, last_day = calendar.monthrange(today.year, today.month)
        end = date(today.year, today.month, last_day)
        label = f"{start.strftime('%B %Y')} (Bulan Ini)"
        return start, end, label
    elif mode == "last_month":
        first_of_current = date(today.year, today.month, 1)
        last_of_prev = first_of_current - timedelta(days=1)
        start = date(last_of_prev.year, last_of_prev.month, 1)
        end = last_of_prev
        label = f"{start.strftime('%B %Y')} (Bulan Lalu)"
        return start, end, label
    elif mode == "current_year":
        start = date(today.year, 1, 1)
        end = date(today.year, 12, 31)
        label = f"Tahun {today.year}"
        return start, end, label
    elif mode == "last_year":
        yr = today.year - 1
        start = date(yr, 1, 1)
        end = date(yr, 12, 31)
        label = f"Tahun {yr}"
        return start, end, label
    elif mode == "specific_month":
        yr = req.year or today.year
        mo = req.month or today.month
        start = date(yr, mo, 1)
        _, last_day = calendar.monthrange(yr, mo)
        end = date(yr, mo, last_day)
        month_name = calendar.month_name[mo]
        label = f"{month_name} {yr}"
        return start, end, label
    elif mode == "specific_year":
        yr = req.year or today.year
        start = date(yr, 1, 1)
        end = date(yr, 12, 31)
        label = f"Tahun {yr}"
        return start, end, label
    elif mode == "custom":
        start = req.start_date
        end = req.end_date
        if start and end:
            label = f"{start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')}"
        elif start:
            label = f"Mulai {start.strftime('%d %b %Y')}"
        elif end:
            label = f"Sampai {end.strftime('%d %b %Y')}"
        else:
            label = "Semua Tanggal"
        return start, end, label
    else:
        return None, None, "Semua Data"

def generate_export_response(records: list, format: str, period_label: Optional[str]) -> StreamingResponse:
    if format == "pdf":
        exporter = PdfExporter()
        media_type = "application/pdf"
        filename = "laporan_premi.pdf"
    elif format == "docx":
        exporter = WordExporter()
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = "laporan_premi.docx"
    else:
        exporter = ExcelExporter()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "laporan_premi.xlsx"

    output = exporter.generate(records, period_label=period_label)

    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.post("/export")
async def export_records_post(
    req: ExportFilterRequest,
    repo: IHarvestRepository = Depends(get_harvest_repo)
):
    start_date, end_date, period_label = resolve_export_period(req)
    records = await repo.get_records_for_export(
        start_date=start_date,
        end_date=end_date,
        division_id=req.division_id,
        block_id=req.block_id,
        search=req.search
    )
    return generate_export_response(records, req.format, period_label)

@router.get("/export")
async def export_records(
    format: str = Query("xlsx"),
    search: str = Query(None),
    period_mode: str = Query("all"),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    division_id: Optional[uuid.UUID] = Query(None),
    block_id: Optional[uuid.UUID] = Query(None),
    repo: IHarvestRepository = Depends(get_harvest_repo)
):
    req = ExportFilterRequest(
        format=format,
        period_mode=period_mode,
        year=year,
        month=month,
        start_date=start_date,
        end_date=end_date,
        division_id=division_id,
        block_id=block_id,
        search=search
    )
    start_d, end_d, period_label = resolve_export_period(req)
    records = await repo.get_records_for_export(
        start_date=start_d,
        end_date=end_d,
        division_id=division_id,
        block_id=block_id,
        search=search
    )
    return generate_export_response(records, format, period_label)


from pydantic import BaseModel
class BulkExportReq(BaseModel):
    record_ids: List[uuid.UUID]
    format: str = "xlsx"

@router.post("/bulk/export")
async def bulk_export_records(
    req: BulkExportReq,
    repo: IHarvestRepository = Depends(get_harvest_repo)
):
    # In a real scenario we'd fetch only the selected IDs, but for simplicity here we fetch all and filter
    records, _ = await repo.get_records(skip=0, limit=1000)
    selected_records = [r for r in records if r.id in req.record_ids]
    
    exporter = ExcelExporter()
    output = exporter.generate(selected_records)
    
    return StreamingResponse(
        output, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": f'attachment; filename="Laporan_Terpilih.xlsx"'}
    )

from src.domain.repositories.harvester_repo_interface import IHarvesterRepository
from src.api.dependencies import get_harvester_repo

@router.post("", response_model=HarvestRecordResponse, status_code=201)
async def create_record(
    req: HarvestRecordCreate, 
    repo: IHarvestRepository = Depends(get_harvest_repo),
    config_repo: IConfigRepository = Depends(get_config_repo),
    harvester_repo: IHarvesterRepository = Depends(get_harvester_repo)
):
    harvester = await harvester_repo.get_harvester_by_id(req.harvester_id)
    if not harvester:
        raise HTTPException(status_code=400, detail="Invalid Harvester ID")
    
    if not harvester.block_id:
        raise HTTPException(status_code=400, detail="Harvester is not assigned to a block")

    # Retrieve configs to calculate ledger
    fine_config = await config_repo.get_active_fine_config()
    loose_config = await config_repo.get_active_loose_fruit_config()
    
    if not fine_config or not loose_config:
        raise HTTPException(status_code=400, detail="Active configs not found. Cannot calculate ledger.")

    # Execute business engine
    ledger_result = calculate_daily_ledger(
        valid_bunch_count=req.valid_bunch_count,
        unripe_bunch_count=req.unripe_bunch_count,
        avg_bunch_weight_kg=req.avg_bunch_weight_kg,
        loose_fruit_percentage=float(loose_config.flat_percentage),
        loose_fruit_rate_rupiah=float(loose_config.rate_per_kg_rupiah),
        fine_mode=fine_config.mode,
        fine_rate_rupiah=float(fine_config.rate_per_bunch_rupiah) if fine_config.rate_per_bunch_rupiah else 0.0
    )
    
    # Merge payload with calculation result
    data = req.model_dump()
    data.update({
        "block_id": harvester.block_id,
        "loose_fruit_percentage_snapshot": ledger_result.loose_fruit_percentage_snapshot,
        "loose_fruit_rate_snapshot_rupiah": ledger_result.loose_fruit_rate_snapshot_rupiah,
        "fine_mode_snapshot": ledger_result.fine_mode_snapshot,
        "fine_amount_rupiah": ledger_result.fine_amount_rupiah
    })
    
    try:
        return await repo.create_record(data)
    except Exception as e:
        from sqlalchemy.exc import IntegrityError
        if isinstance(e, IntegrityError):
            raise HTTPException(status_code=400, detail="Invalid reference: harvester_id, block_id, or point_id does not exist")
        raise e

@router.get("/{record_id}", response_model=HarvestRecordResponse)
async def get_record(record_id: uuid.UUID, repo: IHarvestRepository = Depends(get_harvest_repo)):
    record = await repo.get_record_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.delete("/{record_id}", status_code=204)
async def delete_record(record_id: uuid.UUID, repo: IHarvestRepository = Depends(get_harvest_repo)):
    try:
        success = await repo.delete_record(record_id)
        if not success:
            raise HTTPException(status_code=404, detail="Record not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

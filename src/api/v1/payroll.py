from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
import uuid
import collections
import io
import zipfile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.responses import StreamingResponse
from src.infrastructure.database.session import get_db
from src.infrastructure.database.models import Harvester, PayrollPeriod, PayrollTierDetail, PayrollSummary, PayrollBatch
from src.domain.services.exporter.slip_pdf_exporter import SlipPdfExporter
from src.domain.services.exporter.slip_excel_exporter import SlipExcelExporter
from src.domain.services.exporter.slip_word_exporter import SlipWordExporter

from src.domain.models.payroll import (
    PayrollPeriodCreate, PayrollPeriodResponse,
    PayrollSummaryResponse, PayrollBatchResponse
)
from src.domain.repositories.payroll_repo_interface import IPayrollRepository
from src.api.dependencies import get_payroll_repo

from src.domain.repositories.harvest_repo_interface import IHarvestRepository
from src.api.dependencies import get_harvest_repo

from src.domain.repositories.config_repo_interface import IConfigRepository
from src.api.dependencies import get_config_repo

from src.domain.engine.payroll_calculator import calculate_monthly_payroll, EligibilityConfigModel, TierModel

router = APIRouter(prefix="/api/v1/payroll", tags=["payroll"])

@router.post("/periods/open", response_model=PayrollPeriodResponse)
async def open_period(req: PayrollPeriodCreate, repo: IPayrollRepository = Depends(get_payroll_repo)):
    return await repo.get_or_create_open_period(req.year, req.month)

@router.post("/periods/{period_id}/close", response_model=PayrollPeriodResponse)
async def close_period(period_id: uuid.UUID, repo: IPayrollRepository = Depends(get_payroll_repo)):
    period = await repo.close_period(period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    return period

@router.get("/periods", response_model=List[dict])
async def get_periods_for_year(year: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from src.infrastructure.database.models import PayrollPeriod, PayrollBatch
    
    result = await db.execute(
        select(PayrollPeriod, PayrollBatch.status)
        .outerjoin(PayrollBatch, PayrollBatch.payroll_period_id == PayrollPeriod.id)
        .where(PayrollPeriod.year == year)
    )
    
    response = []
    for period, batch_status in result.all():
        response.append({
            "id": period.id,
            "year": period.year,
            "month": period.month,
            "is_closed": period.status == 'closed',
            "batch_status": batch_status or "empty"
        })
        
    return response

@router.get("/harvesters/{harvester_id}/summary", response_model=PayrollSummaryResponse)
async def get_harvester_summary_on_the_fly(
    harvester_id: uuid.UUID,
    year: int,
    month: int,
    harvest_repo: IHarvestRepository = Depends(get_harvest_repo),
    payroll_repo: IPayrollRepository = Depends(get_payroll_repo),
    config_repo: IConfigRepository = Depends(get_config_repo)
):
    from datetime import datetime
    
    # 1. Fetch records
    period = await payroll_repo.get_or_create_open_period(year, month)
    records = await harvest_repo.get_records_by_period_and_harvester(period.id, harvester_id)
    if not records:
        raise HTTPException(status_code=400, detail="No harvest records found for this harvester in the given month")
        
    # 2. Fetch configurations
    eligibility_conf = await config_repo.get_active_eligibility_config()
    tiers_conf = await config_repo.get_active_tiers()
    
    if not eligibility_conf:
        raise HTTPException(status_code=400, detail="Active eligibility config not found")
        
    eligibility_model = EligibilityConfigModel(
        basis_kg=float(eligibility_conf.basis_kg),
        min_bunch_count=eligibility_conf.min_bunch_count
    )
    
    tier_models = [
        TierModel(
            tier_level=t.tier_level,
            min_kg=float(t.min_kg),
            max_kg=float(t.max_kg) if t.max_kg is not None else None,
            rate_per_kg=float(t.rate_per_kg)
        )
        for t in tiers_conf
    ]
    
    # 3. Calculate
    total_valid = sum(r.valid_bunch_count for r in records)
    total_unripe = sum(r.unripe_bunch_count for r in records)
    total_net = sum(float(r.net_tonnage_kg) for r in records)
    total_loose_premium = sum(float(r.loose_fruit_premium_rupiah) for r in records)
    total_fine = sum(float(r.fine_amount_rupiah) for r in records)
    fine_mode_used = records[0].fine_mode_snapshot if records else "kg"
    
    result = calculate_monthly_payroll(
        total_valid_bunch_count=total_valid,
        total_unripe_bunch_count=total_unripe,
        total_net_tonnage_kg=total_net,
        total_loose_fruit_premium_rupiah=total_loose_premium,
        total_fine_rupiah=total_fine,
        fine_mode_used=fine_mode_used,
        eligibility=eligibility_model,
        tiers=tier_models
    )
    
    # 4. Return formatted response
    import uuid
    tier_details = [
        {
            "id": uuid.uuid4(),
            "tier_level": td.tier_level,
            "kg_in_tier": td.kg_in_tier,
            "rate_per_kg": td.rate_per_kg,
            "subtotal_rupiah": td.subtotal_rupiah
        } for td in result.tier_details
    ]
    
    return {
        "harvester_id": harvester_id,
        "total_valid_bunch_count": result.total_valid_bunch_count,
        "total_unripe_bunch_count": result.total_unripe_bunch_count,
        "total_net_tonnage_kg": result.total_net_tonnage_kg,
        "total_loose_fruit_premium_rupiah": result.total_loose_fruit_premium_rupiah,
        "fine_mode_used": result.fine_mode_used,
        "total_fine_rupiah": result.total_fine_rupiah,
        "total_tier_premium_rupiah": result.total_tier_premium_rupiah,
        "total_net_pay_rupiah": result.total_net_pay_rupiah,
        "generated_at": datetime.now(),
        "tier_details": tier_details,
        "daily_records": records
    }

@router.get("/harvesters/{harvester_id}/summary/export")
async def export_harvester_summary_on_the_fly(
    harvester_id: uuid.UUID,
    year: int,
    month: int,
    format: str = "pdf",
    harvest_repo: IHarvestRepository = Depends(get_harvest_repo),
    payroll_repo: IPayrollRepository = Depends(get_payroll_repo),
    config_repo: IConfigRepository = Depends(get_config_repo),
    db: AsyncSession = Depends(get_db)
):
    from src.infrastructure.database.models import Harvester
    from fastapi.responses import StreamingResponse
    import io
    
    # 1. Generate summary dict
    summary_dict = await get_harvester_summary_on_the_fly(harvester_id, year, month, harvest_repo, payroll_repo, config_repo)
    
    # 2. Fetch harvester name
    harvester_res = await db.execute(select(Harvester).where(Harvester.id == harvester_id))
    harvester = harvester_res.scalar_one_or_none()
    h_name = harvester.full_name if harvester else "Unknown"
    h_code = harvester.employee_number if harvester else "Unknown"
    
    # 3. Format period name
    month_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    period_name = f"{month_names[month - 1]} {year}"
    
    # 4. Construct mock object for Exporters
    class MockSummary:
        pass
    
    mock = MockSummary()
    for k, v in summary_dict.items():
        setattr(mock, k, v)
        
    class MockTier:
        def __init__(self, d):
            for k, v in d.items():
                setattr(self, k, v)
                
    mock.tier_details = [MockTier(t) for t in summary_dict['tier_details']]
    
    # 5. Generate file
    if format == "pdf":
        exp = SlipPdfExporter()
        media_type = "application/pdf"
        ext = "pdf"
    elif format == "excel":
        exp = SlipExcelExporter()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"
    elif format == "word":
        exp = SlipWordExporter()
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ext = "docx"
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use pdf, excel, or word.")
        
    file_bytes = exp.generate(mock, h_name, h_code, period_name)
    file_name = f"Slip_Gaji_{h_code}_{h_name}_{period_name}".replace(" ", "_")
    
    return StreamingResponse(
        iter([file_bytes.getvalue()]), 
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}.{ext}"'
        }
    )

@router.post("/periods/{period_id}/batches/generate", response_model=PayrollBatchResponse)
async def generate_payroll_batch(
    period_id: uuid.UUID,
    payroll_repo: IPayrollRepository = Depends(get_payroll_repo),
    harvest_repo: IHarvestRepository = Depends(get_harvest_repo),
    config_repo: IConfigRepository = Depends(get_config_repo),
    generated_by: str = "system_admin"
):
    # 1. Fetch all records for the period
    all_records = await harvest_repo.get_records_by_period(period_id)
    if not all_records:
        raise HTTPException(status_code=400, detail="No harvest records found for this period")
        
    # Group records by harvester_id
    grouped_records = collections.defaultdict(list)
    for r in all_records:
        grouped_records[r.harvester_id].append(r)
        
    # 2. Fetch configurations
    eligibility_conf = await config_repo.get_active_eligibility_config()
    tiers_conf = await config_repo.get_active_tiers()
    
    if not eligibility_conf:
        raise HTTPException(status_code=400, detail="Active eligibility config not found")
        
    eligibility_model = EligibilityConfigModel(
        basis_kg=float(eligibility_conf.basis_kg),
        min_bunch_count=eligibility_conf.min_bunch_count
    )
    
    tier_models = [
        TierModel(
            tier_level=t.tier_level,
            min_kg=float(t.min_kg),
            max_kg=float(t.max_kg) if t.max_kg is not None else None,
            rate_per_kg=float(t.rate_per_kg)
        )
        for t in tiers_conf
    ]
    
    # 3. Create the Batch
    batch = await payroll_repo.create_payroll_batch(period_id, generated_by)
    
    # 4. Calculate for each harvester in memory
    summaries_data = []
    tier_details_data_map = {}
    
    for harvester_id, records in grouped_records.items():
        total_valid = sum(r.valid_bunch_count for r in records)
        total_unripe = sum(r.unripe_bunch_count for r in records)
        total_net = sum(float(r.net_tonnage_kg) for r in records)
        total_loose_premium = sum(float(r.loose_fruit_premium_rupiah) for r in records)
        total_fine = sum(float(r.fine_amount_rupiah) for r in records)
        fine_mode_used = records[0].fine_mode_snapshot if records else "kg"
        
        result = calculate_monthly_payroll(
            total_valid_bunch_count=total_valid,
            total_unripe_bunch_count=total_unripe,
            total_net_tonnage_kg=total_net,
            total_loose_fruit_premium_rupiah=total_loose_premium,
            total_fine_rupiah=total_fine,
            fine_mode_used=fine_mode_used,
            eligibility=eligibility_model,
            tiers=tier_models
        )
        
        summaries_data.append({
            'harvester_id': harvester_id,
            'total_valid_bunch_count': result.total_valid_bunch_count,
            'total_unripe_bunch_count': result.total_unripe_bunch_count,
            'total_net_tonnage_kg': result.total_net_tonnage_kg,
            'total_loose_fruit_premium_rupiah': result.total_loose_fruit_premium_rupiah,
            'fine_mode_used': result.fine_mode_used,
            'total_fine_rupiah': result.total_fine_rupiah,
            'total_tier_premium_rupiah': result.total_tier_premium_rupiah,
            'total_net_pay_rupiah': result.total_net_pay_rupiah
        })
        
        tier_details_data_map[harvester_id] = [
            {
                'tier_level': td.tier_level,
                'kg_in_tier': td.kg_in_tier,
                'rate_per_kg': td.rate_per_kg,
                'subtotal_rupiah': td.subtotal_rupiah
            }
            for td in result.tier_details
        ]
        
    # 5. Bulk insert everything
    await payroll_repo.bulk_create_payroll_summaries(batch.id, summaries_data, tier_details_data_map)
    
    # 6. Update Batch status to generated
    batch = await payroll_repo.update_batch_status(batch.id, 'generated', generated_by, f"Calculated payroll for {len(grouped_records)} harvesters.")
    return batch

@router.get("/periods/{period_id}/batches", response_model=List[PayrollBatchResponse])
async def get_period_batches(
    period_id: uuid.UUID,
    payroll_repo: IPayrollRepository = Depends(get_payroll_repo)
):
    batches = await payroll_repo.get_batches_by_period(period_id)
    return batches

@router.post("/batches/{batch_id}/status", response_model=PayrollBatchResponse)
async def update_batch_status(
    batch_id: uuid.UUID,
    status: str,
    changed_by: str = "system_admin",
    notes: Optional[str] = None,
    payroll_repo: IPayrollRepository = Depends(get_payroll_repo)
):
    batch = await payroll_repo.update_batch_status(batch_id, status, changed_by, notes)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

@router.get("/batches/{batch_id}/summaries", response_model=List[PayrollSummaryResponse])
async def get_batch_summaries(
    batch_id: uuid.UUID,
    payroll_repo: IPayrollRepository = Depends(get_payroll_repo),
    harvest_repo: IHarvestRepository = Depends(get_harvest_repo),
    db: AsyncSession = Depends(get_db)
):
    summaries = await payroll_repo.get_summaries_by_batch(batch_id)
    batch = await payroll_repo.get_batch_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
        
    # Fetch tiers and daily records to attach for transparency
    # For a real enterprise system, doing this per summary could be slow,
    # but since it's just attaching them in memory, we can optimize by fetching all related records for the period.
    all_period_records = await harvest_repo.get_records_by_period(batch.payroll_period_id)
    records_map = collections.defaultdict(list)
    for r in all_period_records:
        records_map[r.harvester_id].append(r)
        
    for summary in summaries:
        setattr(summary, "daily_records", records_map.get(summary.harvester_id, []))
        
    return summaries

@router.get("/batches/{batch_id}/export")
async def export_batch(
    batch_id: uuid.UUID,
    format: str = "pdf",
    payroll_repo: IPayrollRepository = Depends(get_payroll_repo),
    harvest_repo: IHarvestRepository = Depends(get_harvest_repo),
    db: AsyncSession = Depends(get_db)
):
    batch = await payroll_repo.get_batch_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
        
    summaries = await payroll_repo.get_summaries_by_batch(batch_id)
    
    all_period_records = await harvest_repo.get_records_by_period(batch.payroll_period_id)
    records_map = collections.defaultdict(list)
    for r in all_period_records:
        records_map[r.harvester_id].append(r)
        
    period_res = await db.execute(select(PayrollPeriod).where(PayrollPeriod.id == batch.payroll_period_id))
    period = period_res.scalar_one_or_none()
    month_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    period_name = f"{month_names[period.month - 1]} {period.year}" if period else "Unknown"

    if format not in ["pdf", "excel", "docx"]:
        raise HTTPException(status_code=400, detail="Unsupported format. Use pdf, excel, or docx.")
        
    # Create exporters
    pdf_exp = SlipPdfExporter() if format == "pdf" else None
    excel_exp = SlipExcelExporter() if format == "excel" else None
    word_exp = SlipWordExporter() if format == "docx" else None

    # We will build a ZIP file in memory containing all documents
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for summary in summaries:
            harvester_res = await db.execute(select(Harvester).where(Harvester.id == summary.harvester_id))
            harvester = harvester_res.scalar_one_or_none()
            
            tiers_res = await db.execute(select(PayrollTierDetail).where(PayrollTierDetail.payroll_summary_id == summary.id))
            summary.tier_details = tiers_res.scalars().all()
            setattr(summary, "daily_records", records_map.get(summary.harvester_id, []))
            
            h_name = harvester.full_name if harvester else "Unknown"
            h_code = harvester.employee_number if harvester else "Unknown"
            
            file_name = f"Slip_Gaji_{h_code}_{h_name}_{period_name}".replace(" ", "_")
            
            if format == "pdf":
                file_bytes = pdf_exp.generate(summary, h_name, h_code, period_name)
                zip_file.writestr(f"{file_name}.pdf", file_bytes.getvalue())
            elif format == "excel":
                file_bytes = excel_exp.generate(summary, h_name, h_code, period_name)
                zip_file.writestr(f"{file_name}.xlsx", file_bytes.getvalue())
            elif format == "docx":
                file_bytes = word_exp.generate(summary, h_name, h_code, period_name)
                zip_file.writestr(f"{file_name}.docx", file_bytes.getvalue())

    return StreamingResponse(
        iter([zip_buffer.getvalue()]), 
        media_type="application/x-zip-compressed",
        headers={
            "Content-Disposition": f'attachment; filename="Payroll_Batch_{batch_id}_{period_name}.zip"'.replace(" ", "_")
        }
    )

from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import date, timedelta
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from src.infrastructure.database.session import get_db
from src.infrastructure.database.models import DailyHarvestRecord, Harvester, PayrollSummary

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

class DashboardSummaryResponse(BaseModel):
    total_tonnage_kg: float
    total_valid_bunches: int
    active_harvester_count: int
    total_payroll_rupiah: float
    avg_bjr_kg: float
    productivity_kg_per_harvester: float

class DashboardTrendItem(BaseModel):
    date: str
    label: str
    tonnage_kg: float
    valid_bunches: int
    premium_rupiah: float

@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    # 1. Base query for DailyHarvestRecords
    harvest_query = select(
        func.coalesce(func.sum(DailyHarvestRecord.gross_tonnage_kg), 0).label("total_tonnage"),
        func.coalesce(func.sum(DailyHarvestRecord.valid_bunch_count), 0).label("total_bunches"),
        func.count(distinct(DailyHarvestRecord.harvester_id)).label("active_harvester_in_records"),
        func.coalesce(
            func.sum(
                DailyHarvestRecord.loose_fruit_premium_rupiah - DailyHarvestRecord.fine_amount_rupiah
            ), 
            0
        ).label("net_premiums")
    )

    if start_date:
        harvest_query = harvest_query.where(DailyHarvestRecord.harvest_date >= start_date)
    if end_date:
        harvest_query = harvest_query.where(DailyHarvestRecord.harvest_date <= end_date)

    result = await db.execute(harvest_query)
    row = result.first()

    total_tonnage = float(row.total_tonnage) if row else 0.0
    total_bunches = int(row.total_bunches) if row else 0
    active_in_records = int(row.active_harvester_in_records) if row else 0
    net_premiums = float(row.net_premiums) if row else 0.0

    # 2. Total active harvesters count in system
    harvester_count_query = select(func.count(Harvester.id)).where(Harvester.is_active == True)
    harvester_res = await db.execute(harvester_count_query)
    total_active_harvesters = harvester_res.scalar() or 0

    # 3. Total Payroll Net Pay if available from PayrollSummary
    payroll_query = select(func.coalesce(func.sum(PayrollSummary.total_net_pay_rupiah), 0))
    payroll_res = await db.execute(payroll_query)
    total_payroll = float(payroll_res.scalar() or 0.0)

    # Use total_payroll if present in DB, otherwise use net_premiums
    final_payroll_value = total_payroll if total_payroll > 0 else max(0.0, net_premiums)

    # 4. Computed Metrics
    avg_bjr = round(total_tonnage / total_bunches, 2) if total_bunches > 0 else 0.0
    active_count = active_in_records if active_in_records > 0 else total_active_harvesters
    productivity = round(total_tonnage / active_count, 2) if active_count > 0 else 0.0

    return DashboardSummaryResponse(
        total_tonnage_kg=round(total_tonnage, 2),
        total_valid_bunches=total_bunches,
        active_harvester_count=active_count,
        total_payroll_rupiah=round(final_payroll_value, 2),
        avg_bjr_kg=avg_bjr,
        productivity_kg_per_harvester=productivity
    )


@router.get("/trends", response_model=List[DashboardTrendItem])
async def get_dashboard_trends(
    range: str = Query("90d", pattern="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db)
):
    days = 90
    if range == "7d":
        days = 7
    elif range == "30d":
        days = 30

    # Find max date in records for truthful range windowing
    max_date_res = await db.execute(select(func.max(DailyHarvestRecord.harvest_date)))
    max_date = max_date_res.scalar()
    
    if max_date:
        end_d = max_date
    else:
        end_d = date.today()

    start_d = end_d - timedelta(days=days - 1)

    # Truthful aggregation directly from DailyHarvestRecord table
    trend_query = select(
        DailyHarvestRecord.harvest_date,
        func.coalesce(func.sum(DailyHarvestRecord.gross_tonnage_kg), 0).label("tonnage_kg"),
        func.coalesce(func.sum(DailyHarvestRecord.valid_bunch_count), 0).label("valid_bunches"),
        func.coalesce(
            func.sum(DailyHarvestRecord.loose_fruit_premium_rupiah - DailyHarvestRecord.fine_amount_rupiah),
            0
        ).label("premium_rupiah")
    ).where(
        DailyHarvestRecord.harvest_date >= start_d,
        DailyHarvestRecord.harvest_date <= end_d
    ).group_by(
        DailyHarvestRecord.harvest_date
    ).order_by(
        DailyHarvestRecord.harvest_date.asc()
    )

    res = await db.execute(trend_query)
    db_rows = res.all()

    record_map = {}
    for r in db_rows:
        date_str = r.harvest_date.strftime("%Y-%m-%d")
        record_map[date_str] = {
            "tonnage_kg": float(r.tonnage_kg),
            "valid_bunches": int(r.valid_bunches),
            "premium_rupiah": max(0.0, float(r.premium_rupiah))
        }

    # Generate complete daily sequence for smooth chart rendering
    trend_items: List[DashboardTrendItem] = []
    curr_d = start_d
    months_id = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

    while curr_d <= end_d:
        d_str = curr_d.strftime("%Y-%m-%d")
        lbl = f"{curr_d.day:02d} {months_id[curr_d.month - 1]}"
        
        data = record_map.get(d_str, {"tonnage_kg": 0.0, "valid_bunches": 0, "premium_rupiah": 0.0})
        
        trend_items.append(DashboardTrendItem(
            date=d_str,
            label=lbl,
            tonnage_kg=round(data["tonnage_kg"], 2),
            valid_bunches=data["valid_bunches"],
            premium_rupiah=round(data["premium_rupiah"], 2)
        ))
        curr_d += timedelta(days=1)

    return trend_items

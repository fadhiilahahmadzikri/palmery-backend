from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from src.infrastructure.database.models import PayrollPeriod, PayrollSummary, PayrollTierDetail, PayrollBatch
from src.domain.repositories.payroll_repo_interface import IPayrollRepository

class PayrollRepository(IPayrollRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_open_period(self, year: int, month: int) -> PayrollPeriod:
        result = await self.db.execute(select(PayrollPeriod).where(
            PayrollPeriod.year == year,
            PayrollPeriod.month == month
        ))
        period = result.scalar_one_or_none()
        if not period:
            period = PayrollPeriod(year=year, month=month, status='open')
            self.db.add(period)
            await self.db.commit()
            await self.db.refresh(period)
        return period

    async def close_period(self, period_id: uuid.UUID) -> PayrollPeriod:
        result = await self.db.execute(select(PayrollPeriod).where(PayrollPeriod.id == period_id))
        period = result.scalar_one_or_none()
        if period:
            period.status = 'closed'
            period.closed_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(period)
        return period

    async def create_payroll_batch(self, period_id: uuid.UUID, generated_by: str) -> PayrollBatch:
        # Delete existing batch if any, to act as a pure refresh
        result = await self.db.execute(select(PayrollBatch).where(PayrollBatch.payroll_period_id == period_id))
        existing = result.scalar_one_or_none()
        if existing:
            await self.db.delete(existing)
            await self.db.flush()
            
        batch = PayrollBatch(
            payroll_period_id=period_id,
            status='draft',
            generated_by=generated_by,
            generated_at=datetime.now(timezone.utc)
        )
        self.db.add(batch)
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def update_batch_status(self, batch_id: uuid.UUID, status: str, changed_by: str, notes: Optional[str] = None) -> PayrollBatch:
        result = await self.db.execute(select(PayrollBatch).where(PayrollBatch.id == batch_id))
        batch = result.scalar_one_or_none()
        if not batch:
            return None
            
        batch.status = status
        
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def get_batches_by_period(self, period_id: uuid.UUID) -> List[PayrollBatch]:
        result = await self.db.execute(
            select(PayrollBatch)
            .where(PayrollBatch.payroll_period_id == period_id)
        )
        return result.scalars().all()

    async def get_batch_by_id(self, batch_id: uuid.UUID) -> Optional[PayrollBatch]:
        result = await self.db.execute(
            select(PayrollBatch)
            .where(PayrollBatch.id == batch_id)
        )
        return result.scalar_one_or_none()

    async def bulk_create_payroll_summaries(self, batch_id: uuid.UUID, summaries_data: List[dict], tier_details_data_map: dict) -> None:
        # bulk insert summaries
        summaries = []
        for data in summaries_data:
            summary = PayrollSummary(**data)
            summary.payroll_batch_id = batch_id
            summaries.append(summary)
            
        self.db.add_all(summaries)
        await self.db.flush() # flush to get summary IDs
        
        # bulk insert tiers
        all_tiers = []
        for summary in summaries:
            # Map back using harvester_id as the key in tier_details_data_map
            tiers_data = tier_details_data_map.get(summary.harvester_id, [])
            for t_data in tiers_data:
                tier = PayrollTierDetail(**t_data)
                tier.payroll_summary_id = summary.id
                all_tiers.append(tier)
                
        self.db.add_all(all_tiers)
        await self.db.commit()

    async def get_summaries_by_batch(self, batch_id: uuid.UUID) -> List[PayrollSummary]:
        result = await self.db.execute(
            select(PayrollSummary)
            .options(selectinload(PayrollSummary.tier_details))
            .where(PayrollSummary.payroll_batch_id == batch_id)
        )
        return result.scalars().all()

    async def get_summary_by_id(self, summary_id: uuid.UUID) -> Optional[PayrollSummary]:
        result = await self.db.execute(select(PayrollSummary).where(PayrollSummary.id == summary_id))
        return result.scalar_one_or_none()

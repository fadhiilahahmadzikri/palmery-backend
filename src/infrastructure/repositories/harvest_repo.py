from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from src.infrastructure.database.models import DailyHarvestRecord
from src.domain.repositories.harvest_repo_interface import IHarvestRepository

class HarvestRepository(IHarvestRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_records(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> Tuple[List[DailyHarvestRecord], int]:
        query = select(DailyHarvestRecord)
        
        total = await self.db.execute(select(func.count()).select_from(query.subquery()))
        
        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total.scalar()

    async def get_record_by_id(self, record_id: uuid.UUID) -> Optional[DailyHarvestRecord]:
        result = await self.db.execute(select(DailyHarvestRecord).where(DailyHarvestRecord.id == record_id))
        return result.scalar_one_or_none()

    async def create_record(self, data: dict) -> DailyHarvestRecord:
        db_obj = DailyHarvestRecord(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def _check_immutability(self, db_obj: DailyHarvestRecord):
        from src.infrastructure.database.models import PayrollPeriod, PayrollBatch
        # Check if period is closed based on harvest_date
        period = await self.db.execute(select(PayrollPeriod).where(
            PayrollPeriod.year == func.extract('year', db_obj.harvest_date),
            PayrollPeriod.month == func.extract('month', db_obj.harvest_date)
        ))
        p = period.scalar_one_or_none()
        if p and p.status == 'closed':
            raise ValueError("Cannot modify record: The payroll period is already closed.")
            
        # Check if there is an approved or paid batch for this period
        if p:
            batch_res = await self.db.execute(select(PayrollBatch).where(
                PayrollBatch.payroll_period_id == p.id,
                PayrollBatch.status.in_(['approved', 'paid'])
            ))
            if batch_res.first():
                raise ValueError("Cannot modify record: A payroll batch for this period is already approved or paid.")

    async def update_record(self, record_id: uuid.UUID, data: dict) -> Optional[DailyHarvestRecord]:
        db_obj = await self.get_record_by_id(record_id)
        if not db_obj:
            return None
            
        await self._check_immutability(db_obj)
            
        for key, value in data.items():
            setattr(db_obj, key, value)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_record(self, record_id: uuid.UUID) -> bool:
        db_obj = await self.get_record_by_id(record_id)
        if db_obj:
            await self._check_immutability(db_obj)
            await self.db.delete(db_obj)
            await self.db.commit()
            return True
        return False
        
    async def get_records_by_period(self, period_id: uuid.UUID) -> List[DailyHarvestRecord]:
        from src.infrastructure.database.models import PayrollPeriod
        period = await self.db.execute(select(PayrollPeriod).where(PayrollPeriod.id == period_id))
        p = period.scalar_one_or_none()
        if not p:
            return []
        
        result = await self.db.execute(
            select(DailyHarvestRecord).where(
                func.extract('year', DailyHarvestRecord.harvest_date) == p.year,
                func.extract('month', DailyHarvestRecord.harvest_date) == p.month
            )
        )
        return result.scalars().all()
        
    async def get_records_by_period_and_harvester(self, period_id: uuid.UUID, harvester_id: uuid.UUID) -> List[DailyHarvestRecord]:
        from src.infrastructure.database.models import PayrollPeriod
        period = await self.db.execute(select(PayrollPeriod).where(PayrollPeriod.id == period_id))
        p = period.scalar_one_or_none()
        if not p:
            return []
            
        result = await self.db.execute(
            select(DailyHarvestRecord).where(
                func.extract('year', DailyHarvestRecord.harvest_date) == p.year,
                func.extract('month', DailyHarvestRecord.harvest_date) == p.month,
                DailyHarvestRecord.harvester_id == harvester_id
            )
        )
        return result.scalars().all()

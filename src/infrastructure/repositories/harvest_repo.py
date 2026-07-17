from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, func, or_, cast, String
from src.infrastructure.database.models import DailyHarvestRecord
from src.domain.repositories.harvest_repo_interface import IHarvestRepository
import uuid

class HarvestRepository(IHarvestRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_record(self, data: dict) -> DailyHarvestRecord:
        record = DailyHarvestRecord(**data)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_records(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> Tuple[List[DailyHarvestRecord], int]:
        query = select(DailyHarvestRecord)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    DailyHarvestRecord.harvester_name.ilike(search_term),
                    DailyHarvestRecord.tier_status.ilike(search_term),
                    cast(DailyHarvestRecord.harvest_date, String).ilike(search_term)
                )
            )
            
        # Get total count matching criteria
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Get paginated data
        paginated_query = query.order_by(DailyHarvestRecord.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(paginated_query)
        records = list(result.scalars().all())
        
        return records, total_count

    async def get_record_by_id(self, record_id: uuid.UUID) -> Optional[DailyHarvestRecord]:
        result = await self.session.execute(select(DailyHarvestRecord).where(DailyHarvestRecord.id == record_id))
        return result.scalar_one_or_none()

    async def update_record(self, record_id: uuid.UUID, data: dict) -> Optional[DailyHarvestRecord]:
        record = await self.get_record_by_id(record_id)
        if record:
            for key, value in data.items():
                if value is not None:
                    setattr(record, key, value)
            await self.session.commit()
            await self.session.refresh(record)
        return record

    async def delete_record(self, record_id: uuid.UUID) -> bool:
        result = await self.session.execute(delete(DailyHarvestRecord).where(DailyHarvestRecord.id == record_id))
        await self.session.commit()
        return result.rowcount > 0

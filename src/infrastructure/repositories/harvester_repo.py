from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.infrastructure.database.models import Harvester
from src.domain.repositories.harvester_repo_interface import IHarvesterRepository

class HarvesterRepository(IHarvesterRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_harvesters(self, skip: int = 0, limit: int = 100) -> List[Harvester]:
        result = await self.db.execute(select(Harvester).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_harvester_by_id(self, harvester_id: uuid.UUID) -> Optional[Harvester]:
        result = await self.db.execute(select(Harvester).where(Harvester.id == harvester_id))
        return result.scalar_one_or_none()

    async def create_harvester(self, data: dict) -> Harvester:
        db_obj = Harvester(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_harvester(self, harvester_id: uuid.UUID, data: dict) -> Optional[Harvester]:
        db_obj = await self.get_harvester_by_id(harvester_id)
        if not db_obj:
            return None
        for key, value in data.items():
            setattr(db_obj, key, value)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def _has_dependencies(self, harvester_id: uuid.UUID) -> bool:
        from src.infrastructure.database.models import DailyHarvestRecord, PayrollSummary
        from sqlalchemy import func

        harvest_count_res = await self.db.execute(
            select(func.count(DailyHarvestRecord.id)).where(DailyHarvestRecord.harvester_id == harvester_id)
        )
        if (harvest_count_res.scalar() or 0) > 0:
            return True

        payroll_count_res = await self.db.execute(
            select(func.count(PayrollSummary.id)).where(PayrollSummary.harvester_id == harvester_id)
        )
        if (payroll_count_res.scalar() or 0) > 0:
            return True

        return False

    async def delete_harvester(self, harvester_id: uuid.UUID) -> bool:
        db_obj = await self.get_harvester_by_id(harvester_id)
        if not db_obj:
            return False

        has_deps = await self._has_dependencies(harvester_id)
        if has_deps:
            # Soft deactivation for harvesters with business history
            db_obj.is_active = False
            await self.db.commit()
            return True
        else:
            # Hard delete for unreferenced harvesters
            await self.db.delete(db_obj)
            await self.db.commit()
            return True

    async def bulk_delete_harvesters(self, harvester_ids: List[uuid.UUID]) -> dict:
        hard_deleted = []
        deactivated = []

        for h_id in harvester_ids:
            db_obj = await self.get_harvester_by_id(h_id)
            if not db_obj:
                continue

            has_deps = await self._has_dependencies(h_id)
            if has_deps:
                db_obj.is_active = False
                deactivated.append(str(h_id))
            else:
                await self.db.delete(db_obj)
                hard_deleted.append(str(h_id))

        if hard_deleted or deactivated:
            await self.db.commit()

        return {
            "hard_deleted_count": len(hard_deleted),
            "deactivated_count": len(deactivated),
            "hard_deleted_ids": hard_deleted,
            "deactivated_ids": deactivated
        }

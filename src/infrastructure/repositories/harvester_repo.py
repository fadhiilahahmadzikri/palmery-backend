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

    async def delete_harvester(self, harvester_id: uuid.UUID) -> bool:
        db_obj = await self.get_harvester_by_id(harvester_id)
        if not db_obj:
            return False
        await self.db.delete(db_obj)
        await self.db.commit()
        return True

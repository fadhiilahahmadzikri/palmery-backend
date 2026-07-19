from typing import List, Optional
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.infrastructure.database.models import Division, Block, CollectionPoint
from src.domain.repositories.location_repo_interface import ILocationRepository

logger = logging.getLogger(__name__)


class LocationRepository(ILocationRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_divisions(self) -> List[Division]:
        result = await self.db.execute(select(Division))
        return result.scalars().all()

    async def create_division(self, data: dict) -> Division:
        db_obj = Division(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_blocks_by_division(self, division_id: uuid.UUID) -> List[Block]:
        result = await self.db.execute(select(Block).where(Block.division_id == division_id))
        return result.scalars().all()

    async def create_block(self, data: dict) -> Block:
        db_obj = Block(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_points_by_block(self, block_id: uuid.UUID) -> List[CollectionPoint]:
        result = await self.db.execute(select(CollectionPoint).where(CollectionPoint.block_id == block_id))
        return result.scalars().all()

    async def create_collection_point(self, data: dict) -> CollectionPoint:
        db_obj = CollectionPoint(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_collection_point(self, point_id: uuid.UUID) -> bool:
        point = await self.db.get(CollectionPoint, point_id)
        if not point:
            return False
        await self.db.delete(point)
        await self.db.commit()
        return True

    async def delete_block(self, block_id: uuid.UUID) -> bool:
        block = await self.db.get(Block, block_id)
        if not block:
            return False
        await self.db.delete(block)
        await self.db.commit()
        return True

    async def delete_division(self, division_id: uuid.UUID) -> bool:
        div = await self.db.get(Division, division_id)
        if not div:
            return False
        await self.db.delete(div)
        await self.db.commit()
        return True

    async def update_division(self, division_id: uuid.UUID, data: dict) -> Optional[Division]:
        div = await self.db.get(Division, division_id)
        if not div:
            return None
        for key, value in data.items():
            setattr(div, key, value)
        await self.db.commit()
        await self.db.refresh(div)
        return div

    async def update_block(self, block_id: uuid.UUID, data: dict) -> Optional[Block]:
        block = await self.db.get(Block, block_id)
        if not block:
            return None
        for key, value in data.items():
            setattr(block, key, value)
        await self.db.commit()
        await self.db.refresh(block)
        return block

    async def update_collection_point(self, point_id: uuid.UUID, data: dict) -> Optional[CollectionPoint]:
        point = await self.db.get(CollectionPoint, point_id)
        if not point:
            return None
        for key, value in data.items():
            setattr(point, key, value)
        await self.db.commit()
        await self.db.refresh(point)
        return point

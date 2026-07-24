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

    async def _check_point_dependencies(self, point_id: uuid.UUID):
        from src.infrastructure.database.models import DailyHarvestRecord
        from sqlalchemy import func
        res = await self.db.execute(select(func.count(DailyHarvestRecord.id)).where(DailyHarvestRecord.collection_point_id == point_id))
        if (res.scalar() or 0) > 0:
            raise ValueError("TPH tidak dapat dihapus karena masih memiliki Laporan Rekap Panen terhubung.")

    async def _check_block_dependencies(self, block_id: uuid.UUID):
        from src.infrastructure.database.models import CollectionPoint, Harvester, DailyHarvestRecord
        from sqlalchemy import func
        cp_res = await self.db.execute(select(func.count(CollectionPoint.id)).where(CollectionPoint.block_id == block_id))
        if (cp_res.scalar() or 0) > 0:
            raise ValueError("Blok tidak dapat dihapus karena masih memiliki TPH terhubung.")

        h_res = await self.db.execute(select(func.count(Harvester.id)).where(Harvester.block_id == block_id))
        if (h_res.scalar() or 0) > 0:
            raise ValueError("Blok tidak dapat dihapus karena masih memiliki Pemanen terhubung.")

        hr_res = await self.db.execute(select(func.count(DailyHarvestRecord.id)).where(DailyHarvestRecord.block_id == block_id))
        if (hr_res.scalar() or 0) > 0:
            raise ValueError("Blok tidak dapat dihapus karena masih memiliki Laporan Rekap Panen terhubung.")

    async def _check_division_dependencies(self, division_id: uuid.UUID):
        from src.infrastructure.database.models import Block, Harvester
        from sqlalchemy import func
        b_res = await self.db.execute(select(func.count(Block.id)).where(Block.division_id == division_id))
        if (b_res.scalar() or 0) > 0:
            raise ValueError("Divisi tidak dapat dihapus karena masih memiliki Blok Panen terhubung.")

        h_res = await self.db.execute(select(func.count(Harvester.id)).where(Harvester.division_id == division_id))
        if (h_res.scalar() or 0) > 0:
            raise ValueError("Divisi tidak dapat dihapus karena masih memiliki Pemanen terhubung.")

    async def delete_collection_point(self, point_id: uuid.UUID) -> bool:
        point = await self.db.get(CollectionPoint, point_id)
        if not point:
            return False
        await self._check_point_dependencies(point_id)
        await self.db.delete(point)
        await self.db.commit()
        return True

    async def delete_block(self, block_id: uuid.UUID) -> bool:
        block = await self.db.get(Block, block_id)
        if not block:
            return False
        await self._check_block_dependencies(block_id)
        await self.db.delete(block)
        await self.db.commit()
        return True

    async def delete_division(self, division_id: uuid.UUID) -> bool:
        div = await self.db.get(Division, division_id)
        if not div:
            return False
        await self._check_division_dependencies(division_id)
        await self.db.delete(div)
        await self.db.commit()
        return True

    async def bulk_delete_divisions(self, division_ids: List[uuid.UUID]) -> dict:
        deleted_ids, blocked_ids, errors = [], [], []
        for div_id in division_ids:
            div = await self.db.get(Division, div_id)
            if not div: continue
            try:
                await self._check_division_dependencies(div_id)
                await self.db.delete(div)
                deleted_ids.append(str(div_id))
            except ValueError as ve:
                blocked_ids.append(str(div_id))
                errors.append(f"Divisi {div_id}: {str(ve)}")
        if deleted_ids: await self.db.commit()
        return {"deleted_count": len(deleted_ids), "blocked_count": len(blocked_ids), "deleted_ids": deleted_ids, "blocked_ids": blocked_ids, "errors": errors}

    async def bulk_delete_blocks(self, block_ids: List[uuid.UUID]) -> dict:
        deleted_ids, blocked_ids, errors = [], [], []
        for b_id in block_ids:
            blk = await self.db.get(Block, b_id)
            if not blk: continue
            try:
                await self._check_block_dependencies(b_id)
                await self.db.delete(blk)
                deleted_ids.append(str(b_id))
            except ValueError as ve:
                blocked_ids.append(str(b_id))
                errors.append(f"Blok {b_id}: {str(ve)}")
        if deleted_ids: await self.db.commit()
        return {"deleted_count": len(deleted_ids), "blocked_count": len(blocked_ids), "deleted_ids": deleted_ids, "blocked_ids": blocked_ids, "errors": errors}

    async def bulk_delete_points(self, point_ids: List[uuid.UUID]) -> dict:
        deleted_ids, blocked_ids, errors = [], [], []
        for p_id in point_ids:
            pt = await self.db.get(CollectionPoint, p_id)
            if not pt: continue
            try:
                await self._check_point_dependencies(p_id)
                await self.db.delete(pt)
                deleted_ids.append(str(p_id))
            except ValueError as ve:
                blocked_ids.append(str(p_id))
                errors.append(f"TPH {p_id}: {str(ve)}")
        if deleted_ids: await self.db.commit()
        return {"deleted_count": len(deleted_ids), "blocked_count": len(blocked_ids), "deleted_ids": deleted_ids, "blocked_ids": blocked_ids, "errors": errors}

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

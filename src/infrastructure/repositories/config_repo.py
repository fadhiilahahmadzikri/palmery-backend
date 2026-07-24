from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.infrastructure.database.models import (
    FineConfiguration, LooseFruitConfiguration, 
    PremiumEligibilityConfiguration, ProgressiveTier
)
from src.domain.repositories.config_repo_interface import IConfigRepository

class ConfigRepository(IConfigRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_fine_config(self) -> FineConfiguration:
        import uuid
        from datetime import date, datetime, timezone
        query = select(FineConfiguration).where(
            FineConfiguration.effective_until.is_(None)
        ).order_by(FineConfiguration.effective_from.desc()).limit(1)
        result = await self.db.execute(query)
        cfg = result.scalar()
        if cfg is None:
            cfg = FineConfiguration(id=uuid.uuid4(), mode="rupiah", rate_per_bunch_rupiah=5000, effective_from=date(2026, 1, 1), created_at=datetime.now(timezone.utc))
        return cfg
        
    async def get_active_loose_fruit_config(self) -> LooseFruitConfiguration:
        import uuid
        from datetime import date, datetime, timezone
        query = select(LooseFruitConfiguration).where(
            LooseFruitConfiguration.effective_until.is_(None)
        ).order_by(LooseFruitConfiguration.effective_from.desc()).limit(1)
        result = await self.db.execute(query)
        cfg = result.scalar()
        if cfg is None:
            cfg = LooseFruitConfiguration(id=uuid.uuid4(), flat_percentage=0.10, rate_per_kg_rupiah=75.0, effective_from=date(2026, 1, 1), created_at=datetime.now(timezone.utc))
        return cfg
        
    async def get_active_eligibility_config(self) -> Optional[PremiumEligibilityConfiguration]:
        query = select(PremiumEligibilityConfiguration).where(
            PremiumEligibilityConfiguration.effective_until.is_(None)
        ).order_by(PremiumEligibilityConfiguration.effective_from.desc()).limit(1)
        result = await self.db.execute(query)
        return result.scalar()

    async def get_active_tiers(self) -> List[ProgressiveTier]:
        result = await self.db.execute(
            select(ProgressiveTier).where(ProgressiveTier.effective_until.is_(None)).order_by(ProgressiveTier.tier_level)
        )
        return result.scalars().all()

    async def create_fine_config(self, data: dict) -> FineConfiguration:
        db_obj = FineConfiguration(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def create_loose_fruit_config(self, data: dict) -> LooseFruitConfiguration:
        db_obj = LooseFruitConfiguration(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def create_eligibility_config(self, data: dict) -> PremiumEligibilityConfiguration:
        db_obj = PremiumEligibilityConfiguration(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def create_tier(self, data: dict) -> ProgressiveTier:
        db_obj = ProgressiveTier(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_tier(self, tier_id: int, data: dict) -> Optional[ProgressiveTier]:
        result = await self.db.execute(select(ProgressiveTier).where(ProgressiveTier.id == tier_id))
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return None
        for key, value in data.items():
            setattr(db_obj, key, value)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_tier(self, tier_id: int) -> bool:
        result = await self.db.execute(select(ProgressiveTier).where(ProgressiveTier.id == tier_id))
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return False
        await self.db.delete(db_obj)
        await self.db.commit()
        return True

    async def bulk_delete_tiers(self, tier_ids: List[int]) -> dict:
        deleted_ids = []
        for t_id in tier_ids:
            result = await self.db.execute(select(ProgressiveTier).where(ProgressiveTier.id == t_id))
            db_obj = result.scalar_one_or_none()
            if db_obj:
                await self.db.delete(db_obj)
                deleted_ids.append(t_id)
        if deleted_ids:
            await self.db.commit()
        return {"deleted_count": len(deleted_ids), "deleted_ids": deleted_ids}

    async def delete_fine_config(self, config_id: uuid.UUID) -> bool:
        result = await self.db.execute(select(FineConfiguration).where(FineConfiguration.id == config_id))
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return False
        await self.db.delete(db_obj)
        await self.db.commit()
        return True

    async def delete_loose_fruit_config(self, config_id: uuid.UUID) -> bool:
        result = await self.db.execute(select(LooseFruitConfiguration).where(LooseFruitConfiguration.id == config_id))
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return False
        await self.db.delete(db_obj)
        await self.db.commit()
        return True

    async def delete_eligibility_config(self, config_id: uuid.UUID) -> bool:
        result = await self.db.execute(select(PremiumEligibilityConfiguration).where(PremiumEligibilityConfiguration.id == config_id))
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return False
        await self.db.delete(db_obj)
        await self.db.commit()
        return True

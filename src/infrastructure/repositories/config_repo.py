from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from src.infrastructure.database.models import AppConfig, ProgressiveTier
from src.domain.repositories.config_repo_interface import IConfigRepository

class ConfigRepository(IConfigRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- App Config ---
    async def get_all_configs(self) -> List[AppConfig]:
        result = await self.session.execute(select(AppConfig))
        return list(result.scalars().all())

    async def get_config_by_id(self, config_id: int) -> Optional[AppConfig]:
        result = await self.session.execute(select(AppConfig).where(AppConfig.id == config_id))
        return result.scalar_one_or_none()

    async def create_config(self, data: dict) -> AppConfig:
        config = AppConfig(**data)
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def update_config(self, key: str, value: float) -> Optional[AppConfig]:
        result = await self.session.execute(select(AppConfig).where(AppConfig.config_key == key))
        config = result.scalar_one_or_none()
        if config:
            config.config_value = value
            await self.session.commit()
            await self.session.refresh(config)
        return config

    async def delete_config(self, config_id: int) -> bool:
        result = await self.session.execute(delete(AppConfig).where(AppConfig.id == config_id))
        await self.session.commit()
        return result.rowcount > 0

    # --- Progressive Tiers ---
    async def get_all_tiers(self) -> List[ProgressiveTier]:
        result = await self.session.execute(select(ProgressiveTier).order_by(ProgressiveTier.tier_level))
        return list(result.scalars().all())

    async def get_tier_by_id(self, tier_id: int) -> Optional[ProgressiveTier]:
        result = await self.session.execute(select(ProgressiveTier).where(ProgressiveTier.id == tier_id))
        return result.scalar_one_or_none()

    async def create_tier(self, data: dict) -> ProgressiveTier:
        tier = ProgressiveTier(**data)
        self.session.add(tier)
        await self.session.commit()
        await self.session.refresh(tier)
        return tier

    async def update_tier(self, tier_id: int, data: dict) -> Optional[ProgressiveTier]:
        tier = await self.get_tier_by_id(tier_id)
        if tier:
            for key, value in data.items():
                if value is not None:
                    setattr(tier, key, value)
            await self.session.commit()
            await self.session.refresh(tier)
        return tier

    async def delete_tier(self, tier_id: int) -> bool:
        result = await self.session.execute(delete(ProgressiveTier).where(ProgressiveTier.id == tier_id))
        await self.session.commit()
        return result.rowcount > 0

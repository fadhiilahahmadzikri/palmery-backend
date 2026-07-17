from abc import ABC, abstractmethod
from typing import List, Optional
from src.infrastructure.database.models import AppConfig, ProgressiveTier

class IConfigRepository(ABC):
    @abstractmethod
    async def get_all_configs(self) -> List[AppConfig]:
        pass

    @abstractmethod
    async def get_config_by_id(self, config_id: int) -> Optional[AppConfig]:
        pass

    @abstractmethod
    async def create_config(self, data: dict) -> AppConfig:
        pass

    @abstractmethod
    async def update_config(self, key: str, value: float) -> Optional[AppConfig]:
        pass

    @abstractmethod
    async def delete_config(self, config_id: int) -> bool:
        pass

    @abstractmethod
    async def get_all_tiers(self) -> List[ProgressiveTier]:
        pass

    @abstractmethod
    async def get_tier_by_id(self, tier_id: int) -> Optional[ProgressiveTier]:
        pass

    @abstractmethod
    async def create_tier(self, data: dict) -> ProgressiveTier:
        pass

    @abstractmethod
    async def update_tier(self, tier_id: int, data: dict) -> Optional[ProgressiveTier]:
        pass

    @abstractmethod
    async def delete_tier(self, tier_id: int) -> bool:
        pass

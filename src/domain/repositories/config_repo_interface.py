from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from src.infrastructure.database.models import (
    FineConfiguration, LooseFruitConfiguration, 
    PremiumEligibilityConfiguration, ProgressiveTier
)

class IConfigRepository(ABC):
    @abstractmethod
    async def get_active_fine_config(self) -> Optional[FineConfiguration]:
        pass
        
    @abstractmethod
    async def get_active_loose_fruit_config(self) -> Optional[LooseFruitConfiguration]:
        pass
        
    @abstractmethod
    async def get_active_eligibility_config(self) -> Optional[PremiumEligibilityConfiguration]:
        pass

    @abstractmethod
    async def get_active_tiers(self) -> List[ProgressiveTier]:
        pass
        
    @abstractmethod
    async def create_fine_config(self, data: dict) -> FineConfiguration:
        pass

    @abstractmethod
    async def create_loose_fruit_config(self, data: dict) -> LooseFruitConfiguration:
        pass

    @abstractmethod
    async def create_eligibility_config(self, data: dict) -> PremiumEligibilityConfiguration:
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

    @abstractmethod
    async def bulk_delete_tiers(self, tier_ids: List[int]) -> dict:
        pass

    @abstractmethod
    async def delete_fine_config(self, config_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def delete_loose_fruit_config(self, config_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def delete_eligibility_config(self, config_id: uuid.UUID) -> bool:
        pass

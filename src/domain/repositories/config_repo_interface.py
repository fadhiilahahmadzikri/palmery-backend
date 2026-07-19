from abc import ABC, abstractmethod
from typing import List, Optional
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

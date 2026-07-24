from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from src.infrastructure.database.models import Harvester

class IHarvesterRepository(ABC):
    @abstractmethod
    async def get_harvesters(self, skip: int = 0, limit: int = 100) -> List[Harvester]:
        pass

    @abstractmethod
    async def get_harvester_by_id(self, harvester_id: uuid.UUID) -> Optional[Harvester]:
        pass

    @abstractmethod
    async def create_harvester(self, data: dict) -> Harvester:
        pass

    @abstractmethod
    async def update_harvester(self, harvester_id: uuid.UUID, data: dict) -> Optional[Harvester]:
        pass

    @abstractmethod
    async def delete_harvester(self, harvester_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def bulk_delete_harvesters(self, harvester_ids: List[uuid.UUID]) -> dict:
        pass

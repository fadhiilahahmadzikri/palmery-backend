from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import uuid
from src.infrastructure.database.models import DailyHarvestRecord

class IHarvestRepository(ABC):
    @abstractmethod
    async def get_records(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> Tuple[List[DailyHarvestRecord], int]:
        pass

    @abstractmethod
    async def get_record_by_id(self, record_id: uuid.UUID) -> Optional[DailyHarvestRecord]:
        pass

    @abstractmethod
    async def create_record(self, data: dict) -> DailyHarvestRecord:
        pass

    @abstractmethod
    async def update_record(self, record_id: uuid.UUID, data: dict) -> Optional[DailyHarvestRecord]:
        pass

    @abstractmethod
    async def delete_record(self, record_id: uuid.UUID) -> bool:
        pass

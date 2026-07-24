from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import date
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

    @abstractmethod
    async def bulk_delete_records(self, record_ids: List[uuid.UUID]) -> dict:
        pass
    
    @abstractmethod
    async def get_records_by_period(self, period_id: uuid.UUID) -> List[DailyHarvestRecord]:
        pass
        
    @abstractmethod
    async def get_records_by_period_and_harvester(self, period_id: uuid.UUID, harvester_id: uuid.UUID) -> List[DailyHarvestRecord]:
        pass

    @abstractmethod
    async def get_records_for_export(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        division_id: Optional[uuid.UUID] = None,
        block_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None
    ) -> List[DailyHarvestRecord]:
        pass

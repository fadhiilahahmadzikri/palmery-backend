from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from src.infrastructure.database.models import PayrollPeriod, PayrollSummary, PayrollBatch

# Valid batch statuses (simplified):
#   'draft'  — kalkulasi sedang berjalan / preview, data masih bisa berubah
#   'final'  — kalkulasi dikunci, siap ekspor resmi
# Backward-compatible: 'generated', 'approved', 'paid' diperlakukan sama seperti statusnya
# saat dibaca di UI (lihat helper normalize_batch_status di payroll.py).

VALID_BATCH_STATUSES = {'draft', 'final'}

class IPayrollRepository(ABC):
    @abstractmethod
    async def get_or_create_open_period(self, year: int, month: int) -> PayrollPeriod:
        pass

    @abstractmethod
    async def get_current_period(self) -> PayrollPeriod:
        """Return (or create) the PayrollPeriod for the current calendar month."""
        pass

    @abstractmethod
    async def create_payroll_batch(self, period_id: uuid.UUID, generated_by: str) -> PayrollBatch:
        pass

    @abstractmethod
    async def finalize_batch(self, batch_id: uuid.UUID) -> Optional[PayrollBatch]:
        """Lock a draft batch so it becomes final (irreversible)."""
        pass

    @abstractmethod
    async def update_batch_status(self, batch_id: uuid.UUID, status: str, changed_by: str, notes: Optional[str] = None) -> PayrollBatch:
        pass

    @abstractmethod
    async def get_batches_by_period(self, period_id: uuid.UUID) -> List[PayrollBatch]:
        pass

    @abstractmethod
    async def get_batch_by_id(self, batch_id: uuid.UUID) -> Optional[PayrollBatch]:
        pass

    @abstractmethod
    async def bulk_create_payroll_summaries(self, batch_id: uuid.UUID, summaries_data: List[dict], tier_details_data_map: dict) -> None:
        pass

    @abstractmethod
    async def get_summaries_by_batch(self, batch_id: uuid.UUID) -> List[PayrollSummary]:
        pass

    @abstractmethod
    async def get_summary_by_id(self, summary_id: uuid.UUID) -> Optional[PayrollSummary]:
        pass

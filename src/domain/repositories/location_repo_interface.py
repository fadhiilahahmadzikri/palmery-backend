from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from src.infrastructure.database.models import Division, Block, CollectionPoint

class ILocationRepository(ABC):
    @abstractmethod
    async def get_divisions(self) -> List[Division]:
        pass

    @abstractmethod
    async def create_division(self, data: dict) -> Division:
        pass

    @abstractmethod
    async def get_blocks_by_division(self, division_id: uuid.UUID) -> List[Block]:
        pass

    @abstractmethod
    async def create_block(self, data: dict) -> Block:
        pass

    @abstractmethod
    async def get_points_by_block(self, block_id: uuid.UUID) -> List[CollectionPoint]:
        pass

    @abstractmethod
    async def create_collection_point(self, data: dict) -> CollectionPoint:
        pass

    @abstractmethod
    async def delete_division(self, division_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def delete_block(self, block_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def delete_collection_point(self, point_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def bulk_delete_divisions(self, division_ids: List[uuid.UUID]) -> dict:
        pass

    @abstractmethod
    async def bulk_delete_blocks(self, block_ids: List[uuid.UUID]) -> dict:
        pass

    @abstractmethod
    async def bulk_delete_points(self, point_ids: List[uuid.UUID]) -> dict:
        pass

    @abstractmethod
    async def update_division(self, division_id: uuid.UUID, data: dict) -> Optional[Division]:
        pass

    @abstractmethod
    async def update_block(self, block_id: uuid.UUID, data: dict) -> Optional[Block]:
        pass

    @abstractmethod
    async def update_collection_point(self, point_id: uuid.UUID, data: dict) -> Optional[CollectionPoint]:
        pass

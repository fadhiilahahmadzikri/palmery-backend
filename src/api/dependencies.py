import os
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.session import get_db

from src.domain.repositories.config_repo_interface import IConfigRepository
from src.domain.repositories.harvest_repo_interface import IHarvestRepository

from src.infrastructure.repositories.config_repo import ConfigRepository as DatabaseConfigRepository
from src.infrastructure.repositories.harvest_repo import HarvestRepository as DatabaseHarvestRepository

from src.infrastructure.providers.demo.demo_provider import DemoConfigRepository, DemoHarvestRepository

# Initialize demo repositories as singletons
_demo_config_repo = DemoConfigRepository()
_demo_harvest_repo = DemoHarvestRepository()

def get_config_repo(db: AsyncSession = Depends(get_db)) -> IConfigRepository:
    provider = os.getenv("DATA_PROVIDER", "database").lower()
    if provider == "demo":
        return _demo_config_repo
    return DatabaseConfigRepository(db)

def get_harvest_repo(db: AsyncSession = Depends(get_db)) -> IHarvestRepository:
    provider = os.getenv("DATA_PROVIDER", "database").lower()
    if provider == "demo":
        return _demo_harvest_repo
    return DatabaseHarvestRepository(db)

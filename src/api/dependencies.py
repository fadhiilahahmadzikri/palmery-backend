import os
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.session import get_db

from src.domain.repositories.config_repo_interface import IConfigRepository
from src.domain.repositories.harvest_repo_interface import IHarvestRepository
from src.domain.repositories.location_repo_interface import ILocationRepository
from src.domain.repositories.harvester_repo_interface import IHarvesterRepository
from src.domain.repositories.payroll_repo_interface import IPayrollRepository

from src.infrastructure.repositories.config_repo import ConfigRepository as DatabaseConfigRepository
from src.infrastructure.repositories.harvest_repo import HarvestRepository as DatabaseHarvestRepository
from src.infrastructure.repositories.location_repo import LocationRepository as DatabaseLocationRepository
from src.infrastructure.repositories.harvester_repo import HarvesterRepository as DatabaseHarvesterRepository
from src.infrastructure.repositories.payroll_repo import PayrollRepository as DatabasePayrollRepository

def get_config_repo(db: AsyncSession = Depends(get_db)) -> IConfigRepository:
    return DatabaseConfigRepository(db)

def get_harvest_repo(db: AsyncSession = Depends(get_db)) -> IHarvestRepository:
    return DatabaseHarvestRepository(db)

def get_location_repo(db: AsyncSession = Depends(get_db)) -> ILocationRepository:
    return DatabaseLocationRepository(db)

def get_harvester_repo(db: AsyncSession = Depends(get_db)) -> IHarvesterRepository:
    return DatabaseHarvesterRepository(db)

def get_payroll_repo(db: AsyncSession = Depends(get_db)) -> IPayrollRepository:
    return DatabasePayrollRepository(db)

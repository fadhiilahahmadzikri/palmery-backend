import asyncio
import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.database.models import (
    AppConfig, ProgressiveTier, Division, Block, CollectionPoint, Harvester
)
from sqlalchemy.future import select

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(AppConfig).where(AppConfig.config_key == 'FLAT_RATE_PERCENTAGE'))
        if result.scalar_one_or_none():
            print("Database already seeded.")
            return

        # Insert AppConfig
        configs = [
            AppConfig(config_key='FLAT_RATE_PERCENTAGE', config_value=0.10, description='10% of total tonnage is brondolan'),
            AppConfig(config_key='LOOSE_FRUIT_RATE', config_value=75, description='Rp 75 per kg of brondolan'),
            AppConfig(config_key='BASE_TARGET_KG', config_value=1000, description='Base target before progressive premium applies'),
            AppConfig(config_key='MIN_BUNCHES_REQUIRED', config_value=100, description='Minimum bunches to qualify for FFB premium')
        ]
        session.add_all(configs)

        # Insert Progressive Tiers
        tiers = [
            ProgressiveTier(tier_level=1, min_kg=0, max_kg=500, rate_per_kg=250),
            ProgressiveTier(tier_level=2, min_kg=501, max_kg=1000, rate_per_kg=300),
            ProgressiveTier(tier_level=3, min_kg=1001, max_kg=None, rate_per_kg=350)
        ]
        session.add_all(tiers)

        # Insert Locations
        div1 = Division(code="DIV-01", name="Division 1 North")
        div2 = Division(code="DIV-02", name="Division 2 South")
        session.add_all([div1, div2])
        await session.flush()

        blk1 = Block(division_id=div1.id, code="B-101", planting_year=2015, area_ha=30.5)
        blk2 = Block(division_id=div1.id, code="B-102", planting_year=2016, area_ha=28.0)
        blk3 = Block(division_id=div2.id, code="B-201", planting_year=2018, area_ha=35.2)
        session.add_all([blk1, blk2, blk3])
        await session.flush()

        # Insert Collection Points
        cp1 = CollectionPoint(block_id=blk1.id, point_number=1)
        cp2 = CollectionPoint(block_id=blk1.id, point_number=2)
        cp3 = CollectionPoint(block_id=blk2.id, point_number=1)
        cp4 = CollectionPoint(block_id=blk3.id, point_number=1)
        session.add_all([cp1, cp2, cp3, cp4])

        # Insert Harvesters
        h1 = Harvester(
            employee_number="EMP-001", full_name="Budi Santoso", 
            division_id=div1.id, block_id=blk1.id, 
            hire_date=date(2020, 1, 15), is_active=True
        )
        h2 = Harvester(
            employee_number="EMP-002", full_name="Agus Pratama", 
            division_id=div1.id, block_id=blk2.id, 
            hire_date=date(2021, 3, 10), is_active=True
        )
        h3 = Harvester(
            employee_number="EMP-003", full_name="Siti Aminah", 
            division_id=div2.id, block_id=blk3.id, 
            hire_date=date(2022, 6, 22), is_active=True
        )
        session.add_all([h1, h2, h3])

        await session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())

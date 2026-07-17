import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.database.models import AppConfig, ProgressiveTier
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

        await session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())

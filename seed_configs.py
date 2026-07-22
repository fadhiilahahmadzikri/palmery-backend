import asyncio
from datetime import date
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.database.models import (
    FineConfiguration,
    LooseFruitConfiguration,
    PremiumEligibilityConfiguration
)
from sqlalchemy.future import select

async def seed_configs():
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(FineConfiguration).limit(1))
        if result.scalar_one_or_none():
            print("Configs already seeded.")
            return

        # 1. Fine Configuration
        fine = FineConfiguration(
            mode="per_bunch",
            rate_per_bunch_rupiah=5000,
            effective_from=date(2026, 1, 1),
            effective_until=None
        )

        # 2. Loose Fruit Configuration
        loose = LooseFruitConfiguration(
            flat_percentage=0.10,
            rate_per_kg_rupiah=75.0,
            effective_from=date(2026, 1, 1),
            effective_until=None
        )

        # 3. Premium Eligibility Configuration
        eligibility = PremiumEligibilityConfiguration(
            basis_kg=1000,
            min_bunch_count=100,
            effective_from=date(2026, 1, 1),
            effective_until=None
        )

        session.add_all([fine, loose, eligibility])
        await session.commit()
        print("Configuration tables seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_configs())

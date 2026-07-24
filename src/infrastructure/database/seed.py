import asyncio
from seed.seed_database import seed_data as run_seed_data

async def seed_data(force_reseed: bool = False):
    await run_seed_data()

if __name__ == "__main__":
    asyncio.run(seed_data(force_reseed=True))

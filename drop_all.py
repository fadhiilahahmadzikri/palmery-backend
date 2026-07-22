import asyncio
from src.infrastructure.database.session import engine, Base
# Import all models so they are registered with Base
import src.infrastructure.database.models

async def force_reset():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("Dropped all tables successfully.")

if __name__ == "__main__":
    asyncio.run(force_reset())

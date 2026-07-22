import asyncio
from sqlalchemy.future import select
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.database.models import FineConfiguration

async def fix():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(FineConfiguration))
        for fine in result.scalars():
            fine.mode = 'rupiah'
        await session.commit()
        print('Fixed fine configuration modes')

if __name__ == "__main__":
    asyncio.run(fix())

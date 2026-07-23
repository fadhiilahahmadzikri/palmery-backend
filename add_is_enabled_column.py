import asyncio
from sqlalchemy import text
from src.infrastructure.database.session import engine

async def migrate():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE progressive_tiers ADD COLUMN IF NOT EXISTS is_enabled BOOLEAN NOT NULL DEFAULT TRUE;"))
    print("Migration successful: Added is_enabled column to progressive_tiers.")

if __name__ == "__main__":
    asyncio.run(migrate())

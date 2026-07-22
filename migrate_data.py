import asyncio
from sqlalchemy import text
from src.infrastructure.database.session import AsyncSessionLocal

async def migrate_data():
    async with AsyncSessionLocal() as db:
        # Migrate PayrollBatches
        # draft, generated -> ongoing
        await db.execute(text("UPDATE payroll_batches SET status = 'ongoing' WHERE status IN ('draft', 'generated');"))
        # approved, paid, final -> final
        await db.execute(text("UPDATE payroll_batches SET status = 'final' WHERE status IN ('approved', 'paid', 'final');"))
        
        await db.commit()
        print("Migrasi data PayrollBatches selesai.")

if __name__ == "__main__":
    asyncio.run(migrate_data())

import asyncio
from sqlalchemy import select
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.database.models import PayrollBatch, PayrollPeriod

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(PayrollBatch.id, PayrollBatch.status))
        batches = res.all()
        print('--- Payroll Batches ---')
        if not batches:
            print("Tidak ada data batch.")
        for b in batches:
            print(f'Batch ID: {b.id}, Status: {b.status}')
        
        res = await db.execute(select(PayrollPeriod.id, PayrollPeriod.month, PayrollPeriod.year, PayrollPeriod.status))
        periods = res.all()
        print('\n--- Payroll Periods ---')
        if not periods:
            print("Tidak ada data period.")
        for p in periods:
            print(f'Period {p.month}/{p.year}, Status: {p.status}')

if __name__ == "__main__":
    asyncio.run(check())

import sys
import os
import asyncio
from datetime import date, timedelta
import random
from sqlalchemy import text
from faker import Faker
import uuid

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.database.models import (
    Division, Block, CollectionPoint, Harvester,
    FineConfiguration, LooseFruitConfiguration,
    PremiumEligibilityConfiguration, ProgressiveTier,
    DailyHarvestRecord, PayrollPeriod
)
from src.domain.engine.ledger_calculator import calculate_daily_ledger
from src.domain.engine.payroll_calculator import calculate_monthly_payroll, EligibilityConfigModel, TierModel
from src.infrastructure.database.models import PayrollBatch, PayrollSummary, PayrollTierDetail

fake = Faker('id_ID')

async def seed_data():
    async with AsyncSessionLocal() as db:
        print("Truncating tables...")
        tables = [
            "payroll_tier_details", "payroll_summaries", "payroll_batches",
            "daily_harvest_records", "progressive_tiers", "premium_eligibility_configurations", 
            "loose_fruit_configurations", "fine_configurations",
            "collection_points", "blocks", "harvesters", "divisions", "payroll_periods"
        ]
        for table in tables:
            await db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        await db.commit()

        print("Seeding Configurations...")
        fine_config = FineConfiguration(
            id=uuid.uuid4(), mode="rupiah", rate_per_bunch_rupiah=10000,
            effective_from=date(2026, 1, 1)
        )
        loose_config = LooseFruitConfiguration(
            id=uuid.uuid4(), flat_percentage=0.10, rate_per_kg_rupiah=75.0,
            effective_from=date(2026, 1, 1)
        )
        elig_config = PremiumEligibilityConfiguration(
            id=uuid.uuid4(), basis_kg=1000.0, min_bunch_count=100,
            effective_from=date(2026, 1, 1)
        )
        tiers = [
            ProgressiveTier(id=1, tier_level=1, min_kg=0, max_kg=500.0, rate_per_kg=100.0, effective_from=date(2026, 1, 1)),
            ProgressiveTier(id=2, tier_level=2, min_kg=500.0, max_kg=1500.0, rate_per_kg=150.0, effective_from=date(2026, 1, 1)),
            ProgressiveTier(id=3, tier_level=3, min_kg=1500.0, max_kg=None, rate_per_kg=200.0, effective_from=date(2026, 1, 1))
        ]
        db.add_all([fine_config, loose_config, elig_config] + tiers)
        
        print("Seeding Locations...")
        divisions = []
        for i in range(1, 4):
            div = Division(id=uuid.uuid4(), code=f"DIV-0{i}", name=f"Divisi 0{i}", is_active=True)
            divisions.append(div)
        db.add_all(divisions)
        await db.commit()

        blocks = []
        points = []
        
        # Variasikan jumlah blok per divisi (2 sampai 4 blok)
        for div in divisions:
            num_blocks = random.randint(2, 4)
            for j in range(1, num_blocks + 1):
                blk = Block(
                    id=uuid.uuid4(), division_id=div.id,
                    code=f"{div.code}-B{j}", planting_year=random.randint(2010, 2020),
                    area_ha=round(random.uniform(20.0, 50.0), 2), is_active=True
                )
                blocks.append(blk)
                
                # Variasikan jumlah TPH per blok (3 sampai 5 TPH)
                num_points = random.randint(3, 5)
                for k in range(1, num_points + 1):
                    pt = CollectionPoint(id=uuid.uuid4(), block_id=blk.id, point_number=k, is_active=True)
                    points.append(pt)
                    
        db.add_all(blocks)
        db.add_all(points)
        await db.commit()

        print("Seeding Harvesters...")
        harvesters = []
        for i in range(1, 31):
            random_block = random.choice(blocks)
            harv = Harvester(
                id=uuid.uuid4(),
                employee_number=f"EMP{str(i).zfill(4)}",
                full_name=fake.name(),
                phone_number=fake.phone_number()[:20],
                address=fake.address(),
                date_of_birth=fake.date_of_birth(minimum_age=20, maximum_age=55),
                gender=random.choice(['M', 'F']),
                division_id=random_block.division_id,
                block_id=random_block.id,
                hire_date=fake.date_between(start_date="-5y", end_date="today"),
                is_active=True
            )
            harvesters.append(harv)
        db.add_all(harvesters)
        await db.commit()

        print("Seeding Payroll Periods...")
        p_may = PayrollPeriod(id=uuid.uuid4(), year=2026, month=5, status="closed", closed_at=fake.date_time_this_month())
        p_june = PayrollPeriod(id=uuid.uuid4(), year=2026, month=6, status="closed", closed_at=fake.date_time_this_month())
        p_july = PayrollPeriod(id=uuid.uuid4(), year=2026, month=7, status="open")
        p_august = PayrollPeriod(id=uuid.uuid4(), year=2026, month=8, status="open")
        periods_dict = {5: p_may, 6: p_june, 7: p_july, 8: p_august}
        db.add_all([p_may, p_june, p_july, p_august])
        await db.commit()

        print("Seeding Daily Harvest Records (~500 records)...")
        records = []
        start_date = date(2026, 6, 1)
        
        # Helper: group points by block_id
        points_by_block = {}
        for pt in points:
            points_by_block.setdefault(pt.block_id, []).append(pt)
            
        for i in range(500):
            h = random.choice(harvesters)
            
            # Pemanen HANYA memanen di bloknya sendiri (Sesuai business logic baru)
            available_points = points_by_block.get(h.block_id, [])
            pt = random.choice(available_points) if available_points else None
            
            if not pt:
                continue

            d = start_date + timedelta(days=random.randint(0, 45))
            
            valid_bunch = random.randint(50, 250)
            unripe_bunch = random.randint(0, 5)
            avg_weight = round(random.uniform(15.0, 25.0), 2)
            
            ledger = calculate_daily_ledger(
                valid_bunch_count=valid_bunch,
                unripe_bunch_count=unripe_bunch,
                avg_bunch_weight_kg=avg_weight,
                loose_fruit_percentage=float(loose_config.flat_percentage),
                loose_fruit_rate_rupiah=float(loose_config.rate_per_kg_rupiah),
                fine_mode=fine_config.mode,
                fine_rate_rupiah=float(fine_config.rate_per_bunch_rupiah) if fine_config.rate_per_bunch_rupiah else 0.0
            )

            rec = DailyHarvestRecord(
                id=uuid.uuid4(),
                harvester_id=h.id,
                block_id=h.block_id,
                collection_point_id=pt.id,
                harvest_date=d,
                valid_bunch_count=valid_bunch,
                unripe_bunch_count=unripe_bunch,
                avg_bunch_weight_kg=avg_weight,
                loose_fruit_percentage_snapshot=ledger.loose_fruit_percentage_snapshot,
                loose_fruit_rate_snapshot_rupiah=ledger.loose_fruit_rate_snapshot_rupiah,
                fine_mode_snapshot=ledger.fine_mode_snapshot,
                fine_amount_rupiah=ledger.fine_amount_rupiah,
                notes=None,
                recorded_by="Seeder",
                payroll_period_id=periods_dict.get(d.month, p_may).id
            )
            records.append(rec)
        
        db.add_all(records)
        await db.commit()
        
        print("Seeding Payroll Batches and Summaries...")
        for month_num, status in [(5, 'final'), (6, 'final'), (7, 'draft')]:
            period = periods_dict[month_num]
            month_records = [r for r in records if r.payroll_period_id == period.id]
            if not month_records: continue
            
            # Group records by harvester
            records_by_harvester = {}
            for r in month_records:
                records_by_harvester.setdefault(r.harvester_id, []).append(r)
                
            batch = PayrollBatch(
                id=uuid.uuid4(),
                payroll_period_id=period.id,
                status=status,
                generated_by='system_seeder',
                generated_at=period.closed_at or fake.date_time_this_month()
            )
            db.add(batch)
            await db.flush()
            
            elig_model = EligibilityConfigModel(basis_kg=float(elig_config.basis_kg), min_bunch_count=elig_config.min_bunch_count)
            tier_models = [TierModel(tier_level=t.tier_level, min_kg=float(t.min_kg), max_kg=float(t.max_kg) if t.max_kg else None, rate_per_kg=float(t.rate_per_kg)) for t in tiers]
            
            summaries_to_add = []
            tiers_to_add = []
            
            for h_id, h_records in records_by_harvester.items():
                total_valid = sum(r.valid_bunch_count for r in h_records)
                total_unripe = sum(r.unripe_bunch_count for r in h_records)
                total_net = sum(float(r.net_tonnage_kg) for r in h_records)
                total_loose = sum(float(r.loose_fruit_premium_rupiah) for r in h_records)
                total_fine = sum(float(r.fine_amount_rupiah) for r in h_records)
                fine_mode = h_records[0].fine_mode_snapshot
                
                result = calculate_monthly_payroll(
                    total_valid, total_unripe, total_net, total_loose, total_fine, fine_mode, elig_model, tier_models
                )
                
                summary = PayrollSummary(
                    id=uuid.uuid4(),
                    payroll_batch_id=batch.id,
                    harvester_id=h_id,
                    total_valid_bunch_count=result.total_valid_bunch_count,
                    total_unripe_bunch_count=result.total_unripe_bunch_count,
                    total_net_tonnage_kg=result.total_net_tonnage_kg,
                    total_loose_fruit_premium_rupiah=result.total_loose_fruit_premium_rupiah,
                    fine_mode_used=result.fine_mode_used,
                    total_fine_rupiah=result.total_fine_rupiah,
                    total_tier_premium_rupiah=result.total_tier_premium_rupiah,
                    total_net_pay_rupiah=result.total_net_pay_rupiah,
                    generated_at=batch.generated_at
                )
                summaries_to_add.append(summary)
                
                for td in result.tier_details:
                    tiers_to_add.append(PayrollTierDetail(
                        payroll_summary_id=summary.id,
                        tier_level=td.tier_level,
                        kg_in_tier=td.kg_in_tier,
                        rate_per_kg=td.rate_per_kg,
                        subtotal_rupiah=td.subtotal_rupiah
                    ))
            
            db.add_all(summaries_to_add)
            await db.flush()
            db.add_all(tiers_to_add)
            
        await db.commit()

        print(f"Database seeding completed successfully. Generated {len(records)} daily records, {len(harvesters)} harvesters, {len(divisions)} divisions, {len(blocks)} blocks, {len(points)} points.")

if __name__ == "__main__":
    asyncio.run(seed_data())

import sys
import os
import asyncio
from datetime import date, datetime, timezone, timedelta
import random
import math
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

# Names of 20 authentic Indonesian harvesters
INDONESIAN_HARVESTER_NAMES = [
    "Budi Santoso", "Agus Setiawan", "Herman Wijaya", "Suprianto",
    "Bambang Prasetyo", "Eko Prasetyo", "Joko Widodo", "Hendra Saputra",
    "Rizky Ramadhan", "Dedi Kurniawan", "Slamet Riyadi", "Rudi Hermawan",
    "Yudi Pratama", "Ahmad Hidayat", "Wahyu Nugroho", "Arif Rahman",
    "Tri Mulyono", "Doni Kusuma", "Bayu Perkasa", "Fajar Utama"
]

MANDOR_NAMES = ["Mandor Amir", "Mandor Susilo", "Mandor Tarigan", "Mandor Hasibuan"]

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
            effective_from=date(2025, 8, 1)
        )
        loose_config = LooseFruitConfiguration(
            id=uuid.uuid4(), flat_percentage=0.10, rate_per_kg_rupiah=75.0,
            effective_from=date(2025, 8, 1)
        )
        elig_config = PremiumEligibilityConfiguration(
            id=uuid.uuid4(), basis_kg=1000.0, min_bunch_count=100,
            effective_from=date(2025, 8, 1)
        )
        tiers = [
            ProgressiveTier(id=1, tier_level=1, min_kg=0, max_kg=500.0, rate_per_kg=250.0, effective_from=date(2025, 8, 1)),
            ProgressiveTier(id=2, tier_level=2, min_kg=501.0, max_kg=1000.0, rate_per_kg=300.0, effective_from=date(2025, 8, 1)),
            ProgressiveTier(id=3, tier_level=3, min_kg=1001.0, max_kg=None, rate_per_kg=350.0, effective_from=date(2025, 8, 1))
        ]
        db.add_all([fine_config, loose_config, elig_config] + tiers)
        
        print("Seeding 3 Divisions...")
        divisions = []
        div_names = ["Divisi 01 (Estate Alfa)", "Divisi 02 (Estate Beta)", "Divisi 03 (Estate Gamma)"]
        for i in range(1, 4):
            div = Division(id=uuid.uuid4(), code=f"DIV-0{i}", name=div_names[i-1], is_active=True)
            divisions.append(div)
        db.add_all(divisions)
        await db.commit()

        print("Seeding 5 Blocks per Division (15 Blocks total) & 10 TPH per Block (150 TPH total)...")
        blocks = []
        points = []
        
        for div_idx, div in enumerate(divisions, start=1):
            for b_idx in range(1, 6):  # Exactly 5 blocks per division
                blk = Block(
                    id=uuid.uuid4(), 
                    division_id=div.id,
                    code=f"DIV-0{div_idx}-B{b_idx}", 
                    planting_year=2012 + (b_idx % 8),
                    area_ha=30.0 + (b_idx * 2.5), 
                    is_active=True
                )
                blocks.append(blk)
                
                for tph_idx in range(1, 11):  # Exactly 10 TPH per block
                    pt = CollectionPoint(
                        id=uuid.uuid4(), 
                        block_id=blk.id, 
                        point_number=tph_idx, 
                        is_active=True
                    )
                    points.append(pt)
                    
        db.add_all(blocks)
        db.add_all(points)
        await db.commit()

        print("Seeding Exactly 20 Indonesian Harvesters...")
        harvesters = []
        for i, name in enumerate(INDONESIAN_HARVESTER_NAMES, start=1):
            assigned_block = blocks[(i - 1) % len(blocks)]
            harv = Harvester(
                id=uuid.uuid4(),
                employee_number=f"EMP{str(i).zfill(4)}",
                full_name=name,
                phone_number=f"081234567{str(i).zfill(3)}",
                address=f"Perumahan Afdeling {assigned_block.code}, Kebun Sawit",
                date_of_birth=date(1985 + (i % 15), (i % 12) + 1, (i % 28) + 1),
                gender="M",
                division_id=assigned_block.division_id,
                block_id=assigned_block.id,
                hire_date=date(2020 + (i % 5), (i % 12) + 1, 1),
                is_active=True
            )
            harvesters.append(harv)
        db.add_all(harvesters)
        await db.commit()

        print("Seeding 12 Payroll Periods (Aug 2025 - Jul 2026)...")
        months_list = [
            (2025, 8), (2025, 9), (2025, 10), (2025, 11), (2025, 12),
            (2026, 1), (2026, 2), (2026, 3), (2026, 4), (2026, 5), (2026, 6), (2026, 7)
        ]
        
        periods_dict = {}
        periods_list = []
        for yr, m in months_list:
            is_july = (yr == 2026 and m == 7)
            status = "open" if is_july else "closed"
            closed_at = None if is_july else datetime(yr, m, 28, 17, 0, tzinfo=timezone.utc)
            period = PayrollPeriod(
                id=uuid.uuid4(),
                year=yr,
                month=m,
                status=status,
                closed_at=closed_at
            )
            periods_dict[(yr, m)] = period
            periods_list.append(period)

        db.add_all(periods_list)
        await db.commit()

        print("Seeding Daily Harvest Records across 1 Full Year (365 Days: Aug 2025 - Jul 2026)...")
        records = []
        points_by_block = {}
        for pt in points:
            points_by_block.setdefault(pt.block_id, []).append(pt)

        # Generate realistic daily harvest records for 1 full year
        # Start date: Aug 1, 2025 to Jul 25, 2026
        start_date = date(2025, 8, 1)
        end_date = date(2026, 7, 25)
        curr_date = start_date
        
        rec_counter = 0

        # Deterministic random generator for reproducible real data
        rng = random.Random(42)

        while curr_date <= end_date:
            yr, m = curr_date.year, curr_date.month
            period = periods_dict.get((yr, m))
            if not period:
                curr_date += timedelta(days=1)
                continue

            is_sunday = (curr_date.weekday() == 6)
            
            # Seasonal factor for palm oil (Peak season Oct-Dec, Trek season Mar-May)
            month_angle = ((m - 1) / 12.0) * 2 * math.pi
            seasonal_factor = 1.0 + 0.15 * math.sin(month_angle - 1.5)

            if not is_sunday:
                # Working day: 12-16 harvesters active each day out of 20
                active_count = rng.randint(12, 16)
                todays_harvesters = rng.sample(harvesters, active_count)

                for h_idx, h in enumerate(todays_harvesters):
                    available_points = points_by_block.get(h.block_id, [])
                    if not available_points:
                        continue

                    rec_counter += 1
                    pt = available_points[rec_counter % len(available_points)]

                    # Base yield per harvester: 80 - 150 bunches
                    base_bunches = rng.randint(85, 145)
                    valid_bunch = int(base_bunches * seasonal_factor)
                    unripe_bunch = rng.choice([0, 0, 0, 1, 2]) if valid_bunch > 90 else 0
                    
                    # BJR (Berat Janjang Rata-rata) 16.0 - 22.0 kg
                    avg_weight = round(rng.uniform(16.5, 22.5), 2)

                    ledger = calculate_daily_ledger(
                        valid_bunch_count=valid_bunch,
                        unripe_bunch_count=unripe_bunch,
                        avg_bunch_weight_kg=avg_weight,
                        loose_fruit_percentage=float(loose_config.flat_percentage),
                        loose_fruit_rate_rupiah=float(loose_config.rate_per_kg_rupiah),
                        fine_mode=fine_config.mode,
                        fine_rate_rupiah=float(fine_config.rate_per_bunch_rupiah)
                    )

                    rec = DailyHarvestRecord(
                        id=uuid.uuid4(),
                        harvester_id=h.id,
                        block_id=h.block_id,
                        collection_point_id=pt.id,
                        harvest_date=curr_date,
                        valid_bunch_count=valid_bunch,
                        unripe_bunch_count=unripe_bunch,
                        avg_bunch_weight_kg=avg_weight,
                        loose_fruit_percentage_snapshot=ledger.loose_fruit_percentage_snapshot,
                        loose_fruit_rate_snapshot_rupiah=ledger.loose_fruit_rate_snapshot_rupiah,
                        fine_mode_snapshot=ledger.fine_mode_snapshot,
                        fine_amount_rupiah=ledger.fine_amount_rupiah,
                        notes=f"Panen Harian Kerani TPH {pt.point_number}" if unripe_bunch > 0 else None,
                        recorded_by=MANDOR_NAMES[rec_counter % len(MANDOR_NAMES)],
                        payroll_period_id=period.id
                    )
                    records.append(rec)

            curr_date += timedelta(days=1)

        db.add_all(records)
        await db.commit()

        print(f"Seeding Payroll Batches & Calculating Real Monthly Payroll Summaries for {len(months_list)} Months...")
        for yr, month_num in months_list:
            status = 'ongoing' if (yr == 2026 and month_num == 7) else 'final'
            period = periods_dict[(yr, month_num)]
            month_records = [r for r in records if r.payroll_period_id == period.id]
            if not month_records:
                continue

            records_by_harvester = {}
            for r in month_records:
                records_by_harvester.setdefault(r.harvester_id, []).append(r)

            batch = PayrollBatch(
                id=uuid.uuid4(),
                payroll_period_id=period.id,
                status=status,
                generated_by='system_seeder',
                generated_at=period.closed_at or datetime.now(timezone.utc)
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
        print(f"Database re-seeding completed successfully! Created {len(harvesters)} Harvesters, {len(divisions)} Divisions, {len(blocks)} Blocks, {len(points)} TPHs, {len(records)} Daily Harvest Records across 1 Full Year (Aug 2025 - Jul 2026) with 11 Finalized & 1 Ongoing Monthly Payroll Batches.")

if __name__ == "__main__":
    asyncio.run(seed_data())

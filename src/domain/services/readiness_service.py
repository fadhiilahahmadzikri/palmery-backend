from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.infrastructure.database.models import (
    Division, Block, CollectionPoint, Harvester,
    PremiumEligibilityConfiguration, ProgressiveTier,
    DailyHarvestRecord, PayrollPeriod
)

class ReadinessCheckItem(BaseModel):
    key: str
    label: str
    count: int
    is_ready: bool
    target_url: str
    missing_message: str
    action_label: str

class SystemReadinessResponse(BaseModel):
    is_system_ready: bool
    can_input_harvest: bool
    can_process_payroll: bool
    items: List[ReadinessCheckItem]
    blocking_prerequisite_for_harvest: Optional[ReadinessCheckItem] = None
    blocking_prerequisite_for_payroll: Optional[ReadinessCheckItem] = None

class ReadinessService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_system_readiness(self) -> SystemReadinessResponse:
        # Count Division
        div_res = await self.db.execute(select(func.count(Division.id)))
        division_count = div_res.scalar() or 0

        # Count Block
        block_res = await self.db.execute(select(func.count(Block.id)))
        block_count = block_res.scalar() or 0

        # Count Collection Point (TPH)
        tph_res = await self.db.execute(select(func.count(CollectionPoint.id)))
        tph_count = tph_res.scalar() or 0

        # Count Harvester
        harv_res = await self.db.execute(select(func.count(Harvester.id)))
        harvester_count = harv_res.scalar() or 0

        # Check Eligibility Config
        elig_res = await self.db.execute(
            select(func.count(PremiumEligibilityConfiguration.id)).where(PremiumEligibilityConfiguration.effective_until.is_(None))
        )
        eligibility_configured = (elig_res.scalar() or 0) > 0

        # Count Active Tiers
        tier_res = await self.db.execute(
            select(func.count(ProgressiveTier.id)).where(ProgressiveTier.effective_until.is_(None), ProgressiveTier.is_enabled == True)
        )
        enabled_tier_count = tier_res.scalar() or 0

        # Count Harvest Records
        record_res = await self.db.execute(select(func.count(DailyHarvestRecord.id)))
        record_count = record_res.scalar() or 0

        # Build Check Items
        items = [
            ReadinessCheckItem(
                key="divisions",
                label="Divisi Perkebunan",
                count=division_count,
                is_ready=division_count > 0,
                target_url="/locations?tab=divisions",
                missing_message="Belum ada Divisi terdaftar. Divisi diperlukan sebagai wadah Blok dan Pemanen.",
                action_label="Kelola Divisi"
            ),
            ReadinessCheckItem(
                key="blocks",
                label="Blok Panen",
                count=block_count,
                is_ready=block_count > 0,
                target_url="/locations?tab=blocks",
                missing_message="Belum ada Blok Panen terdaftar. Laporan panen wajib merekam Lokasi Blok.",
                action_label="Kelola Blok Panen"
            ),
            ReadinessCheckItem(
                key="tph",
                label="TPH (Tempat Pengumpulan Hasil)",
                count=tph_count,
                is_ready=tph_count > 0,
                target_url="/locations?tab=tph",
                missing_message="Belum ada TPH terdaftar. Laporan panen memerlukan penentuan TPH.",
                action_label="Kelola TPH"
            ),
            ReadinessCheckItem(
                key="harvesters",
                label="Pemanen",
                count=harvester_count,
                is_ready=harvester_count > 0,
                target_url="/harvesters",
                missing_message="Belum ada Pemanen terdaftar. Laporan panen memerlukan profil Pemanen.",
                action_label="Tambah Pemanen"
            ),
            ReadinessCheckItem(
                key="eligibility",
                label="Syarat Premi (Eligibility)",
                count=1 if eligibility_configured else 0,
                is_ready=eligibility_configured,
                target_url="/settings?tab=eligibility",
                missing_message="Konfigurasi Syarat Premi belum diatur. Diperlukan untuk validasi ambang batas panen.",
                action_label="Konfigurasi Syarat Premi"
            ),
            ReadinessCheckItem(
                key="tiers",
                label="Tier Progresif Aktif",
                count=enabled_tier_count,
                is_ready=enabled_tier_count > 0,
                target_url="/settings?tab=tiers",
                missing_message="Belum ada Tier Progresif aktif yang dikonfigurasi.",
                action_label="Konfigurasi Tier"
            ),
            ReadinessCheckItem(
                key="harvest_records",
                label="Laporan Rekap Panen",
                count=record_count,
                is_ready=record_count > 0,
                target_url="/report",
                missing_message="Belum ada Laporan Rekap Panen Harian untuk kalkulasi payroll.",
                action_label="Input Laporan Panen"
            ),
        ]

        # Determine Prerequisite Gate for Harvest Input
        harvest_prereqs = ["divisions", "blocks", "tph", "harvesters", "eligibility"]
        blocking_for_harvest = next((item for item in items if item.key in harvest_prereqs and not item.is_ready), None)

        can_input_harvest = blocking_for_harvest is None

        # Determine Prerequisite Gate for Payroll
        payroll_prereqs = ["harvest_records"]
        blocking_for_payroll = next((item for item in items if item.key in payroll_prereqs and not item.is_ready), None)

        can_process_payroll = can_input_harvest and blocking_for_payroll is None

        is_system_ready = all(item.is_ready for item in items if item.key != "harvest_records")

        return SystemReadinessResponse(
            is_system_ready=is_system_ready,
            can_input_harvest=can_input_harvest,
            can_process_payroll=can_process_payroll,
            items=items,
            blocking_prerequisite_for_harvest=blocking_for_harvest,
            blocking_prerequisite_for_payroll=blocking_for_payroll,
        )

    async def purge_system_data(self) -> bool:
        from sqlalchemy import delete
        from src.infrastructure.database.models import (
            DailyHarvestRecord, PayrollTierDetail, PayrollSummary, PayrollBatch, PayrollPeriod,
            Harvester, CollectionPoint, Block, Division, ProgressiveTier,
            PremiumEligibilityConfiguration, LooseFruitConfiguration, FineConfiguration
        )

        await self.db.execute(delete(PayrollTierDetail))
        await self.db.execute(delete(PayrollSummary))
        await self.db.execute(delete(PayrollBatch))
        await self.db.execute(delete(DailyHarvestRecord))
        await self.db.execute(delete(PayrollPeriod))
        await self.db.execute(delete(Harvester))
        await self.db.execute(delete(CollectionPoint))
        await self.db.execute(delete(Block))
        await self.db.execute(delete(Division))
        await self.db.execute(delete(ProgressiveTier))
        await self.db.execute(delete(PremiumEligibilityConfiguration))
        await self.db.execute(delete(LooseFruitConfiguration))
        await self.db.execute(delete(FineConfiguration))

        await self.db.commit()
        return True

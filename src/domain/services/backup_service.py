import json
from datetime import datetime, date, timezone
from decimal import Decimal
import uuid
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.infrastructure.database.models import (
    AppConfig, Division, Block, CollectionPoint, Harvester,
    FineConfiguration, LooseFruitConfiguration, PremiumEligibilityConfiguration, ProgressiveTier,
    PayrollPeriod, DailyHarvestRecord, PayrollBatch, PayrollSummary, PayrollTierDetail
)

def default_json_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

class BackupService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_backup(self) -> Dict[str, Any]:
        tables_data = {}

        # List of models to backup in safe restore order
        models_to_backup = [
            ("app_config", AppConfig),
            ("fine_configurations", FineConfiguration),
            ("loose_fruit_configurations", LooseFruitConfiguration),
            ("premium_eligibility_configurations", PremiumEligibilityConfiguration),
            ("progressive_tiers", ProgressiveTier),
            ("divisions", Division),
            ("blocks", Block),
            ("collection_points", CollectionPoint),
            ("harvesters", Harvester),
            ("payroll_periods", PayrollPeriod),
            ("daily_harvest_records", DailyHarvestRecord),
            ("payroll_batches", PayrollBatch),
            ("payroll_summaries", PayrollSummary),
            ("payroll_tier_details", PayrollTierDetail),
        ]

        for table_name, model in models_to_backup:
            result = await self.db.execute(select(model))
            rows = result.scalars().all()
            table_rows = []
            for row in rows:
                row_dict = {}
                for column in row.__table__.columns:
                    val = getattr(row, column.name)
                    if isinstance(val, (datetime, date)):
                        val = val.isoformat()
                    elif isinstance(val, Decimal):
                        val = float(val)
                    elif isinstance(val, uuid.UUID):
                        val = str(val)
                    row_dict[column.name] = val
                table_rows.append(row_dict)
            tables_data[table_name] = table_rows

        return {
            "metadata": {
                "backup_version": "1.0",
                "system": "Palm Payroll Ledger",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "total_tables": len(tables_data)
            },
            "tables": tables_data
        }

    async def restore_backup(self, backup_data: Dict[str, Any]) -> bool:
        if "tables" not in backup_data:
            raise ValueError("Payload backup tidak valid: key 'tables' tidak ditemukan.")

        tables = backup_data["tables"]

        # Deletion order (child first)
        delete_order = [
            PayrollTierDetail, PayrollSummary, PayrollBatch, DailyHarvestRecord,
            PayrollPeriod, Harvester, CollectionPoint, Block, Division,
            ProgressiveTier, PremiumEligibilityConfiguration, LooseFruitConfiguration,
            FineConfiguration, AppConfig
        ]

        for model in delete_order:
            await self.db.execute(delete(model))
        await self.db.flush()

        # Insertion order (parent first)
        insert_map = [
            ("app_config", AppConfig),
            ("fine_configurations", FineConfiguration),
            ("loose_fruit_configurations", LooseFruitConfiguration),
            ("premium_eligibility_configurations", PremiumEligibilityConfiguration),
            ("progressive_tiers", ProgressiveTier),
            ("divisions", Division),
            ("blocks", Block),
            ("collection_points", CollectionPoint),
            ("harvesters", Harvester),
            ("payroll_periods", PayrollPeriod),
            ("daily_harvest_records", DailyHarvestRecord),
            ("payroll_batches", PayrollBatch),
            ("payroll_summaries", PayrollSummary),
            ("payroll_tier_details", PayrollTierDetail),
        ]

        for table_name, model in insert_map:
            rows = tables.get(table_name, [])
            for row_dict in rows:
                parsed_dict = {}
                for col in model.__table__.columns:
                    val = row_dict.get(col.name)
                    if val is not None:
                        if str(col.type).startswith("UUID") or "UUID" in str(col.type):
                            val = uuid.UUID(val) if isinstance(val, str) else val
                        elif "DATE" in str(col.type) and not "DATETIME" in str(col.type):
                            val = date.fromisoformat(val) if isinstance(val, str) else val
                        elif "DATETIME" in str(col.type) or "TIMESTAMP" in str(col.type):
                            val = datetime.fromisoformat(val) if isinstance(val, str) else val
                    parsed_dict[col.name] = val
                instance = model(**parsed_dict)
                self.db.add(instance)

        await self.db.commit()
        return True

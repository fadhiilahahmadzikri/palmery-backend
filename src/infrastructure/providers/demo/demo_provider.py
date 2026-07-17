import json
import os
from typing import List, Optional
from src.infrastructure.database.models import AppConfig, ProgressiveTier, DailyHarvestRecord
from src.domain.repositories.config_repo_interface import IConfigRepository
from src.domain.repositories.harvest_repo_interface import IHarvestRepository

def load_json(filename):
    filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), 'demo', filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return []

def save_json(filename, data):
    filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), 'demo', filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

class DemoConfigRepository(IConfigRepository):
    def __init__(self):
        self._configs = load_json('config.json')
        self._tiers = load_json('tiers.json')
        
    async def get_all_configs(self) -> List[AppConfig]:
        return [AppConfig(**c) for c in self._configs]

    async def get_config_by_id(self, config_id: int) -> Optional[AppConfig]:
        for c in self._configs:
            if c["id"] == config_id:
                return AppConfig(**c)
        return None

    async def create_config(self, data: dict) -> AppConfig:
        new_id = max([c.get("id", 0) for c in self._configs], default=0) + 1
        config = {"id": new_id, **data}
        self._configs.append(config)
        save_json('config.json', self._configs)
        return AppConfig(**config)

    async def update_config(self, key: str, value: float) -> Optional[AppConfig]:
        for c in self._configs:
            if c["config_key"] == key:
                c["config_value"] = value
                save_json('config.json', self._configs)
                return AppConfig(**c)
        return None

    async def delete_config(self, config_id: int) -> bool:
        initial_len = len(self._configs)
        self._configs = [c for c in self._configs if c["id"] != config_id]
        if len(self._configs) < initial_len:
            save_json('config.json', self._configs)
            return True
        return False

    async def get_all_tiers(self) -> List[ProgressiveTier]:
        sorted_tiers = sorted(self._tiers, key=lambda x: x["tier_level"])
        return [ProgressiveTier(**t) for t in sorted_tiers]

    async def get_tier_by_id(self, tier_id: int) -> Optional[ProgressiveTier]:
        for t in self._tiers:
            if t["id"] == tier_id:
                return ProgressiveTier(**t)
        return None

    async def create_tier(self, data: dict) -> ProgressiveTier:
        new_id = max([t.get("id", 0) for t in self._tiers], default=0) + 1
        tier = {"id": new_id, **data}
        self._tiers.append(tier)
        save_json('tiers.json', self._tiers)
        return ProgressiveTier(**tier)

    async def update_tier(self, tier_id: int, data: dict) -> Optional[ProgressiveTier]:
        for t in self._tiers:
            if t["id"] == tier_id:
                for k, v in data.items():
                    if v is not None:
                        t[k] = v
                save_json('tiers.json', self._tiers)
                return ProgressiveTier(**t)
        return None

    async def delete_tier(self, tier_id: int) -> bool:
        initial_len = len(self._tiers)
        self._tiers = [t for t in self._tiers if t["id"] != tier_id]
        if len(self._tiers) < initial_len:
            save_json('tiers.json', self._tiers)
            return True
        return False

import uuid

class DemoHarvestRepository(IHarvestRepository):
    def __init__(self):
        self._records = load_json('harvest.json')
        
    async def get_records(self, skip: int = 0, limit: int = 100) -> List[DailyHarvestRecord]:
        return [DailyHarvestRecord(**r) for r in self._records[skip:skip+limit]]

    async def get_record_by_id(self, record_id: uuid.UUID) -> Optional[DailyHarvestRecord]:
        for r in self._records:
            if str(r["id"]) == str(record_id):
                return DailyHarvestRecord(**r)
        return None

    async def create_record(self, data: dict) -> DailyHarvestRecord:
        record = {"id": str(uuid.uuid4()), **data}
        # Insert at the beginning to simulate latest first
        self._records.insert(0, record)
        save_json('harvest.json', self._records)
        return DailyHarvestRecord(**record)

    async def update_record(self, record_id: uuid.UUID, data: dict) -> Optional[DailyHarvestRecord]:
        for r in self._records:
            if str(r["id"]) == str(record_id):
                for k, v in data.items():
                    if v is not None:
                        r[k] = v
                save_json('harvest.json', self._records)
                return DailyHarvestRecord(**r)
        return None

    async def delete_record(self, record_id: uuid.UUID) -> bool:
        initial_len = len(self._records)
        self._records = [r for r in self._records if str(r["id"]) != str(record_id)]
        if len(self._records) < initial_len:
            save_json('harvest.json', self._records)
            return True
        return False

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base

class AppConfig(Base):
    __tablename__ = 'app_config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False)
    config_value = Column(Numeric, nullable=False)
    description = Column(String(255))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ProgressiveTier(Base):
    __tablename__ = 'progressive_tiers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tier_level = Column(Integer, unique=True, nullable=False)
    min_kg = Column(Numeric, nullable=False)
    max_kg = Column(Numeric, nullable=True)
    rate_per_kg = Column(Numeric, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class DailyHarvestRecord(Base):
    __tablename__ = 'daily_harvest_records'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    harvest_date = Column(Date, nullable=False, server_default=func.current_date())
    harvester_name = Column(String(100), nullable=False)
    
    input_total_bunches = Column(Integer, nullable=False)
    input_avg_bunch_weight = Column(Numeric, nullable=False)
    input_unripe_penalty = Column(Numeric, nullable=False, default=0)
    
    calc_total_tonnage = Column(Numeric, nullable=False)
    calc_loose_fruit_kg = Column(Numeric, nullable=False)
    calc_net_ffb = Column(Numeric, nullable=False)
    
    premium_loose_fruit = Column(Numeric, nullable=False)
    premium_ffb = Column(Numeric, nullable=False)
    total_final_premium = Column(Numeric, nullable=False)
    tier_status = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

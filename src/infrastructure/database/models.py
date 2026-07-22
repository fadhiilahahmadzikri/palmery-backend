import uuid
import enum
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date, 
    ForeignKey, Boolean, Text, Computed, UniqueConstraint, Index, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base

class PayrollPeriodStatus(str, enum.Enum):
    open = "open"
    closed = "closed"

class PayrollBatchStatus(str, enum.Enum):
    ongoing = "ongoing"
    final = "final"


class AppConfig(Base):
    __tablename__ = 'app_config'
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False)
    config_value = Column(Numeric, nullable=False)
    description = Column(String(255))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Division(Base):
    __tablename__ = 'divisions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    blocks = relationship("Block", back_populates="division", cascade="all, delete-orphan", passive_deletes=True)
    harvesters = relationship("Harvester", back_populates="division")

class Block(Base):
    __tablename__ = 'blocks'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    division_id = Column(UUID(as_uuid=True), ForeignKey('divisions.id', ondelete='CASCADE'), nullable=False)
    code = Column(String(20), nullable=False)
    planting_year = Column(Integer)
    area_ha = Column(Numeric)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('division_id', 'code', name='uq_division_code'),
        Index('idx_blocks_division', 'division_id')
    )

    division = relationship("Division", back_populates="blocks")
    collection_points = relationship("CollectionPoint", back_populates="block", cascade="all, delete-orphan", passive_deletes=True)
    harvest_records = relationship("DailyHarvestRecord", back_populates="block", cascade="all, delete-orphan", passive_deletes=True)

class CollectionPoint(Base):
    __tablename__ = 'collection_points'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.id', ondelete='CASCADE'), nullable=False)
    point_number = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('block_id', 'point_number', name='uq_block_point'),
        Index('idx_collection_points_block', 'block_id')
    )

    block = relationship("Block", back_populates="collection_points")
    harvest_records = relationship("DailyHarvestRecord", back_populates="collection_point", cascade="all, delete-orphan", passive_deletes=True)

class Harvester(Base):
    __tablename__ = 'harvesters'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_number = Column(String(30), unique=True)
    full_name = Column(String(100), nullable=False)
    phone_number = Column(String(20))
    address = Column(Text)
    date_of_birth = Column(Date)
    gender = Column(String(1))
    division_id = Column(UUID(as_uuid=True), ForeignKey('divisions.id'))
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.id'))
    hire_date = Column(Date)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_harvesters_division', 'division_id'),
        Index('idx_harvesters_block', 'block_id'),
    )

    division = relationship("Division", back_populates="harvesters", lazy="joined")
    block = relationship("Block", lazy="joined")

    @property
    def division_name(self) -> str | None:
        return self.division.name if self.division else None

    @property
    def block_code(self) -> str | None:
        return self.block.code if self.block else None

class FineConfiguration(Base):
    __tablename__ = 'fine_configurations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mode = Column(String(10), nullable=False)
    rate_per_bunch_rupiah = Column(Numeric)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('uq_fine_configurations_one_active', 'id', postgresql_where=(effective_until.is_(None)), unique=True),
    )

class ProgressiveTier(Base):
    __tablename__ = 'progressive_tiers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tier_level = Column(Integer, nullable=False)
    min_kg = Column(Numeric, nullable=False)
    max_kg = Column(Numeric)
    rate_per_kg = Column(Numeric, nullable=False)
    effective_from = Column(Date, nullable=False, server_default=func.current_date())
    effective_until = Column(Date)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('uq_progressive_tiers_active_level', 'tier_level', postgresql_where=(effective_until.is_(None)), unique=True),
    )

class LooseFruitConfiguration(Base):
    __tablename__ = 'loose_fruit_configurations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flat_percentage = Column(Numeric, nullable=False)
    rate_per_kg_rupiah = Column(Numeric, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('uq_loose_fruit_configurations_one_active', 'id', postgresql_where=(effective_until.is_(None)), unique=True),
    )

class PremiumEligibilityConfiguration(Base):
    __tablename__ = 'premium_eligibility_configurations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    basis_kg = Column(Numeric, nullable=False)
    min_bunch_count = Column(Integer, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('uq_premium_eligibility_configurations_one_active', 'id', postgresql_where=(effective_until.is_(None)), unique=True),
    )

class PayrollPeriod(Base):
    __tablename__ = 'payroll_periods'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    status = Column(Enum(PayrollPeriodStatus, name='payroll_period_status', native_enum=False, length=20), nullable=False, default=PayrollPeriodStatus.open)
    closed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('year', 'month', name='uq_payroll_period_year_month'),
    )

class DailyHarvestRecord(Base):
    __tablename__ = 'daily_harvest_records'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    harvester_id = Column(UUID(as_uuid=True), ForeignKey('harvesters.id'), nullable=False)
    block_id = Column(UUID(as_uuid=True), ForeignKey('blocks.id', ondelete='CASCADE'), nullable=False)
    collection_point_id = Column(UUID(as_uuid=True), ForeignKey('collection_points.id', ondelete='CASCADE'), nullable=False)
    harvest_date = Column(Date, nullable=False, server_default=func.current_date())
    
    valid_bunch_count = Column(Integer, nullable=False)
    unripe_bunch_count = Column(Integer, nullable=False, default=0)
    avg_bunch_weight_kg = Column(Numeric, nullable=False)
    
    gross_tonnage_kg = Column(Numeric, Computed("valid_bunch_count * avg_bunch_weight_kg", persisted=True))
    
    loose_fruit_percentage_snapshot = Column(Numeric, nullable=False, default=0)
    loose_fruit_rate_snapshot_rupiah = Column(Numeric, nullable=False, default=0)
    
    loose_fruit_deduction_kg = Column(Numeric, Computed("valid_bunch_count * avg_bunch_weight_kg * loose_fruit_percentage_snapshot", persisted=True))
    loose_fruit_premium_rupiah = Column(Numeric, Computed("valid_bunch_count * avg_bunch_weight_kg * loose_fruit_percentage_snapshot * loose_fruit_rate_snapshot_rupiah", persisted=True))
    
    fine_mode_snapshot = Column(String(10), nullable=False)
    fine_amount_rupiah = Column(Numeric, nullable=False, default=0)
    
    weight_deduction_kg = Column(Numeric, Computed("CASE WHEN fine_mode_snapshot = 'kg' THEN unripe_bunch_count * avg_bunch_weight_kg ELSE 0 END", persisted=True))
    
    net_tonnage_kg = Column(Numeric, Computed("""
        (valid_bunch_count * avg_bunch_weight_kg)
        - (valid_bunch_count * avg_bunch_weight_kg * loose_fruit_percentage_snapshot)
        - (CASE WHEN fine_mode_snapshot = 'kg' THEN unripe_bunch_count * avg_bunch_weight_kg ELSE 0 END)
    """, persisted=True))
    
    notes = Column(Text)
    recorded_by = Column(String(100))
    payroll_period_id = Column(UUID(as_uuid=True), ForeignKey('payroll_periods.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_daily_harvest_harvester_date', 'harvester_id', 'harvest_date'),
        Index('idx_daily_harvest_block', 'block_id'),
        Index('idx_daily_harvest_period', 'payroll_period_id'),
    )

    harvester = relationship("Harvester", lazy="joined")
    block = relationship("Block", back_populates="harvest_records", lazy="joined")
    collection_point = relationship("CollectionPoint", back_populates="harvest_records", lazy="joined")
    payroll_period = relationship("PayrollPeriod")

    @property
    def harvester_name(self) -> str | None:
        return self.harvester.full_name if self.harvester else None

    @property
    def location_name(self) -> str | None:
        if self.collection_point:
            return f"TPH {self.collection_point.point_number}"
        if self.block:
            return f"Blok {self.block.code}"
        return None


class PayrollBatch(Base):
    __tablename__ = 'payroll_batches'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_period_id = Column(UUID(as_uuid=True), ForeignKey('payroll_periods.id'), nullable=False, unique=True)
    status = Column(Enum(PayrollBatchStatus, name='payroll_batch_status', native_enum=False, length=20), nullable=False, default=PayrollBatchStatus.ongoing)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(String(100), default='system')
    
    payroll_period = relationship("PayrollPeriod")
    payroll_summaries = relationship("PayrollSummary", back_populates="batch", cascade="all, delete-orphan")

class PayrollSummary(Base):
    __tablename__ = 'payroll_summaries'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_batch_id = Column(UUID(as_uuid=True), ForeignKey('payroll_batches.id', ondelete='CASCADE'), nullable=False)
    harvester_id = Column(UUID(as_uuid=True), ForeignKey('harvesters.id'), nullable=False)
    
    total_valid_bunch_count = Column(Integer, nullable=False, default=0)
    total_unripe_bunch_count = Column(Integer, nullable=False, default=0)
    total_net_tonnage_kg = Column(Numeric, nullable=False, default=0)
    total_loose_fruit_premium_rupiah = Column(Numeric, nullable=False, default=0)
    
    fine_mode_used = Column(String(10), nullable=False)
    total_fine_rupiah = Column(Numeric, nullable=False, default=0)
    
    total_tier_premium_rupiah = Column(Numeric, nullable=False, default=0)
    total_net_pay_rupiah = Column(Numeric, nullable=False, default=0)
    
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('payroll_batch_id', 'harvester_id', name='uq_payroll_batch_harvester'),
        Index('idx_payroll_summaries_batch', 'payroll_batch_id')
    )
    
    batch = relationship("PayrollBatch", back_populates="payroll_summaries")
    tier_details = relationship("PayrollTierDetail", back_populates="summary", cascade="all, delete-orphan")

class PayrollTierDetail(Base):
    __tablename__ = 'payroll_tier_details'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_summary_id = Column(UUID(as_uuid=True), ForeignKey('payroll_summaries.id', ondelete='CASCADE'), nullable=False)
    tier_level = Column(Integer, nullable=False)
    kg_in_tier = Column(Numeric, nullable=False)
    rate_per_kg = Column(Numeric, nullable=False)
    subtotal_rupiah = Column(Numeric, nullable=False)

    summary = relationship("PayrollSummary", back_populates="tier_details")

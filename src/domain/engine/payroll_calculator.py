from dataclasses import dataclass
from typing import List, Optional

@dataclass
class EligibilityConfigModel:
    basis_kg: float
    min_bunch_count: int

@dataclass
class TierModel:
    tier_level: int
    min_kg: float
    max_kg: Optional[float]
    rate_per_kg: float

@dataclass
class PayrollTierDetailResult:
    tier_level: int
    kg_in_tier: float
    rate_per_kg: float
    subtotal_rupiah: float

@dataclass
class PayrollSummaryResult:
    total_valid_bunch_count: int
    total_unripe_bunch_count: int
    total_net_tonnage_kg: float
    total_loose_fruit_premium_rupiah: float
    fine_mode_used: str
    total_fine_rupiah: float
    total_tier_premium_rupiah: float
    total_net_pay_rupiah: float
    tier_details: List[PayrollTierDetailResult]

def calculate_monthly_payroll(
    total_valid_bunch_count: int,
    total_unripe_bunch_count: int,
    total_net_tonnage_kg: float,
    total_loose_fruit_premium_rupiah: float,
    total_fine_rupiah: float,
    fine_mode_used: str,
    eligibility: EligibilityConfigModel,
    tiers: List[TierModel]
) -> PayrollSummaryResult:
    
    total_tier_premium_rupiah = 0.0
    tier_details = []
    
    # Gate 1: Lolos Minimum Janjang?
    if total_valid_bunch_count >= eligibility.min_bunch_count:
        # Gate 2: Hitung Lebih Basis
        lebih_basis_kg = max(0.0, total_net_tonnage_kg - eligibility.basis_kg)
        
        remaining_lb = lebih_basis_kg
        
        # Asumsi array tiers sudah terurut berdasarkan tier_level ASC
        for tier in tiers:
            if remaining_lb <= 0:
                break
                
            capacity = (tier.max_kg - tier.min_kg) if tier.max_kg is not None else float('inf')
            
            kg_in_this_tier = min(remaining_lb, capacity)
            subtotal = kg_in_this_tier * tier.rate_per_kg
            
            tier_details.append(PayrollTierDetailResult(
                tier_level=tier.tier_level,
                kg_in_tier=kg_in_this_tier,
                rate_per_kg=tier.rate_per_kg,
                subtotal_rupiah=subtotal
            ))
            
            remaining_lb -= kg_in_this_tier
            total_tier_premium_rupiah += subtotal
            
    total_net_pay = total_loose_fruit_premium_rupiah + total_tier_premium_rupiah - total_fine_rupiah
    
    return PayrollSummaryResult(
        total_valid_bunch_count=total_valid_bunch_count,
        total_unripe_bunch_count=total_unripe_bunch_count,
        total_net_tonnage_kg=total_net_tonnage_kg,
        total_loose_fruit_premium_rupiah=total_loose_fruit_premium_rupiah,
        fine_mode_used=fine_mode_used,
        total_fine_rupiah=total_fine_rupiah,
        total_tier_premium_rupiah=total_tier_premium_rupiah,
        total_net_pay_rupiah=total_net_pay,
        tier_details=tier_details
    )

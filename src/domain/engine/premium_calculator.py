from typing import List, Optional
from pydantic import BaseModel

class TierConfig(BaseModel):
    min_kg: float
    max_kg: Optional[float]
    rate: float

class HarvestConfig(BaseModel):
    flat_rate_percentage: float = 0.10
    loose_fruit_rate: float = 75.0
    base_target_kg: float = 1000.0
    min_bunches_required: int = 100

class PremiumResult(BaseModel):
    harvester_name: str
    total_tonnage: float
    loose_fruit_kg: float
    net_ffb: float
    premium_loose_fruit: float
    premium_ffb: float
    total_final_premium: float
    tier_status: str

def calculate_premium(
    harvester_name: str,
    total_bunches: int,
    avg_bunch_weight: float,
    unripe_penalty: float,
    config: HarvestConfig,
    tiers: List[TierConfig]
) -> PremiumResult:
    # 1. Total Tonnage
    total_tonnage = total_bunches * avg_bunch_weight
    
    # 2. Loose Fruit (Brondolan)
    loose_fruit_kg = total_tonnage * config.flat_rate_percentage
    premium_loose_fruit = loose_fruit_kg * config.loose_fruit_rate
    
    # 3. Net FFB (TBS Bersih)
    net_ffb = total_tonnage - loose_fruit_kg
    
    # 4. Validations & FFB Premium
    premium_ffb = 0.0
    tier_status = "Non-Syarat"
    highest_tier_id = 0
    
    if total_bunches >= config.min_bunches_required:
        over_basis_kg = max(0.0, net_ffb - config.base_target_kg)
        
        if over_basis_kg <= 0:
            tier_status = "Basis"
        else:
            remaining_kg = over_basis_kg
            tier_idx = 1
            for tier in tiers:
                if remaining_kg <= 0:
                    break
                
                # calculate tier capacity
                if tier.max_kg is None:
                    capacity = remaining_kg
                else:
                    if tier.min_kg == 0:
                        capacity = tier.max_kg
                    else:
                        capacity = (tier.max_kg - tier.min_kg) + 1.0
                
                kg_in_tier = min(remaining_kg, capacity)
                if kg_in_tier > 0:
                    highest_tier_id = tier_idx
                
                premium_ffb += kg_in_tier * tier.rate
                remaining_kg -= kg_in_tier
                tier_idx += 1
                
            if highest_tier_id > 0:
                tier_status = f"Tier {highest_tier_id}"
            else:
                tier_status = "Basis"
            
    # 5. Final Calculation
    total_premium = premium_loose_fruit + premium_ffb - unripe_penalty
    total_premium = max(0.0, total_premium) # Ensure no negative payout
    
    return PremiumResult(
        harvester_name=harvester_name,
        total_tonnage=total_tonnage,
        loose_fruit_kg=loose_fruit_kg,
        net_ffb=net_ffb,
        premium_loose_fruit=premium_loose_fruit,
        premium_ffb=premium_ffb,
        total_final_premium=total_premium,
        tier_status=tier_status
    )

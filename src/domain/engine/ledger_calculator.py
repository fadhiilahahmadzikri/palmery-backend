from dataclasses import dataclass
from typing import Literal

@dataclass
class LedgerResult:
    valid_bunch_count: int
    unripe_bunch_count: int
    avg_bunch_weight_kg: float
    gross_tonnage_kg: float
    loose_fruit_percentage_snapshot: float
    loose_fruit_rate_snapshot_rupiah: float
    loose_fruit_deduction_kg: float
    loose_fruit_premium_rupiah: float
    fine_mode_snapshot: str
    fine_amount_rupiah: float
    weight_deduction_kg: float
    net_tonnage_kg: float

def calculate_daily_ledger(
    valid_bunch_count: int,
    unripe_bunch_count: int,
    avg_bunch_weight_kg: float,
    loose_fruit_percentage: float,
    loose_fruit_rate_rupiah: float,
    fine_mode: Literal['rupiah', 'kg'],
    fine_rate_rupiah: float
) -> LedgerResult:
    
    gross_tonnage = float(valid_bunch_count * avg_bunch_weight_kg)
    
    loose_fruit_deduction_kg = gross_tonnage * loose_fruit_percentage
    loose_fruit_premium_rupiah = loose_fruit_deduction_kg * loose_fruit_rate_rupiah
    
    weight_deduction_kg = 0.0
    fine_amount_rupiah = 0.0
    
    if fine_mode == 'kg':
        weight_deduction_kg = unripe_bunch_count * avg_bunch_weight_kg
    elif fine_mode == 'rupiah':
        fine_amount_rupiah = unripe_bunch_count * fine_rate_rupiah
        
    net_tonnage_kg = gross_tonnage - loose_fruit_deduction_kg - weight_deduction_kg
    
    return LedgerResult(
        valid_bunch_count=valid_bunch_count,
        unripe_bunch_count=unripe_bunch_count,
        avg_bunch_weight_kg=avg_bunch_weight_kg,
        gross_tonnage_kg=gross_tonnage,
        loose_fruit_percentage_snapshot=loose_fruit_percentage,
        loose_fruit_rate_snapshot_rupiah=loose_fruit_rate_rupiah,
        loose_fruit_deduction_kg=loose_fruit_deduction_kg,
        loose_fruit_premium_rupiah=loose_fruit_premium_rupiah,
        fine_mode_snapshot=fine_mode,
        fine_amount_rupiah=fine_amount_rupiah,
        weight_deduction_kg=weight_deduction_kg,
        net_tonnage_kg=net_tonnage_kg
    )

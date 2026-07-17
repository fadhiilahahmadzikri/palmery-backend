import json
import os
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

def generate_demo_data():
    fake = Faker('id_ID')
    
    # Ensure demo directory exists
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'demo')
    os.makedirs(demo_dir, exist_ok=True)
    
    # 1. Configs
    configs = [
        {"id": 1, "config_key": "BASE_TARGET_KG", "config_value": 1000.0},
        {"id": 2, "config_key": "FLAT_RATE_PERCENTAGE", "config_value": 0.1},
        {"id": 3, "config_key": "LOOSE_FRUIT_RATE", "config_value": 75.0},
        {"id": 4, "config_key": "MIN_BUNCHES_REQUIRED", "config_value": 100.0}
    ]
    with open(os.path.join(demo_dir, 'config.json'), 'w') as f:
        json.dump(configs, f, indent=4)
        
    # 2. Tiers
    tiers = [
        {"id": 1, "tier_level": 1, "min_kg": 0.0, "max_kg": 500.0, "rate_per_kg": 150.0},
        {"id": 2, "tier_level": 2, "min_kg": 501.0, "max_kg": 1000.0, "rate_per_kg": 200.0},
        {"id": 3, "tier_level": 3, "min_kg": 1001.0, "max_kg": None, "rate_per_kg": 250.0}
    ]
    with open(os.path.join(demo_dir, 'tiers.json'), 'w') as f:
        json.dump(tiers, f, indent=4)
        
    # 3. Harvest Records
    records = []
    
    harvesters = [fake.name() for _ in range(20)]
    
    start_date = datetime.now() - timedelta(days=180)
    
    record_id = 1
    for _ in range(500):
        date = start_date + timedelta(days=random.randint(0, 180))
        harvester = random.choice(harvesters)
        
        # Realistically, a harvester brings 50 to 300 bunches, weight 10-30kg
        bunches = random.randint(50, 300)
        weight = round(random.uniform(10.0, 30.0), 2)
        penalty = random.choice([0, 0, 0, 5000, 10000, 20000])
        
        total_tonnage = bunches * weight
        loose_fruit_kg = round(total_tonnage * 0.1, 2)
        net_ffb = round(total_tonnage - loose_fruit_kg, 2)
        premium_loose_fruit = loose_fruit_kg * 75.0
        
        premium_ffb = 0.0
        tier_status = "Non-Syarat"
        
        if bunches >= 100:
            excess = max(0, net_ffb - 1000.0)
            if excess <= 0:
                tier_status = "Basis"
            else:
                highest_tier = 0
                remaining = excess
                for t in tiers:
                    if remaining <= 0:
                        break
                    
                    capacity = remaining
                    if t["max_kg"] is not None:
                        if t["min_kg"] == 0:
                            cap = t["max_kg"]
                        else:
                            cap = (t["max_kg"] - t["min_kg"]) + 1.0
                        capacity = min(remaining, cap)
                        
                    premium_ffb += capacity * t["rate_per_kg"]
                    remaining -= capacity
                    highest_tier = t["tier_level"]
                
                tier_status = f"Tier {highest_tier}"
                
        total_premium = premium_loose_fruit + premium_ffb - penalty
        total_premium = max(0, total_premium)
        
        records.append({
            "id": str(uuid.uuid4()),
            "harvest_date": date.date().isoformat(),
            "harvester_name": harvester,
            "input_total_bunches": bunches,
            "input_avg_bunch_weight": weight,
            "input_unripe_penalty": penalty,
            "calc_total_tonnage": round(total_tonnage, 2),
            "calc_loose_fruit_kg": loose_fruit_kg,
            "calc_net_ffb": net_ffb,
            "premium_loose_fruit": premium_loose_fruit,
            "premium_ffb": premium_ffb,
            "total_final_premium": total_premium,
            "tier_status": tier_status
        })
        record_id += 1
        
    # Sort by date descending
    records.sort(key=lambda x: x["harvest_date"], reverse=True)
    
    with open(os.path.join(demo_dir, 'harvest.json'), 'w') as f:
        json.dump(records, f, indent=4)
        
    print(f"Generated {len(records)} harvest records, {len(configs)} configs, {len(tiers)} tiers in demo/")

if __name__ == "__main__":
    generate_demo_data()

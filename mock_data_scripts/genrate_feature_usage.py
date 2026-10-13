import os
import random
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_FILE = "feature_usage.csv"
FEATURES = ["api_calls", "report_export", "seat_added", "dashboard_view", "webhook_trigger"]

def generate_feature_usage(num_rows=15000):
    rows = []
    base_date = datetime.now() - timedelta(days=180)

    for _ in range(num_rows):
        event_date = base_date + timedelta(days=random.randint(0, 180))
        fmt_choice = random.random()
        if fmt_choice < 0.60:
            date_str = event_date.strftime("%Y-%m-%d")
        elif fmt_choice < 0.85:
            date_str = event_date.strftime("%m/%d/%Y")
        else:
            date_str = event_date.strftime("%d-%m-%Y")

        user_id = random.randint(1, 2500)
        if random.random() < 0.03:
            user_id = random.randint(90000, 99999)  # Orphaned ID

        org_id = random.randint(1, 300)
        feature = random.choice(FEATURES) if random.random() > 0.04 else ""

        raw_count = random.randint(1, 500)
        rand_metric = random.random()
        if rand_metric < 0.03:
            usage_count = -random.randint(1, 50)       # Negative anomaly
        elif rand_metric < 0.07:
            usage_count = f"{raw_count:,}"             # String commas
        elif rand_metric < 0.10:
            usage_count = f"${raw_count}"              # Currency symbol
        else:
            usage_count = raw_count

        rows.append({
            "UserId": user_id,
            "OrgId": org_id,
            "UsageDate": date_str,
            "FeatureName": feature,
            "UsageCount": usage_count
        })

    df = pd.DataFrame(rows)
    # Inject 4% duplicate rows
    duplicates = df.sample(frac=0.04, random_state=42)
    df = pd.concat([df, duplicates], ignore_index=True).sample(frac=1.0, random_state=42)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Generated {len(df)} rows in {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_feature_usage()
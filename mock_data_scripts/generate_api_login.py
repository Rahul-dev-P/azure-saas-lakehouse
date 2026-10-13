import json
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_FILE = "logins_batch_1.json"
CLIENT_DEVICES = ["Chrome/Mac", "Safari/iOS", "Chrome/Windows", "Firefox/Linux", "Edge/Windows", "Unknown"]

def generate_api_batch(num_events=10000):
    events = []
    base_time = datetime.now() - timedelta(days=60)

    for i in range(num_events):
        event_time = base_time + timedelta(minutes=random.randint(1, 60 * 24 * 60))
        # Mix ISO UTC strings and explicit offset notations
        timestamp_str = event_time.strftime("%Y-%m-%dT%H:%M:%S") + ("Z" if random.random() > 0.3 else "+00:00")
        
        user_uid = random.randint(1, 2500)
        if random.random() < 0.02:
            user_uid = random.randint(90000, 99999)  # Orphaned User ID

        events.append({
            "event_id": str(uuid.uuid4()),
            "user_uid": user_uid,
            "ip_address": f"{random.randint(11, 200)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
            "client_device": random.choice(CLIENT_DEVICES),
            "login_success": random.random() > 0.08,
            "event_timestamp": timestamp_str
        })

    # Simulate network retries by cloning ~3% of events with identical event_ids
    duplicate_events = random.sample(events, int(num_events * 0.03))
    events.extend(duplicate_events)
    random.shuffle(events)

    payload = {
        "source": "saas_identity_api",
        "batch_id": "batch_2026_001",
        "record_count": len(events),
        "data": events
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Generated {len(events)} login records in {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_api_batch()
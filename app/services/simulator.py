"""
TruckIT Daily Request Simulator
================================================
Runs as a cron job on Railway 5 times per day.

Schedule (Railway cron):
  0  8 * * *   → 8am   morning rush
  0 11 * * *   → 11am  late morning
  0 14 * * *   → 2pm   afternoon
  0 17 * * *   → 5pm   evening rush
  0 20 * * *   → 8pm   night

Each run:
  Step 1 — Reset all trucks to available in Redis
  Step 2 — Create 100 fresh customers in Postgres
  Step 3 — Send 100 move requests via the API

Daily totals:
  500 requests/day  (100 × 5 runs)
  500 customers/day (100 × 5 runs)

By end of year:
  500 customers/day   × 365 = 182,500 customers
  500 assignments/day × 365 = 182,500 assignments
"""

import requests
import psycopg2
import redis
import random
import time
import os
from datetime import datetime
from faker import Faker

fake = Faker("en_CA")

# ── config ────────────────────────────────────────────────────────────────────
API_BASE_URL           = os.getenv("API_BASE_URL", "http://localhost:9010")
TOTAL_REQUESTS         = int(os.getenv("DAILY_REQUESTS", "100"))   # per run
DELAY_BETWEEN_REQUESTS = float(os.getenv("REQUEST_DELAY_SECONDS", "1.5"))

# ── city config ───────────────────────────────────────────────────────────────
CITIES = {
    "calgary":    {"bounds": (50.99, 51.18, -114.27, -113.86), "weight": 15},
    "edmonton":   {"bounds": (53.40, 53.70, -113.71, -113.27), "weight": 13},
    "vancouver":  {"bounds": (49.15, 49.40, -123.27, -122.90), "weight": 15},
    "toronto":    {"bounds": (43.58, 43.85, -79.64,  -79.12),  "weight": 15},
    "montreal":   {"bounds": (45.42, 45.70, -73.97,  -73.47),  "weight": 13},
    "ottawa":     {"bounds": (45.25, 45.53, -75.92,  -75.47),  "weight": 10},
    "winnipeg":   {"bounds": (49.77, 50.01, -97.32,  -96.95),  "weight": 10},
    "halifax":    {"bounds": (44.57, 44.73, -63.70,  -63.46),  "weight":  9},
    "saskatoon":  {"bounds": (52.08, 52.22, -106.78, -106.55), "weight":  7},
    "regina":     {"bounds": (50.38, 50.52, -104.75, -104.52), "weight":  7},
}

TRUCK_TYPES          = ["cargo_van", "small_truck", "medium_truck", "large_truck", "specialty_truck"]
SERVICE_TYPES        = ["packing", "loading", "full_move"]
TRUCK_TYPE_WEIGHTS   = [20, 30, 25, 15, 10]
SERVICE_TYPE_WEIGHTS = [15, 20, 65]


# ── connections ───────────────────────────────────────────────────────────────
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5433)),
        dbname=os.getenv("DB_NAME", "truckit"),
        user=os.getenv("DB_USER", "truckit"),
        password=os.getenv("DB_PASSWORD", "truckit123")
    )


def get_redis():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=False
    )


# ── step 1: reset trucks ──────────────────────────────────────────────────────
def reset_trucks():
    """
    Resets all trucks to available in Redis before each run.
    Preserves driver_id and type — only updates status.
    """
    r = get_redis()
    keys = r.keys("truck:*")

    if not keys:
        print(" No trucks found in Redis — run seed_canada.py first")
        return

    pipe = r.pipeline()
    for key in keys:
        pipe.hset(key, "status", "available")
    pipe.execute()

    print(f" Reset {len(keys):,} trucks to available")


# ── step 2: create customers ──────────────────────────────────────────────────
def create_customers(db_conn, count: int) -> list:
    """
    Creates `count` fresh customers in Postgres.
    Returns list of (customer_id, city) tuples.
    """
    cursor   = db_conn.cursor()
    date_str = datetime.now().strftime("%Y%m%d%H%M")  # includes time for uniqueness across runs
    customers = []

    for i in range(1, count + 1):
        city        = pick_city()
        customer_id = f"cust:{date_str}-{i}"

        cursor.execute("""
            INSERT INTO customers (customer_id, name, email, phone, city)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO NOTHING
        """, (
            customer_id,
            fake.name(),
            fake.email(),
            fake.phone_number(),
            city,
        ))
        customers.append((customer_id, city))

    db_conn.commit()
    cursor.close()
    return customers


# ── step 3: send requests ─────────────────────────────────────────────────────
def send_request(payload: dict) -> bool:
    try:
        response = requests.post(
            f"{API_BASE_URL}/truck/move/request",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        print(f" Connection error — is the API running at {API_BASE_URL}?")
        return False
    except requests.exceptions.Timeout:
        print(f"  Request timed out")
        return False
    except requests.exceptions.HTTPError as e:
        print(f" HTTP {e.response.status_code} — {e.response.text}")
        return False
    except Exception as e:
        print(f"  Unexpected error: {e}")
        return False


# ── helpers ───────────────────────────────────────────────────────────────────
def pick_city() -> str:
    cities  = list(CITIES.keys())
    weights = [CITIES[c]["weight"] for c in cities]
    return random.choices(cities, weights=weights)[0]


def random_coord_in_city(city_name: str) -> tuple:
    bounds = CITIES[city_name]["bounds"]
    lat_min, lat_max, lng_min, lng_max = bounds
    return (
        round(random.uniform(lat_min, lat_max), 6),
        round(random.uniform(lng_min, lng_max), 6),
    )


# ── main simulation ───────────────────────────────────────────────────────────
def run_simulation():
    now = datetime.now()
    print(f"\n🚛 TruckIT Simulator — Run {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Target  : {TOTAL_REQUESTS} requests this run")
    print(f"   API     : {API_BASE_URL}\n")

    # step 1 — reset trucks
    print(" Step 1: Resetting trucks...")
    reset_trucks()
    print()

    # step 2 — create fresh customers
    print(f" Step 2: Creating {TOTAL_REQUESTS} fresh customers...")
    try:
        db_conn   = get_db()
        customers = create_customers(db_conn, TOTAL_REQUESTS)
        db_conn.close()
        print(f" {len(customers)} customers created\n")
    except Exception as e:
        print(f" Failed to create customers: {e}")
        print(f"     Make sure seed_canada.py has been run first")
        exit(1)

    # step 3 — send move requests
    print(f"  Step 3: Sending {TOTAL_REQUESTS} move requests...\n")

    success_count = 0
    failure_count = 0
    city_counts   = {city: 0 for city in CITIES}
    type_counts   = {t: 0 for t in TRUCK_TYPES}

    for i, (customer_id, city) in enumerate(customers, 1):
        pickup_lat,  pickup_lng  = random_coord_in_city(city)
        dropoff_lat, dropoff_lng = random_coord_in_city(city)
        truck_type   = random.choices(TRUCK_TYPES,   weights=TRUCK_TYPE_WEIGHTS)[0]
        service_type = random.choices(SERVICE_TYPES, weights=SERVICE_TYPE_WEIGHTS)[0]

        payload = {
            "customer_id":  customer_id,
            "pickup_lat":   pickup_lat,
            "pickup_lng":   pickup_lng,
            "dropoff_lat":  dropoff_lat,
            "dropoff_lng":  dropoff_lng,
            "truck_type":   truck_type,
            "service_type": service_type,
        }

        print(
            f"  [{i:>3}/{TOTAL_REQUESTS}] "
            f"{city:<12} | "
            f"{truck_type:<16} | "
            f"{service_type:<10} | "
            f"{customer_id}"
        )

        success = send_request(payload)

        if success:
            success_count     += 1
            city_counts[city] += 1
            type_counts[truck_type] += 1
        else:
            failure_count += 1

        if i < TOTAL_REQUESTS:
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # ── summary ───────────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"📊 Run Summary — {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'─' * 60}")
    print(f" Successful : {success_count}")
    print(f"  Failed     : {failure_count}")

    print(f"\n  Requests by city:")
    for city, count in sorted(city_counts.items(), key=lambda x: -x[1]):
        if count > 0:
            bar = "█" * count
            print(f"    {city:<12} : {count:>3}  {bar}")

    print(f"\n  Requests by truck type:")
    for truck_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"    {truck_type:<20} : {count:>3}  {bar}")

    print(f"{'─' * 60}\n")

    if failure_count == TOTAL_REQUESTS:
        print(" All requests failed — check API_BASE_URL and ensure app is running")
        exit(1)
    elif failure_count > 0:
        print(f" {failure_count} requests failed — check logs above")
    else:
        print(" All requests sent successfully")


if __name__ == "__main__":
    run_simulation()
"""
TruckIT Consumer — Truck Matching Engine

Redis is kept lightweight:
    - geosearch  → finds nearby trucks by location + type
    - hget/hset  → checks status, marks busy (3 fields only)

All driver/truck details are fetched from Postgres after match.
"""

from kafka import KafkaConsumer
from math import radians, sin, cos, sqrt, atan2
import redis
import json
import psycopg2
import os



def haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return round(R * 2 * atan2(sqrt(a), sqrt(1 - a)), 2)


consumer = KafkaConsumer(
    "truck.move.requested",
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    auto_offset_reset="latest",
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=False
)

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 5433)),
    dbname=os.getenv("DB_NAME", "truckit"),
    user=os.getenv("DB_USER", "truckit"),
    password=os.getenv("DB_PASSWORD", "truckit123")
)

GEO_KEY = "trucks"

print(" Truck Matching Engine Started...")

# ── main loop ─────────────────────────────────────────────────────────────────
for message in consumer:
    cursor = conn.cursor()
    try:
        data = message.value

        customer_id    = data.get("customer_id")
        pickup_lat     = data.get("pickup_lat")
        pickup_lng     = data.get("pickup_lng")
        dropoff_lat    = data.get("dropoff_lat")
        dropoff_lng    = data.get("dropoff_lng")
        requested_type = data.get("truck_type")
        service_type   = data.get("service_type")

        if not all([pickup_lat, pickup_lng, customer_id, requested_type]):
            print(f"  Invalid message — missing required fields: {data}")
            continue

        print(f"\n  Request | Customer: {customer_id} | Type: {requested_type} | Service: {service_type}")

        assigned             = None
        driver_id            = None
        driver_name          = None
        truck_type           = None
        truck_description    = None
        capacity_kg          = None
        driver_to_pickup_km  = None
        pickup_to_dropoff_km = None

        # ── pickup → dropoff distance (haversine) ─────────────────────────────
        if dropoff_lat and dropoff_lng:
            pickup_to_dropoff_km = haversine(
                pickup_lat, pickup_lng, dropoff_lat, dropoff_lng
            )

        # ── geo search with expanding radius ─────────────────────────────────
        for radius in [5, 10, 25, 50]:
            raw_trucks = r.geosearch(
                GEO_KEY,
                longitude=pickup_lng,
                latitude=pickup_lat,
                radius=radius,
                unit="km",
                withdist=True,
                sort="ASC"
            )

            # filter: available + correct truck type (Redis only holds 3 fields)
            available = [
                (name.decode("utf-8"), round(dist, 2))
                for name, dist in raw_trucks
                if r.hget(name, "status") == b"available"
                and r.hget(name, "type") == requested_type.encode()
            ]

            if available:
                assigned, driver_to_pickup_km = available[0]


                driver_id = r.hget(assigned, "driver_id").decode("utf-8")


                cursor.execute("""
                    SELECT
                        d.name,
                        t.type,
                        t.description,
                        t.capacity_kg
                    FROM trucks t
                    JOIN drivers d ON t.driver_id = d.driver_id
                    WHERE t.truck_id = %s
                """, (assigned,))

                row = cursor.fetchone()
                if row:
                    driver_name, truck_type, truck_description, capacity_kg = row


                r.hset(assigned, mapping={
                    "status":    "busy",
                    "driver_id": driver_id,
                    "type":      requested_type
                })

                print(f"     Assigned : {assigned}")
                print(f"     Driver   : {driver_name} ({driver_id})")
                print(f"     Truck    : {truck_type} — {truck_description}")
                print(f"     Capacity : {capacity_kg}kg")
                print(f"     Distance : Driver → Pickup {driver_to_pickup_km}km | Pickup → Dropoff {pickup_to_dropoff_km}km")
                break

        if not assigned:
            print(f"  No available {requested_type} found within 50km")

        # ── save to Postgres ──────────────────────────────────────────────────
        cursor.execute("""
            INSERT INTO move_assignments (
                customer_id, pickup_lat, pickup_lng,
                dropoff_lat, dropoff_lng, assigned_truck,
                driver_id, driver, truck_type, service_type,
                driver_to_pickup_km, pickup_to_dropoff_km,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            customer_id, pickup_lat, pickup_lng,
            dropoff_lat, dropoff_lng, assigned,
            driver_id, driver_name, truck_type, service_type,
            driver_to_pickup_km, pickup_to_dropoff_km,
            "ASSIGNED" if assigned else "PENDING"
        ))

        conn.commit()
        print(f" Saved to Postgres — status: {'ASSIGNED' if assigned else 'PENDING'}")

    except Exception as e:
        conn.rollback()
        print(f"  Error processing message: {e}")
    finally:
        cursor.close()
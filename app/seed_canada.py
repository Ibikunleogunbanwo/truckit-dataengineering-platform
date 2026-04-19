"""
TruckIT Canada Seed Script
================================================
Seeds drivers and trucks only.
Customers are created daily by the simulator.

Scale:
  8 cities × 200 trucks = 1,600 trucks total
  8 cities × 200 drivers = 1,600 drivers total

Zones per city (7 zones × 25 trucks + 25 random = 200):
  downtown, airport, suburbs, industrial,
  university, hospital, shopping_mall

Coordinates are generated programmatically from
zone center points using random offsets — no
hardcoded coordinate lists.

Redis hash — 3 fields only:
  status    → available / busy
  driver_id → FK to Postgres
  type      → for geosearch filtering
"""

import psycopg2
import redis
import random
from faker import Faker

fake = Faker("en_CA")

# ── connections ───────────────────────────────────────────────────────────────
conn = psycopg2.connect(
    host="localhost", port=5433,
    dbname="truckit", user="truckit", password="truckit123"
)
cursor = conn.cursor()
r = redis.Redis(host="localhost", port=6379, decode_responses=False)

# ── constants ─────────────────────────────────────────────────────────────────
GEO_KEY            = "trucks"
TRUCKS_PER_ZONE    = 125  # 7 zones × 125 = 875 + 125 random = 1000
RANDOM_TRUCKS      = 125
ZONE_SPREAD_KM     = 0.03 # ~3km spread around each zone center

TRUCK_TYPES = [
    "cargo_van",
    "small_truck",
    "medium_truck",
    "large_truck",
    "specialty_truck",
]

CAPACITY_BY_TYPE = {
    "cargo_van":        500,
    "small_truck":     1500,
    "medium_truck":    3500,
    "large_truck":     7000,
    "specialty_truck": 2000,
}

TRUCK_TYPE_DESCRIPTION = {
    "cargo_van":        "Studio or 1-bedroom apartment moves",
    "small_truck":      "1 to 2 bedroom apartment moves",
    "medium_truck":     "2 to 3 bedroom house moves",
    "large_truck":      "4+ bedroom house or office moves",
    "specialty_truck":  "Piano, fragile items, climate-controlled moves",
}

# ── city definitions ──────────────────────────────────────────────────────────
# Each city has 7 zone centers + a bounding box for random trucks
# Zone centers are real landmark coordinates per city

CITIES = {
    "calgary": {
        "bounds": (50.99, 51.18, -114.27, -113.86),
        "random_radius": 0.15,
        "zones": {
            "downtown":     (51.0447, -114.0719),
            "airport":      (51.1315, -114.0100),
            "suburbs":      (51.0892, -114.1523),
            "industrial":   (51.0273, -114.0023),
            "university":   (51.0798, -114.1354),
            "hospital":     (51.0643, -114.0892),
            "shopping_mall":(51.0234, -114.0523),
        },
    },
    "edmonton": {
        "bounds": (53.40, 53.70, -113.71, -113.27),
        "random_radius": 0.15,
        "zones": {
            "downtown":     (53.5461, -113.4938),
            "airport":      (53.3097, -113.5797),
            "suburbs":      (53.5892, -113.3456),
            "industrial":   (53.5123, -113.3789),
            "university":   (53.5232, -113.5263),
            "hospital":     (53.5356, -113.4612),
            "shopping_mall":(53.5678, -113.4123),
        },
    },
    "vancouver": {
        "bounds": (49.15, 49.40, -123.27, -122.90),
        "random_radius": 0.15,
        "zones": {
            "downtown":     (49.2827, -123.1207),
            "airport":      (49.1967, -123.1815),
            "suburbs":      (49.3234, -123.0712),
            "industrial":   (49.2634, -123.0234),
            "university":   (49.2661, -123.2494),
            "hospital":     (49.2578, -123.1234),
            "shopping_mall":(49.2456, -123.0089),
        },
    },
    "toronto": {
        "bounds": (43.58, 43.85, -79.64, -79.12),
        "random_radius": 0.15,
        "zones": {
            "downtown":     (43.6532, -79.3832),
            "airport":      (43.6778, -79.6312),
            "suburbs":      (43.7234, -79.4123),
            "industrial":   (43.6234, -79.5012),
            "university":   (43.6629, -79.3957),
            "hospital":     (43.6589, -79.3890),
            "shopping_mall":(43.7789, -79.3456),
        },
    },
    "montreal": {
        "bounds": (45.42, 45.70, -73.97, -73.47),
        "random_radius": 0.15,
        "zones": {
            "downtown":     (45.5017, -73.5673),
            "airport":      (45.4706, -73.7408),
            "suburbs":      (45.5456, -73.6234),
            "industrial":   (45.5234, -73.6789),
            "university":   (45.5048, -73.5772),
            "hospital":     (45.5123, -73.5812),
            "shopping_mall":(45.4756, -73.6234),
        },
    },
    "ottawa": {
        "bounds": (45.25, 45.53, -75.92, -75.47),
        "random_radius": 0.12,
        "zones": {
            "downtown":     (45.4215, -75.6972),
            "airport":      (45.3223, -75.6692),
            "suburbs":      (45.4678, -75.7456),
            "industrial":   (45.3912, -75.6234),
            "university":   (45.4234, -75.6823),
            "hospital":     (45.4189, -75.7012),
            "shopping_mall":(45.3456, -75.7234),
        },
    },
    "winnipeg": {
        "bounds": (49.77, 50.01, -97.32, -96.95),
        "random_radius": 0.12,
        "zones": {
            "downtown":     (49.8951, -97.1384),
            "airport":      (49.9100, -97.2392),
            "suburbs":      (49.9345, -97.0923),
            "industrial":   (49.8678, -97.0234),
            "university":   (49.8084, -97.1375),
            "hospital":     (49.8923, -97.1456),
            "shopping_mall":(49.8456, -97.2012),
        },
    },
    "halifax": {
        "bounds": (44.57, 44.73, -63.70, -63.46),
        "random_radius": 0.10,
        "zones": {
            "downtown":     (44.6488, -63.5752),
            "airport":      (44.8808, -63.5086),
            "suburbs":      (44.6834, -63.6234),
            "industrial":   (44.6234, -63.5678),
            "university":   (44.6367, -63.5917),
            "hospital":     (44.6512, -63.5923),
            "shopping_mall":(44.6678, -63.6012),
        },
    },
    "saskatoon": {
        "bounds": (52.08, 52.22, -106.78, -106.55),
        "random_radius": 0.10,
        "zones": {
            "downtown":     (52.1332, -106.6700),
            "airport":      (52.1707, -106.6997),
            "suburbs":      (52.1489, -106.5934),
            "industrial":   (52.1056, -106.6234),
            "university":   (52.1338, -106.6318),
            "hospital":     (52.1278, -106.6512),
            "shopping_mall":(52.1423, -106.7123),
        },
    },
    "regina": {
        "bounds": (50.38, 50.52, -104.75, -104.52),
        "random_radius": 0.10,
        "zones": {
            "downtown":     (50.4452, -104.6189),
            "airport":      (50.4320, -104.6658),
            "suburbs":      (50.4789, -104.5678),
            "industrial":   (50.4123, -104.5912),
            "university":   (50.4167, -104.5933),
            "hospital":     (50.4512, -104.6334),
            "shopping_mall":(50.4678, -104.6789),
        },
    },
}

ZONES = [
    "downtown", "airport", "suburbs", "industrial",
    "university", "hospital", "shopping_mall"
]


# ── helpers ───────────────────────────────────────────────────────────────────
def zone_offset(center_lat, center_lng, spread=ZONE_SPREAD_KM):
    """Generate a random coordinate within spread degrees of a zone center."""
    lat = center_lat + random.uniform(-spread, spread)
    lng = center_lng + random.uniform(-spread, spread)
    return round(lat, 6), round(lng, 6)


def city_offset(bounds, radius):
    """Generate a random coordinate anywhere within a city bounding box."""
    lat_min, lat_max, lng_min, lng_max = bounds
    return (
        round(random.uniform(lat_min, lat_max), 6),
        round(random.uniform(lng_min, lng_max), 6),
    )


def pick_truck_type(index: int) -> str:
    """Cycle through truck types evenly."""
    return TRUCK_TYPES[index % len(TRUCK_TYPES)]


# ── table creation ────────────────────────────────────────────────────────────
def create_tables():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id  VARCHAR(50) PRIMARY KEY,
            name         VARCHAR(100),
            email        VARCHAR(100),
            phone        VARCHAR(20),
            city         VARCHAR(50),
            created_at   TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS drivers (
            driver_id    VARCHAR(50) PRIMARY KEY,
            name         VARCHAR(100),
            email        VARCHAR(100),
            phone        VARCHAR(20),
            city         VARCHAR(50),
            license_no   VARCHAR(20),
            created_at   TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS trucks (
            truck_id     VARCHAR(50) PRIMARY KEY,
            driver_id    VARCHAR(50) REFERENCES drivers(driver_id),
            type         VARCHAR(50),
            description  VARCHAR(200),
            plate        VARCHAR(20),
            city         VARCHAR(50),
            zone         VARCHAR(50),
            capacity_kg  INTEGER,
            created_at   TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS move_assignments (
            id                   SERIAL PRIMARY KEY,
            customer_id          VARCHAR(50),
            pickup_lat           FLOAT,
            pickup_lng           FLOAT,
            dropoff_lat          FLOAT,
            dropoff_lng          FLOAT,
            assigned_truck       VARCHAR(50),
            driver_id            VARCHAR(50),
            driver               VARCHAR(100),
            truck_type           VARCHAR(50),
            service_type         VARCHAR(50),
            driver_to_pickup_km  FLOAT,
            pickup_to_dropoff_km FLOAT,
            status               VARCHAR(20),
            created_at           TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    print(" Tables created / verified")


# ── clear ─────────────────────────────────────────────────────────────────────
def clear_existing():
    cursor.execute("TRUNCATE TABLE move_assignments;")
    cursor.execute("TRUNCATE TABLE trucks CASCADE;")
    cursor.execute("TRUNCATE TABLE drivers CASCADE;")
    cursor.execute("TRUNCATE TABLE customers;")
    conn.commit()
    r.flushall()
    print(" Cleared Postgres + Redis")


# ── seed one truck + driver ───────────────────────────────────────────────────
def seed_truck(truck_id, driver_id, driver_name, truck_type, city, zone, lat, lng):
    capacity    = CAPACITY_BY_TYPE[truck_type]
    description = TRUCK_TYPE_DESCRIPTION[truck_type]

    cursor.execute("""
        INSERT INTO drivers (driver_id, name, email, phone, city, license_no)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (driver_id) DO NOTHING
    """, (
        driver_id, driver_name,
        fake.email(), fake.phone_number(),
        city, f"LIC-{random.randint(100000, 999999)}"
    ))

    cursor.execute("""
        INSERT INTO trucks (truck_id, driver_id, type, description, plate, city, zone, capacity_kg)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (truck_id) DO NOTHING
    """, (
        truck_id, driver_id, truck_type,
        description, fake.license_plate(),
        city, zone, capacity
    ))

    # Redis: geo location
    r.geoadd(GEO_KEY, [lng, lat, truck_id])

    # Redis: 3 fields only
    r.hset(truck_id, mapping={
        "status":    "available",
        "driver_id": driver_id,
        "type":      truck_type,
    })


# ── seed one city ─────────────────────────────────────────────────────────────
def seed_city(city_name, city_data):
    bounds  = city_data["bounds"]
    radius  = city_data["random_radius"]
    zones   = city_data["zones"]
    count   = 0

    # 7 zones × 25 trucks = 175 zone trucks
    for zone_name in ZONES:
        zone_lat, zone_lng = zones[zone_name]
        for i in range(TRUCKS_PER_ZONE):
            count    += 1
            truck_id  = f"truck:{city_name}-{count}"
            driver_id = f"driver:{city_name}-{count}"
            lat, lng  = zone_offset(zone_lat, zone_lng)
            seed_truck(
                truck_id, driver_id, fake.name(),
                pick_truck_type(count), city_name, zone_name, lat, lng
            )

    # 25 fully random trucks spread across the city
    for truck_type in TRUCK_TYPES:
        for _ in range(RANDOM_TRUCKS // len(TRUCK_TYPES)):
            count    += 1
            truck_id  = f"truck:{city_name}-{count}"
            driver_id = f"driver:{city_name}-{count}"
            lat, lng  = city_offset(bounds, radius)
            seed_truck(
                truck_id, driver_id, fake.name(),
                truck_type, city_name, "random", lat, lng
            )

    conn.commit()
    print(f"  {city_name.capitalize()}: {count} trucks + {count} drivers seeded")
    return count


# ── verification ──────────────────────────────────────────────────────────────
def verify():
    cursor.execute("SELECT COUNT(*) FROM drivers")
    drivers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM trucks")
    trucks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers")
    customers = cursor.fetchone()[0]

    redis_geo    = r.zcard(GEO_KEY)
    redis_hashes = len(r.keys("truck:*"))

    print(f"\n Seed Summary")
    print(f"  Postgres customers : {customers}  ← grows daily via simulator")
    print(f"  Postgres drivers   : {drivers}")
    print(f"  Postgres trucks    : {trucks}")
    print(f"  Redis geo set      : {redis_geo}")
    print(f"  Redis hashes       : {redis_hashes}")

    if redis_geo != trucks:
        print(f"\n  Mismatch — geo={redis_geo} postgres={trucks}")
    else:
        print(f"  Redis geo + Postgres in sync")

    print(f"\n  Redis hash sample (truck:calgary-1) — should be 3 fields:")
    sample = r.hgetall("truck:calgary-1")
    for k, v in sample.items():
        print(f"    {k.decode():<12} → {v.decode()}")

    cursor.execute("SELECT type, COUNT(*) FROM trucks GROUP BY type ORDER BY type")
    print(f"\n  Trucks by type:")
    for row in cursor.fetchall():
        print(f"    {row[0]:<20} : {row[1]}")

    cursor.execute("SELECT zone, COUNT(*) FROM trucks GROUP BY zone ORDER BY zone")
    print(f"\n  Trucks by zone:")
    for row in cursor.fetchall():
        print(f"    {row[0]:<15} : {row[1]}")

    cursor.execute("SELECT city, COUNT(*) FROM trucks GROUP BY city ORDER BY city")
    print(f"\n  Trucks by city:")
    for row in cursor.fetchall():
        print(f"    {row[0].capitalize():<12} : {row[1]}")


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚛 TruckIT Canada Seed Script\n")
    create_tables()
    clear_existing()

    total = 0
    for city_name, city_data in CITIES.items():
        total += seed_city(city_name, city_data)

    verify()

    cursor.close()
    conn.close()
    print(f"\n Seed complete")
    print(f"   {total} trucks + {total} drivers across 8 cities")
    print(f"   7 zones per city: downtown, airport, suburbs, industrial,")
    print(f"                     university, hospital, shopping_mall")
    print(f"   Customers will be created daily by the simulator\n")
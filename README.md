# TruckIT - Moving Services Platform

**This is my original product idea.**

TruckIT is a moving services platform I came up with and designed from scratch. The idea is simple: make booking a move as easy as booking a ride. Customers pick up their truck type, set a pickup and dropoff location, and the platform finds the nearest available driver. No back-and-forth calls, no guessing on price.

This repo is the **backend prototype and data simulation layer**. I built it to validate the matching logic, test the data architecture, and start generating realistic data before the full product goes into development. The complete product has been designed in Figma and broken down into user stories across four modules: Customer, Driver, Mover, and Admin.

👉 **[View the Figma Prototype](https://www.figma.com/proto/75QBEKsdixUlP1dGb7OOF2/TruckIT?node-id=232-43&t=2saNmEXCNyX159Zg-1&hide-ui=1)**

---

## The Idea

Moving is stressful. Finding a truck, negotiating prices, hoping the driver shows up on time - it is a mess. TruckIT fixes that by connecting customers directly with verified truck drivers in their city. Drivers get a steady stream of jobs. Customers get a transparent, trackable experience from booking to delivery.

The platform covers three types of users: customers who need to move, drivers who own trucks, and movers who help with packing and loading. There is also an admin dashboard for managing the whole operation.

---

## Product Modules

| Module | Platform | Stories | What it covers |
|---|---|---|---|
| Customer | Mobile App | 11 | Book moves, track driver, payment, move history |
| Driver | Mobile App | 11 | Accept jobs, navigation, earnings, availability toggle |
| Mover | Mobile App | 10 | Browse jobs, accept packing and loading work, earnings |
| Admin | Web Dashboard | 6 | Manage users, assign jobs, reports, platform settings |

A few examples from the user stories document:

**CUS-05 - Create Move Request**
> As a customer, I want to create a move request by specifying pickup and delivery addresses, date, time, and services so that I can book movers.

**DRV-05 - Accept Move Request**
> As a driver, I want to accept a move request so that I can confirm my availability and begin the job.

**ADM-01 - View Platform Dashboard**
> As an admin, I want to see an overview of active users, pending move requests, and revenue so that I can monitor platform health.

---

## What This Repo Actually Is

This is not the full product. It is a backend prototype built to answer a few questions before committing to the full build:

1. Can the matching engine find the nearest available truck of the right type in under a second?
2. Does the Redis + Postgres + Kafka combination hold up at scale?
3. Can we generate enough realistic data to train a pricing model before the app goes live?
4. What does the data pipeline look like when it grows to 180,000+ records?

The simulator runs five times a day and generates 500 move requests across ten Canadian cities. By the time the mobile apps are ready, there will already be over 180,000 historical assignments to work with.

### What is not built yet

| Feature | Notes |
|---|---|
| Authentication and authorisation | JWT + OAuth2, driver identity verification |
| Customer mobile app | React Native, based on Figma designs |
| Driver mobile app | React Native, real-time job notifications |
| Mover mobile app | React Native |
| Admin web dashboard | Next.js |
| Real-time driver tracking | WebSocket, location updates every 30 seconds |
| Payment processing | Stripe |
| Push notifications | Firebase Cloud Messaging |
| Move scheduling | Date and time booking, not just on-demand |
| In-app chat | Customer to driver messaging |
| Driver ratings | Post-move review system |

---

## Full Platform Architecture

```
+-------------------------------------------------------------+
|                   MOBILE / WEB APP                   (soon) |
|             Customer + Driver + Mover Apps                  |
|        Book moves, track driver, manage earnings            |
|        Admin Dashboard, reports, user management            |
+---------------------------+---------------------------------+
                            |
+---------------------------v---------------------------------+
|                   FASTAPI LAYER                     (done)  |
|  /move/request   /move/complete   /predict/price            |
|  /driver/register   /truck/register   /auth/login           |
|             Request validation, Kafka publishing            |
+----------+---------------------------------+----------------+
           |                                |
+----------v----------+        +-----------v--------------+
|       KAFKA  (done) |        |    ML MODEL        (soon)|
|  producer           |        |  Move pricing            |
|  consumer           |        |  ETA prediction          |
|  truck.move.        |        |  Trained on 182,500      |
|  requested          |        |  historical assignments  |
+----------+----------+        +--------------------------+
           |
+----------v--------------------------------------------------+
|                 OPERATIONAL LAYER                   (done)  |
|                                                             |
|  Redis (Geo + Status)         Postgres (Source of Truth)    |
|  - GEOSEARCH proximity        - customers                   |
|  - truck availability         - drivers                     |
|  - 3-field hash per truck     - trucks                      |
|    status, driver_id, type    - move_assignments            |
+---------------------------+---------------------------------+
                            |
+---------------------------v---------------------------------+
|              DATA ENGINEERING LAYER                 (soon)  |
|                                                             |
|  Airflow  ->  dbt  ->  BigQuery  ->  Metabase               |
|                                                             |
|  dbt models:                                                |
|  - staging:   stg_assignments, stg_customers                |
|  - marts:     fact_assignments, dim_trucks                  |
|  - analytics: demand_by_zone, driver_performance            |
|                                                             |
|  Dashboard:                                                 |
|  - Demand heatmap by city and zone                          |
|  - Peak hours breakdown                                     |
|  - Driver performance KPIs                                  |
+---------------------------+---------------------------------+
                            |
+---------------------------v---------------------------------+
|                  AGENTIC LAYER                      (soon)  |
|                                                             |
|  Dispatch Agent                                             |
|  - Handles edge cases the rule engine cannot               |
|  - Tools: search_trucks, assign_truck, notify               |
|                                                             |
|  Customer Support Agent                                     |
|  - "Where is my driver?" queries live Postgres              |
|  - "Change my dropoff" updates the assignment               |
|  - "I need a bigger truck" reruns the matching engine       |
|                                                             |
|  Route Optimisation Agent                                   |
|  - Groups nearby pickups for a single driver                |
|                                                             |
|  Built with: Claude API, LangGraph, Anthropic Tool Use      |
+-------------------------------------------------------------+
```

---

## Build Stages

| Stage | What it covers | Status |
|---|---|---|
| Stage 1 | Software Engineering - API, Kafka, Redis, Postgres, Simulator | Done |
| Stage 2 | Data Engineering - BigQuery, dbt, Airflow, Dashboard | In progress |
| Stage 3 | Deployment - Railway, Upstash, CI/CD | Planned |
| Stage 4 | ML Engineering - Pricing model, ETA prediction | Planned |
| Stage 5 | Agentic AI - Dispatch agent, Support agent, LangGraph | Planned |
| Stage 6 | Full Product - Mobile apps, auth, payments, notifications | Planned |

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| API | FastAPI | Fast to build, great for async, auto docs via Swagger |
| Messaging | Apache Kafka | Decouples the API from the matching engine |
| Cache and Geo | Redis | GEOSEARCH makes proximity matching fast and simple |
| Database | PostgreSQL 15 | Solid relational store for everything that matters long term |
| Validation | Pydantic v2 | Clean request models with type safety |
| Containers | Docker Compose | Runs the whole local stack in one command |
| Data gen | Python + Faker | Realistic Canadian names, phones, emails |
| DB GUI | pgAdmin | Inspect data without writing SQL every time |
| Planned | Airflow | Schedule and monitor the data pipeline |
| Planned | dbt | Transform raw events into analytics-ready models |
| Planned | BigQuery | Separate OLAP store for analytics queries |
| Planned | Metabase | Business dashboards without writing SQL |
| Planned | scikit-learn | Pricing and ETA prediction |
| Planned | Claude API + LangGraph | Agentic dispatch and customer support |
| Planned | React Native | Customer and driver mobile apps |
| Planned | Next.js | Admin web dashboard |
| Planned | Stripe | Payment processing |
| Planned | Firebase | Push notifications |

---

## Project Structure

```
TruckIT-engineering/
├── app/
│   ├── main.py                  # FastAPI app, routes registered here
│   ├── api/
│   │   ├── moves.py             # POST /truck/move/request
│   │   └── auth.py              # Auth endpoints (coming soon)
│   ├── core/
│   │   └── kafka.py             # Kafka config
│   ├── models/
│   │   └── move.py              # MoveRequest model with validation
│   ├── services/
│   │   ├── producer.py          # Publishes move requests to Kafka
│   │   ├── consumer.py          # Reads from Kafka, matches trucks
│   │   └── simulator.py         # Runs daily to generate test data
│   └── seed_canada.py           # One-time setup: trucks and drivers
├── docker/
│   └── docker-compose.yml       # Kafka, Zookeeper, Redis, Postgres
├── requirements.txt
└── README.md
```

---

## Data Model

### customers
Created daily by the simulator. In production these come from app signups.
```
customer_id   VARCHAR(50) PK
name          VARCHAR(100)
email         VARCHAR(100)
phone         VARCHAR(20)
city          VARCHAR(50)
created_at    TIMESTAMP
```

### drivers
Seeded once. In production these come from driver registrations.
```
driver_id     VARCHAR(50) PK
name          VARCHAR(100)
email         VARCHAR(100)
phone         VARCHAR(20)
city          VARCHAR(50)
license_no    VARCHAR(20)
created_at    TIMESTAMP
```

### trucks
Seeded once and linked to a driver.
```
truck_id      VARCHAR(50) PK
driver_id     VARCHAR(50) FK to drivers
type          VARCHAR(50)
description   VARCHAR(200)
plate         VARCHAR(20)
city          VARCHAR(50)
zone          VARCHAR(50)
capacity_kg   INTEGER
created_at    TIMESTAMP
```

### move_assignments
Written by the consumer every time a truck is matched to a request.
```
id                    SERIAL PK
customer_id           VARCHAR(50)
pickup_lat            FLOAT
pickup_lng            FLOAT
dropoff_lat           FLOAT
dropoff_lng           FLOAT
assigned_truck        VARCHAR(50)
driver_id             VARCHAR(50)
driver                VARCHAR(100)
truck_type            VARCHAR(50)
service_type          VARCHAR(50)     packing, loading, or full_move
driver_to_pickup_km   FLOAT           haversine: driver location to pickup
pickup_to_dropoff_km  FLOAT           haversine: pickup to dropoff
status                VARCHAR(20)     PENDING, ASSIGNED, or COMPLETED
created_at            TIMESTAMP
```

### Redis

```
trucks               Geo sorted set with 10,000 truck positions
                     Used by GEOSEARCH for proximity matching

truck:{city}-{id}    Hash with exactly 3 fields
                     status    - available or busy
                     driver_id - links back to Postgres
                     type      - used to filter by truck type in geosearch
```

Redis only stores what the matching engine needs at runtime. Everything else stays in Postgres and gets pulled via a JOIN after a match is found. This keeps Redis lean at scale.

### Truck Types

| Type | Best for | Capacity |
|---|---|---|
| cargo_van | Studio or 1-bedroom apartment | 500kg |
| small_truck | 1 to 2 bedroom apartment | 1,500kg |
| medium_truck | 2 to 3 bedroom house | 3,500kg |
| large_truck | 4+ bedroom house or office | 7,000kg |
| specialty_truck | Piano, fragile items, climate-controlled | 2,000kg |

---

## Getting Started

You need Docker, Docker Compose, and Python 3.10 or above.

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/TruckIT-engineering.git
cd TruckIT-engineering
```

### 2. Start the infrastructure

```bash
cd docker && docker-compose up -d
```

This brings up Kafka and Zookeeper on port 9092, Redis on 6379, and Postgres on 5433.

### 3. Install Python dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Seed the database

```bash
python app/seed_canada.py
```

You should see 10,000 trucks and 10,000 drivers seeded across 10 cities, with Redis and Postgres in sync.

### 5. Create the Kafka topic

```bash
docker exec -it kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --create --topic truck.move.requested \
  --partitions 1 --replication-factor 1
```

### 6. Start the consumer in Terminal 1

```bash
python app/services/consumer.py
```

### 7. Start the API in Terminal 2

```bash
uvicorn app.main:app --reload --port 9010
```

### 8. Open Swagger UI

```
http://localhost:9010/docs
```

---

## Sending a Move Request

Use the Swagger UI or send a POST to `/truck/move/request`:

```json
{
  "customer_id": "cust:20260418-1",
  "pickup_lat": 51.0447,
  "pickup_lng": -114.0719,
  "dropoff_lat": 51.05,
  "dropoff_lng": -114.08,
  "truck_type": "medium_truck",
  "service_type": "full_move"
}
```

Truck types: `cargo_van`, `small_truck`, `medium_truck`, `large_truck`, `specialty_truck`

Service types: `packing`, `loading`, `full_move`

The consumer will log something like:

```
Request | Customer: cust:20260418-1 | Type: medium_truck | Service: full_move
Assigned: truck:calgary-948
Driver: Bradley Scott (driver:calgary-948)
Truck: medium_truck - 2 to 3 bedroom house moves
Capacity: 3500kg
Distance: Driver to Pickup 2.81km | Pickup to Dropoff 14.91km
Saved to Postgres - status: ASSIGNED
```

---

## Simulator

The simulator creates fresh customers and fires move requests against the API. It runs five times a day in production via cron.

```bash
python app/services/simulator.py
```

Each run resets all 10,000 trucks to available, creates 100 new customers in Postgres, and sends 100 requests spread across all ten cities.

**Production schedule:**
```
0  8 * * *   8am   morning rush
0 11 * * *   11am  late morning
0 14 * * *   2pm   afternoon
0 17 * * *   5pm   evening rush
0 20 * * *   8pm   night
```

500 requests and 500 new customers every day. By end of year that is 182,500 assignments in Postgres ready for analytics and model training.

---

## Seeded Data

| What | Count | Details |
|---|---|---|
| Cities | 10 | Calgary, Edmonton, Vancouver, Toronto, Montreal, Ottawa, Winnipeg, Halifax, Saskatoon, Regina |
| Trucks | 10,000 | 1,000 per city, 5 types, spread across 8 zones |
| Drivers | 10,000 | One per truck, same city |

Zones: downtown, airport, suburbs, industrial, university, hospital, shopping mall, random

---

## Environment Variables

```bash
API_BASE_URL=http://localhost:9010
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=truck.move.requested
REDIS_HOST=localhost
REDIS_PORT=6379
DB_HOST=localhost
DB_PORT=5433
DB_NAME=truckit
DB_USER=truckit
DB_PASSWORD=truckit123
DAILY_REQUESTS=100
REQUEST_DELAY_SECONDS=1.5
```

---

## pgAdmin

```
Host:     localhost
Port:     5433
Database: truckit
Username: truckit
Password: truckit123
```

---

## Why I Built It This Way

Most portfolio projects are either a clean backend with no real data, or a data pipeline with no real application behind it. I wanted to build something that covers the full stack from product idea to agentic AI.

The engineering layers build on each other intentionally. The simulator generates data that trains the ML models. The ML models feed into the agentic layer. The agentic layer eventually powers the mobile apps. Nothing here is throwaway work.

| Discipline | What this project shows |
|---|---|
| Product Design | Original concept, Figma prototype, 38 user stories across 4 modules |
| Software Engineering | Production API, event streaming, real-time geo matching, containerisation |
| Data Engineering | Pipeline design, dbt modelling, warehouse architecture, orchestration |
| ML Engineering | Feature engineering on real event data, model training, serving predictions |
| Agentic AI | Tool use, multi-agent orchestration, LLM decisions on live operational data |

---

## Author

**Ayo Ogunbanwo**

Product concept, design, and engineering.

Figma Prototype: [View Design](https://www.figma.com/proto/75QBEKsdixUlP1dGb7OOF2/TruckIT?node-id=232-43&t=2saNmEXCNyX159Zg-1&hide-ui=1)

Product requirements document available on request.

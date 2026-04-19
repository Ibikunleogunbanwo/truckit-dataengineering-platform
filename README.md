# TruckIT — Moving Services Platform

> **This is my original product idea.**
>
> TruckIT is a moving services platform I conceptualised and designed — connecting customers with truck drivers and movers for residential and commercial moves across Canada. This engineering repository is a **backend prototype and data simulation layer** built to validate the core matching logic, data architecture, and streaming pipeline before the full product is built.
>
> The full product — including mobile apps for customers, drivers, and movers, plus an admin web dashboard — has been fully designed in Figma and specified in a product requirements document.

---

## Product Vision

TruckIT makes booking a move as simple as booking a ride. Customers specify what they need to move, when, and where — the platform finds the nearest available truck and driver, provides real-time tracking, and handles payment. Drivers get a steady stream of jobs with transparent earnings. Movers can opt in for additional loading and packing work.

### Figma Prototype

The full UI/UX has been designed across four modules — Customer, Driver, Mover, and Admin.

👉 **[View the TruckIT Figma Prototype](https://www.figma.com/proto/75QBEKsdixUlP1dGb7OOF2/TruckIT?node-id=232-43&t=2saNmEXCNyX159Zg-1&hide-ui=1)**

---

## Product Modules

Based on the product requirements document, TruckIT covers four user-facing modules:

| Module | Platform | Stories | Key Capabilities |
|---|---|---|---|
| **Customer** | Mobile App | 11 stories | Book moves · Track driver · Payment · Move history |
| **Driver** | Mobile App | 11 stories | Accept jobs · Navigation · Earnings · Availability |
| **Mover** | Mobile App | 10 stories | Browse jobs · Accept packing/loading work · Earnings |
| **Admin** | Web Dashboard | 6 stories | Manage users · Assign jobs · Reports · Platform settings |

### Selected User Stories

**Customer (CUS-05) — Create Move Request**
> As a customer, I want to create a move request by specifying pickup/delivery addresses, date, time, and services so that I can book movers.

**Driver (DRV-05) — Accept Move Request**
> As a driver, I want to accept a move request so that I can confirm my availability and begin the job.

**Driver (DRV-07) — Navigate to Location**
> As a driver, I want integrated navigation to pickup and delivery locations so that I can reach destinations efficiently.

**Admin (ADM-01) — View Platform Dashboard**
> As an admin, I want to see an overview of active users, pending move requests, and revenue so that I can monitor platform health.

---

## What This Repository Is

This repository is the **backend engineering prototype** — built to:

1. **Validate the core matching algorithm** — can we find the nearest available truck of the right type within seconds?
2. **Prove the data architecture** — does the Redis + Postgres + Kafka combination handle real-time dispatch efficiently at scale?
3. **Simulate realistic data** — generate 182,500 move assignments per year to train future ML pricing and ETA models
4. **Build the data engineering foundation** — create the pipeline infrastructure (BigQuery + dbt + Airflow) before the app is live

### What this prototype does NOT include yet

| Feature | Status | Notes |
|---|---|---|
| Authentication / Authorization | 🔜 Planned | JWT + OAuth2, driver identity verification |
| Customer mobile app | 🔜 Planned | React Native, matches Figma designs |
| Driver mobile app | 🔜 Planned | React Native, real-time job notifications |
| Mover mobile app | 🔜 Planned | React Native |
| Admin web dashboard | 🔜 Planned | Next.js, analytics and platform management |
| Real-time driver tracking | 🔜 Planned | WebSocket, location updates every 30s |
| Payment processing | 🔜 Planned | Stripe integration |
| Push notifications | 🔜 Planned | Firebase Cloud Messaging |
| Move scheduling | 🔜 Planned | Date/time booking, not just on-demand |
| In-app chat | 🔜 Planned | Customer ↔ driver messaging |
| Driver ratings | 🔜 Planned | Post-move review system |

---

## Full Platform Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MOBILE / WEB APP                   🔜    │
│              Customer + Driver + Mover Apps                  │
│         Book moves · Track driver · Manage earnings         │
│         Admin Dashboard · Reports · User management         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    FASTAPI LAYER                      ✅    │
│   /move/request    /move/complete    /predict/price          │
│   /driver/register  /truck/register  /auth/login            │
│              Request validation · Kafka publishing           │
└──────────┬────────────────────────────┬─────────────────────┘
           │                            │
┌──────────▼──────────┐      ┌──────────▼──────────────┐
│      KAFKA          │  ✅  │     ML MODEL        🔜  │
│  producer           │      │  Move pricing            │
│  consumer           │      │  ETA prediction          │
│  truck.move.        │      │  Trained on 182,500      │
│  requested          │      │  historical assignments  │
└──────────┬──────────┘      └──────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────┐
│                  OPERATIONAL LAYER                    ✅    │
│                                                             │
│   Redis (Geo + Status)          Postgres (Source of Truth)  │
│   ├── GEOSEARCH proximity       ├── customers               │
│   ├── truck availability        ├── drivers                 │
│   └── 3-field hash per truck    ├── trucks                  │
│       status|driver_id|type     └── move_assignments        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│               DATA ENGINEERING LAYER                  🔜    │
│                                                             │
│   Airflow  →  dbt  →  BigQuery  →  Metabase                 │
│                                                             │
│   dbt models:                                               │
│   ├── staging/   stg_assignments · stg_customers            │
│   ├── marts/     fact_assignments · dim_trucks              │
│   └── analytics/ demand_by_zone · driver_performance        │
│                                                             │
│   Dashboard metrics:                                        │
│   ├── Demand heatmap by city + zone                         │
│   ├── Peak hours analysis                                   │
│   └── Driver performance KPIs                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   AGENTIC LAYER                       🔜    │
│                                                             │
│   Dispatch Agent                                            │
│   ├── Handles edge cases the rule engine can't              │
│   └── Tools: search_trucks · assign_truck · notify          │
│                                                             │
│   Customer Support Agent                                    │
│   ├── "Where is my driver?" → queries live Postgres         │
│   ├── "Change my dropoff"   → updates assignment            │
│   └── "I need bigger truck" → reruns matching               │
│                                                             │
│   Route Optimisation Agent                                  │
│   └── Batches nearby pickups for single driver              │
│                                                             │
│   Powered by: Claude API · LangGraph · Anthropic Tool Use   │
└─────────────────────────────────────────────────────────────┘
```

---

## Build Stages

| Stage | Focus | Status |
|---|---|---|
| **Stage 1** | Software Engineering — API, Kafka, Redis, Postgres, Simulator | ✅ Complete |
| **Stage 2** | Data Engineering — BigQuery, dbt, Airflow, Dashboard | 🔜 In progress |
| **Stage 3** | Deployment — Railway, Upstash, CI/CD | 🔜 Planned |
| **Stage 4** | ML Engineering — Pricing model, ETA prediction | 🔜 Planned |
| **Stage 5** | Agentic AI — Dispatch agent, Support agent, LangGraph | 🔜 Planned |
| **Stage 6** | Full Product — Mobile apps, Auth, Payments, Notifications | 🔜 Planned |

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| API | FastAPI | REST endpoints, request validation |
| Messaging | Apache Kafka | Event streaming for move requests |
| Cache / Geo | Redis | Real-time truck availability + geo proximity search |
| Database | PostgreSQL 15 | Source of truth for all entities |
| Serialisation | Pydantic v2 | Request/response models with validation |
| Containerisation | Docker Compose | Local dev environment |
| Simulation | Python + Faker | Realistic daily data generation |
| DB Admin | pgAdmin | Postgres GUI |
| **Planned** | Airflow | Pipeline orchestration |
| **Planned** | dbt | Data transformation + modelling |
| **Planned** | BigQuery | Analytics warehouse |
| **Planned** | Metabase | Business intelligence dashboard |
| **Planned** | scikit-learn | Pricing + ETA ML models |
| **Planned** | Claude API + LangGraph | Agentic dispatch + support |
| **Planned** | React Native | Customer + Driver mobile apps |
| **Planned** | Next.js | Admin web dashboard |
| **Planned** | Stripe | Payment processing |
| **Planned** | Firebase | Push notifications |

---

## Project Structure

```
TruckIT-engineering/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── api/
│   │   ├── moves.py             # POST /truck/move/request
│   │   └── auth.py              # Authentication (coming soon)
│   ├── core/
│   │   └── kafka.py             # Kafka configuration
│   ├── models/
│   │   └── move.py              # MoveRequest Pydantic model
│   ├── services/
│   │   ├── producer.py          # Kafka producer
│   │   ├── consumer.py          # Truck matching engine
│   │   └── simulator.py         # Daily request simulator
│   └── seed_canada.py           # One-time seed script
├── docker/
│   └── docker-compose.yml       # Kafka, Zookeeper, Redis, Postgres
├── requirements.txt
└── README.md
```

---

## Data Model

### Postgres Tables

**customers** — created daily by the simulator
```
customer_id   VARCHAR(50) PK
name          VARCHAR(100)
email         VARCHAR(100)
phone         VARCHAR(20)
city          VARCHAR(50)
created_at    TIMESTAMP
```

**drivers** — seeded once via seed_canada.py
```
driver_id     VARCHAR(50) PK
name          VARCHAR(100)
email         VARCHAR(100)
phone         VARCHAR(20)
city          VARCHAR(50)
license_no    VARCHAR(20)
created_at    TIMESTAMP
```

**trucks** — seeded once via seed_canada.py
```
truck_id      VARCHAR(50) PK
driver_id     VARCHAR(50) FK → drivers
type          VARCHAR(50)
description   VARCHAR(200)
plate         VARCHAR(20)
city          VARCHAR(50)
zone          VARCHAR(50)
capacity_kg   INTEGER
created_at    TIMESTAMP
```

**move_assignments** — written by consumer on every matched request
```
id                    SERIAL PK
customer_id           VARCHAR(50)
pickup_lat/lng        FLOAT
dropoff_lat/lng       FLOAT
assigned_truck        VARCHAR(50)
driver_id             VARCHAR(50)
driver                VARCHAR(100)
truck_type            VARCHAR(50)
service_type          VARCHAR(50)   packing | loading | full_move
driver_to_pickup_km   FLOAT
pickup_to_dropoff_km  FLOAT
status                VARCHAR(20)   PENDING | ASSIGNED | COMPLETED
created_at            TIMESTAMP
```

### Redis Schema

```
trucks              Geo sorted set — 10,000 truck locations for proximity search

truck:{city}-{id}   Hash — 3 fields only (intentionally lightweight)
                    status    → available | busy
                    driver_id → FK to Postgres
                    type      → for geosearch type filtering
```

### Truck Types

| Type | Use Case | Capacity |
|---|---|---|
| `cargo_van` | Studio / 1-bed apartment | 500kg |
| `small_truck` | 1-2 bed apartment | 1,500kg |
| `medium_truck` | 2-3 bed house | 3,500kg |
| `large_truck` | 4+ bed house / office | 7,000kg |
| `specialty_truck` | Piano, fragile, climate-controlled | 2,000kg |

---

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Python 3.10+

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/TruckIT-engineering.git
cd TruckIT-engineering
```

### 2. Start infrastructure

```bash
cd docker && docker-compose up -d
```

### 3. Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Seed the database

```bash
python app/seed_canada.py
```

### 5. Create the Kafka topic

```bash
docker exec -it kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --create --topic truck.move.requested \
  --partitions 1 --replication-factor 1
```

### 6. Start the consumer (Terminal 1)

```bash
python app/services/consumer.py
```

### 7. Start the API (Terminal 2)

```bash
uvicorn app.main:app --reload --port 9010
```

### 8. Open Swagger

```
http://localhost:9010/docs
```

---

## API Endpoints

### POST `/truck/move/request`

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

Valid `truck_type`: `cargo_van` · `small_truck` · `medium_truck` · `large_truck` · `specialty_truck`

Valid `service_type`: `packing` · `loading` · `full_move`

---

## Simulator

Generates 500 realistic daily requests across 10 Canadian cities.

```bash
python app/services/simulator.py
```

**Production cron schedule (5× daily):**
```
0  8 * * *   →  8am  morning rush
0 11 * * *   → 11am  late morning
0 14 * * *   →  2pm  afternoon
0 17 * * *   →  5pm  evening rush
0 20 * * *   →  8pm  night
```

**Annual output:** 182,500 assignments · 182,500 customers

---

## Seeded Data

| Entity | Count | Distribution |
|---|---|---|
| Cities | 10 | Calgary · Edmonton · Vancouver · Toronto · Montreal · Ottawa · Winnipeg · Halifax · Saskatoon · Regina |
| Trucks | 10,000 | 1,000/city · 5 types · 8 zones |
| Drivers | 10,000 | One per truck · same city |

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

## Why This Project

TruckIT is both a **product I designed** and a **technical portfolio** covering four engineering disciplines:

| Discipline | What it demonstrates |
|---|---|
| **Product Design** | Original concept · Figma prototype · 38 user stories across 4 modules |
| **Software Engineering** | Production API · event streaming · real-time geo matching · containerisation |
| **Data Engineering** | Pipeline design · dbt modelling · warehouse architecture · orchestration |
| **ML Engineering** | Feature engineering on real event data · model training · prediction serving |
| **Agentic AI** | Tool use · multi-agent orchestration · LLM decisions on live operational data |

---

## Author

**Ayo Ogunbanwo**
Original product concept, design, and engineering.

- Figma Prototype: [View Design](https://www.figma.com/proto/75QBEKsdixUlP1dGb7OOF2/TruckIT?node-id=232-43&t=2saNmEXCNyX159Zg-1&hide-ui=1)
- Product Requirements: Available on request

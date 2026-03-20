# Travel Planner API

Backend API for trip and travel-planning management built with **FastAPI** using a Domain-Driven Design (DDD) approach.

## Feature Summary

- Trip CRUD operations
- Bulk trip creation (main trip + images + pickup points + includes + daily rundown)
- Participant slot management (reserve/release/sync)
- Location, trip day, activity, expense, and trip statistics management
- Domain rule validation (budget limit, date range checks, activity conflict checks)
- SQLModel database persistence (SQLite/PostgreSQL)
- CI pipeline via GitHub Actions

## Current Component Architecture

### API Layer

- main.py: FastAPI app bootstrap, main router registration, and database init via lifespan
- router/router.py: main endpoints under /api/perencanaan
- router/auth_router.py: /token login endpoint exists in the codebase, but is not currently registered in main.py

### Domain Layer

- models/aggregate_root.py: RencanaPerjalanan aggregate root
- models/entity.py: Lokasi, HariPerjalanan, Aktivitas, Pengeluaran, TripImage, TripPickupPoint, TripInclude entities
- models/exception.py: domain exceptions for business invariants
- models/value_objects.py: supporting value objects

### Application/Infrastructure

- schema.py: endpoint request schemas (Pydantic)
- database.py: SQLModel engine, session dependency, and DB schema compatibility validation (non-SQLite)
- security/security.py: stateless bearer JWT validation (user_id, email, role claims)

## Domain Rules (Invariants)

1. Total expenses cannot exceed trip price/budget.
2. Trip days and expense dates must stay within the trip duration range.
3. Activities in the same day must not overlap.
4. Duration updates must still cover existing trip days and expenses.

## Prerequisites

- Python >= 3.13
- uv package manager

## Local Setup

1. Clone repository

```bash
git clone <repository-url>
cd travel_planner
```

2. Install runtime dependencies

```bash
uv sync
```

3. Install dev/test dependencies

```bash
uv sync --extra dev
```

4. Create a .env file

```bash
copy .env.example .env
```

Or define it manually:

```env
SECRET_KEY=your-secret-key-at-least-32-characters
DATABASE_URL=sqlite:///./local_travel.db
```

Optional: generate SECRET_KEY:

```bash
uv run security/generate_key.py
```

## Run the Application

```bash
uv run main.py
```

Server runs at:

- http://127.0.0.1:8005
- Swagger: http://127.0.0.1:8005/docs
- ReDoc: http://127.0.0.1:8005/redoc

Notes:

- If you run uvicorn directly without --port, the default uvicorn port is 8000.
- The main() entry point in main.py runs the app on port 8005.

## JWT Authentication (Current State)

- Many endpoints in the main router are protected with the get_current_user dependency.
- The token must be a valid Bearer JWT with at least the user_id claim.
- The /api/auth/token login endpoint exists in router/auth_router.py, but is not currently registered in main.py.

Authentication header:

```http
Authorization: Bearer <jwt_token>
```

## API Endpoint Summary

Main prefix: /api/perencanaan

### Locations

| Method | Endpoint            | Auth | Description     |
| ------ | ------------------- | ---- | --------------- |
| POST   | /lokasi/            | Yes  | Create location |
| GET    | /lokasi/            | Yes  | List locations  |
| GET    | /lokasi/{lokasi_id} | Yes  | Location detail |

### Travel Plan / Trip

| Method | Endpoint               | Auth | Description                           |
| ------ | ---------------------- | ---- | ------------------------------------- |
| POST   | /                      | Yes  | Create travel plan                    |
| POST   | /bulk-create           | Yes  | Create full trip (atomic transaction) |
| GET    | /                      | Yes  | List current user's plans             |
| GET    | /all                   | No   | List all plans                        |
| GET    | /{rencana_id}          | Yes  | Plan detail (ownership check)         |
| GET    | /trips/latest          | Yes  | Current user's latest trip            |
| GET    | /trips/all             | No   | Trip list for frontend usage          |
| GET    | /trips/{trip_id}       | No   | Normalized trip detail                |
| PUT    | /{rencana_id}/anggaran | Yes  | Update budget                         |
| PUT    | /{rencana_id}/durasi   | Yes  | Update duration                       |
| PUT    | /trips/{trip_id}       | No   | Update trip (frontend format)         |

### Trip Slots

| Method | Endpoint                       | Auth | Description                                  |
| ------ | ------------------------------ | ---- | -------------------------------------------- |
| POST   | /trips/{trip_id}/reserve-slots | No   | Decrease slot_tersedia if enough slots exist |
| POST   | /trips/{trip_id}/release-slots | No   | Increase slot_tersedia (up to slot max)      |
| POST   | /trips/{trip_id}/sync-slots    | No   | Sync slot_tersedia from participant_count    |

### Trip Images

| Method | Endpoint                        | Auth | Description  |
| ------ | ------------------------------- | ---- | ------------ |
| POST   | /{rencana_id}/images            | Yes  | Add image    |
| GET    | /{rencana_id}/images            | Yes  | List images  |
| DELETE | /{rencana_id}/images/{image_id} | Yes  | Delete image |

### Trip Pickup Points

| Method | Endpoint                                | Auth | Description                   |
| ------ | --------------------------------------- | ---- | ----------------------------- |
| POST   | /{rencana_id}/pickup-points             | Yes  | Add pickup point              |
| GET    | /trip-pickup-points?plan_id=...         | No   | List pickup points by plan_id |
| GET    | /pickup_points?trip_id=...              | No   | List pickup points by trip_id |
| GET    | /{rencana_id}/pickup-points             | Yes  | List pickup points for a plan |
| DELETE | /{rencana_id}/pickup-points/{pickup_id} | Yes  | Delete pickup point           |

### Trip Includes

| Method | Endpoint                            | Auth | Description         |
| ------ | ----------------------------------- | ---- | ------------------- |
| POST   | /{rencana_id}/includes              | Yes  | Add include item    |
| GET    | /{rencana_id}/includes              | Yes  | List include items  |
| DELETE | /{rencana_id}/includes/{include_id} | Yes  | Delete include item |

### Days, Activities, Expenses, Statistics

| Method | Endpoint                                   | Auth | Description     |
| ------ | ------------------------------------------ | ---- | --------------- |
| POST   | /{rencana_id}/hari                         | Yes  | Add trip day    |
| DELETE | /{rencana_id}/hari/{tanggal}               | Yes  | Delete trip day |
| POST   | /{rencana_id}/hari/{tanggal}/aktivitas     | Yes  | Add activity    |
| GET    | /{rencana_id}/hari/{tanggal}/aktivitas     | Yes  | List activities |
| POST   | /{rencana_id}/pengeluaran                  | Yes  | Add expense     |
| DELETE | /{rencana_id}/pengeluaran/{id_pengeluaran} | Yes  | Delete expense  |
| GET    | /{rencana_id}/statistik                    | Yes  | Trip statistics |

## Important Payload Examples

### Create travel plan

```json
{
  "nama": "Liburan Bali 5D4N",
  "deskripsi": "Trip keluarga",
  "durasi": {
    "tanggalMulai": "2026-04-01",
    "tanggalSelesai": "2026-04-05"
  },
  "anggaran": {
    "jumlah": 3500000,
    "mata_uang": "IDR"
  },
  "slot": 20,
  "provinsi": "Bali",
  "negara": "Indonesia",
  "destination_type": "Beach",
  "jumlah_hari": 5,
  "jumlah_malam": 4
}
```

### Reserve slot

```json
{
  "participant_count": 2
}
```

### Add daily activity

```json
{
  "waktu_mulai": "08:00:00",
  "duration": 2,
  "deskripsi": "Snorkeling",
  "id_lokasi": "4df5a657-2db9-4f3b-9f9f-bfd81c4788e1"
}
```

## Testing

Run all tests:

```bash
uv run pytest
```

Coverage report:

```bash
uv run pytest --cov=. --cov-report=html
```

Verbose:

```bash
uv run pytest -v
```

## Project Structure

```text
travel_planner/
├── .github/workflows/main.yml
├── models/
│   ├── aggregate_root.py
│   ├── entity.py
│   ├── exception.py
│   └── value_objects.py
├── router/
│   ├── router.py
│   └── auth_router.py
├── security/
│   ├── security.py
│   ├── generate_key.py
│   └── hash.py
├── tests/
├── database.py
├── main.py
├── schema.py
├── pyproject.toml
└── README.md
```

## Continuous Integration

GitHub Actions workflow is defined in `.github/workflows/main.yml`

# Smart Travel Backend — Functionality & Concepts Summary

A FastAPI + PostgreSQL + SQLModel backend for a Nepal-focused travel app. It provides
the full data layer, a hybrid recommendation engine, budget & route optimizers, an
LLM chat agent with live-database tools, live weather, flight how-to-reach info and
offline map data. It is **informational only** — it guides users on how to book, but
never performs bookings or payments.

---

## 1. Tech Stack

| Concern      | Technology                                          |
|--------------|-----------------------------------------------------|
| Framework    | FastAPI + Uvicorn                                   |
| Language     | Python 3.13+                                        |
| ORM          | SQLModel (SQLAlchemy + Pydantic)                    |
| Database     | PostgreSQL, Alembic migrations                      |
| Auth         | JWT (HS256), bcrypt password hashing, slowapi rate limiting |
| Recommender  | scikit-learn (TF-IDF / cosine)                      |
| Live weather | Open-Meteo API (free, no key) via httpx             |
| LLM chat     | Local Ollama (qwen3:8b), OpenAI-compatible          |
| Package mgr  | uv                                                 |

---

## 2. Project Layout

```
app/
  core/            # config, DB engine, security, rate-limit, logging
  models/          # SQLModel ORM tables
  schemas/         # Pydantic request/response models
  services/        # business logic (recommendation, optimization, live data, ...)
  chat/            # LLM agent: tool registry, executor, prompts, tools/
  routers/         # FastAPI route handlers
alembic/           # migrations (head: d0edc8b86582)
data/              # seed CSVs — full Nepal catalog (~30 per table)
scripts/           # seed.py (CSV-driven full seed), import_csv.py
tests/             # pytest suite (88 tests)
```

---

## 3. Data Model

- **User** — travelers and admins (role, nationality, phone, hashed password)
- **Destination** — attraction or trek; category, description, best_time (months JSON),
  permit_required, rating, address
- **Address** — province, district, place, latitude, longitude, altitude
- **Attraction** — types (temple/heritage/...), opening hours, visit duration; 1-to-1 with destination
- **EntryFee** — per-category (Nepali/SAARC/Foreign) entry price for attractions
- **TrekkingRoute** — name, difficulty, distance km, recommended days, max altitude
- **RoutePoint** — individual trek stops: sequence, distance/walking-hours from previous,
  overnight flag, linked address/accommodation/food
- **Permit** — TIMS/ACAP etc., per-category price for treks
- **Accommodation** — name, description, location, budget/standard/luxury price (NPR)
- **FoodCost** — name, category, budget/standard/luxury price (NPR)
- **DestinationItinerary** — day-by-day plan (start/end/overnight, walking hours, notes)
- **Itinerary / UserTrip / SavedDestination / Review / Photo / Blog / ActivityLog**
- **Intelligence tables** — `user_preferences`, `user_interactions`, `recommendation_logs`

---

## 4. Capabilities

### 4.1 Content & Users (full CRUD)
JWT auth (register/login/me/change-password, traveler + admin roles, rate-limited),
plus CRUD endpoints for every entity above, photo upload, reviews, blogs, saved
destinations, user trips and an activity log.

### 4.2 Hybrid Recommendation Engine
`app/services/recommendation_service.py` blends 5 independent scorers, each a 0–1
score per destination:

| Component | Algorithm | Location |
|-----------|-----------|----------|
| Content    | TF-IDF vectorization + cosine similarity against user history | `content_based.py` |
| Preference | Rule-based budget/duration/difficulty/season matching | `structured_preferences.py` |
| Context    | Nepal-specific factors: season, monsoon, altitude, reserve days | `contextual.py` |
| Collaborative | User-based: Jaccard similarity over interactions weighted view=1, click=2, save=3, rating=4, itinerary=5, booking=6 | `collaborative.py` |
| Popularity | Weighted implicit signals (save x3, rating x4, itinerary x5, view x1) + review decay | `popularity.py` |

Final blend: `content 0.35 + preference 0.20 + context 0.20 + collaborative 0.15 + popularity 0.10`.

- **Explainable**: each result includes per-component scores and "why this" factors.
- **Cold start**: new users with no data get popularity + context (no collaborative).
- **Signals**: `POST /recommendations/interaction` and `POST /recommendations/preferences`
  feed the models; recommendations are logged for future evaluation.
- Endpoints: `GET /recommendations/`, `GET /recommendations/summary`,
  `POST /recommendations/interaction`, `POST /recommendations/preferences`.

### 4.3 Budget Optimizer
`app/services/budget_optimizer.py` — `POST /optimization/budget`

- Builds a per-tier cost model from real data: accommodation (per room/night),
  food (per person/day across categories), one-time permits + entry fees resolved by
  category (Nepali / SAARC / Foreign).
- **Feasibility check**: the all-budget plan must fit `total_budget`; otherwise returns
  `feasible: False` with the deficit.
- **Algorithm**: greedy bounded-knapsack-style allocation. Starts at all-budget and
  repeatedly applies the *cheapest* single-tier upgrade (any component, any day),
  maximizing comfort per NPR until the surplus runs out.
- Output: per-day plan (tiers + costs), fee breakdown, totals, per-person and
  per-day averages, surplus, `comfort_score`.

### 4.4 Route Optimizer
`app/services/route_optimizer.py` — `POST /optimization/route`

- **Haversine** great-circle distances between waypoints.
- **Algorithm**: nearest-neighbour tour construction tried from every start point, then
  **2-opt local search** refinement (open-path TSP). Deterministic, pure Python.
- Accepts a `route_id`, a `destination_id`, or custom waypoints.
- Output: original vs optimized order, per-stop distance/cumulative, km + % savings,
  total walking hours. (On real ABC data it saved ~27% distance.)

### 4.5 AI Chat Agent
Local Ollama (qwen3:8b) with a tool registry (`app/chat/tool_registry.py`) exposing
**14 live-database tools**:

Destinations, attractions, accommodations-by-price, trek routes + itineraries, food
costs, permits, budget optimizer, route optimizer, live weather, flight info.

The LLM answers questions (costs, weather, routes, "how do I get there") by calling
these tools — it never invents data; unknown data falls back to guidance text.

Robustness features added after live testing:

- **Refreshed tool registry prompt** — the system prompt lists the real 14 tools with
  their exact parameter names plus a best-fit-tool mapping and "tool first" rules.
- **Tool-call nudge** — if the model hedges ("I don't have current data...") on an
  obvious data question, it is nudged once to actually call the right tool.
- **LLM auto-titles** — conversation titles are generated by the LLM (3–6 words);
  thinking-mode preambles are rejected, retried once, and fall back to a clean
  truncation of the first message.
- **Thinking-mode handling** — qwen3's reasoning preambles are disabled via
  `extra_body={"think": False}` and token budgets raised, so replies and XML tool
  calls are never swallowed.

### 4.6 Live Data
`app/services/live_data.py` — **Open-Meteo** (free, no API key):

- `GET /travel/weather/general?latitude&longitude&days`
- `GET /travel/destinations/{id}/weather`
- Chat tool `get_destination_weather` (current conditions + daily forecast with
  WMO weather-code text, humidity, wind, precipitation).
- **Weather-in-recommender** (`config.WEATHER_MODE` = `auto`): the contextual scorer
  multiplies ranks by a real comfort factor (current temperature + 3-day rain
  probability). Cached 30 min with a circuit breaker — offline it falls back to the
  static season score (fully offline-safe) and every explanation gets a
  `"Live weather: 24°C, overcast, 94% rain next 3 days"` note when online.

### 4.7 Flight How-to-Reach (informational)
`app/services/flight_info.py` — curated Nepal dataset, `GET /travel/destinations/{id}/flights`
+ chat tool `get_flight_options`:

- Closest airports (KTM, PKR, Lukla, Lumbini, Chitwan, Janakpur...), airlines,
  indicative duration + fare ranges, booking-portal links, and a readable
  "how to reach" line. Prices explicitly labeled as indicative, not live bookings.

### 4.8 Offline Map Data
`app/services/map_service.py` — `GET /travel/destinations/{id}/map`:

- GeoJSON `FeatureCollection`: trek routes as LineStrings **with elevation profile**,
  waypoint markers (name, sequence, overnight, altitude, linked teahouse/food), and
  the destination point. The frontend renders this offline against bundled tiles.

---

## 5. API Surface (route groups)

| Group | Purpose |
|-------|---------|
| `/auth` | register, login, me, change-password |
| `/destination`, `/attraction`, `/trekking-route`, `/route-point`, `/destination-itinerary`, `/itinerary` | Nepal content CRUD |
| `/accommodation`, `/food-cost`, `/permit`, `/entry-fee` | pricing data CRUD |
| `/blog`, `/review`, `/photo`, `/saved-destination`, `/user-trip`, `/activity-log`, `/user`, `/admin` | community & management |
| `/recommendations` | hybrid recommendations + signals |
| `/optimization` | budget optimizer, route optimizer |
| `/travel` | live weather, flight info, offline map GeoJSON |
| `/chat` | LLM chat session |
| `/health` | liveness |

Interactive docs at `/docs` (Swagger) and `/redoc`.

---

## 6. Current Status

- **Migrations**: all applied, head `d0edc8b86582` (includes sync migration for
  accommodation/food/permit columns + intelligence tables).
- **Seed data** (CSV-driven, `uv run python scripts/seed.py`): loads the whole
  `data/*.csv` catalog — **30 destinations** (14 attractions + 8 treks → 22
  attractions; treks: ABC, Poon Hill, EBC, Langtang, Mardi Himal, Manaslu, Gokyo,
  Annapurna Circuit), 30 accommodations, 30 food costs, 63 route points with real
  coordinates/altitudes, 54 permits, 57 entry fees, 81 per-day destination
  itineraries, 30 blogs — then seeds 4 demo users, 6 user trips (from
  `user_trip.csv`) with itineraries, reviews, photos and saved destinations.
  Pre-existing data bugs (comment rows, dead `dest_mustang_trek` permits, duplicate
  `mcap_manaslu_*`, dangling `food_budget_plus` refs) were cleaned up.
- **Tests**: 88 passing (auth, CRUD, recommendations, optimizers, travel info,
  chat tools, weather-in-recommender, chat titles + tool-call nudge).
- **Verified live**: Open-Meteo returns real current + forecast data; flight resolver
  maps ABC→Pokhara, Pashupatinath→Kathmandu; GeoJSON includes route + elevation;
  recommendation explanations include live weather notes.
- **Deployment**: Dockerfile (python:3.13-slim + uv, non-root), docker-compose
  (Postgres 16 + backend with auto-migrate + health-check), GitHub Actions CI
  (Postgres service + `uv run pytest`).

---

## 7. Roadmap / Remaining Ideas

1. Frontend integration (in progress by the team) — the API surface is ready.
2. (Done) Docker + docker-compose + CI for deployment.
3. (Done) Live weather as a soft recommendation signal with offline fallback.
4. Offline evaluation harness on `recommendation_logs` to prove the hybrid beats baselines.
5. Optional hardening: production secrets management, HTTPS via a reverse proxy,
   replacing the stale `app/services/scoring.py` (dead code, no importers).

---

*This file summarizes the backend as implemented; it is not part of the runtime.*
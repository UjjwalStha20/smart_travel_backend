# Smart Travel App - Backend

A FastAPI-based backend for a Smart Travel application with PostgreSQL, SQLModel ORM, and Alembic migrations.

## Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.14+
- **ORM**: SQLModel (built on SQLAlchemy + Pydantic)
- **Database**: PostgreSQL
- **Migrations**: Alembic
- **Auth**: bcrypt
- **Package Manager**: uv
- **Server**: Uvicorn

## Project Structure

```
backend/
├── app/
│   ├── core/           # Config, DB engine, security
│   ├── models/         # SQLModel ORM models
│   ├── routers/        # FastAPI route handlers
│   ├── schemas/        # Pydantic schemas
│   └── services/       # Business logic layer
├── alembic/            # Database migration scripts
├── migrations/
├── tests/
├── .env                # Environment variables (not committed)
├── .env.example        # Environment variable template
├── pyproject.toml      # Project metadata & dependencies
└── alembic.ini         # Alembic configuration
```

## Prerequisites

- **Python 3.14+**
- **PostgreSQL** running locally or remotely
- **uv** (Python package manager)

Install uv if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd backend
```

### 2. Create and activate a virtual environment

```bash
uv venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
uv sync
```

### 4. Configure environment variables

Copy the example env file and fill in your PostgreSQL credentials:

```bash
cp .env.example .env
```

Edit `.env` with your database details:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smart_travel_db
DB_USER=postgres
DB_PASSWORD=your_password
```

### 5. Create the database

Make sure PostgreSQL is running, then create the database:

```bash
createdb smart_travel_db
```

### 6. Run database migrations

```bash
alembic upgrade head
```

### 7. Start the development server

```bash
uvicorn app.main:app --reload
```

The API will be available at **http://localhost:8000**.

## API Documentation

Once the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Available Commands

| Command | Description |
|---------|-------------|
| `uvicorn app.main:app --reload` | Start dev server |
| `alembic upgrade head` | Apply all migrations |
| `alembic revision --autogenerate -m "message"` | Create a new migration |
| `alembic downgrade -1` | Rollback last migration |

## Models

- User, Destination, Address, Photo, Review
- Attraction, Permit, TrekkingRoute, RoutePoint
- FoodCost, Accommodation

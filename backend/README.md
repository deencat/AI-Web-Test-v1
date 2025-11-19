# AI Web Test - Backend API

FastAPI backend for the AI Web Test application.

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL (or use Docker Compose)
- Redis (or use Docker Compose)

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

### Running Locally

1. Start PostgreSQL and Redis (using Docker Compose):
```bash
docker-compose up -d db redis
```

2. Run the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Access the API:
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc
- API Root: http://localhost:8000/

### Running with Docker Compose

```bash
# Uncomment the backend service in docker-compose.yml first
docker-compose up --build
```

## API Endpoints

### Health Check
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/db` - Health check with database connection test

### Authentication (Day 5)
- `POST /api/v1/auth/login` - Login with username/password
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/register` - Register new user

### Users (Day 5)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependencies (DB session, auth)
│   │   └── v1/
│   │       ├── api.py           # API router aggregator
│   │       └── endpoints/
│   │           ├── auth.py      # Authentication endpoints
│   │           ├── users.py     # User endpoints
│   │           └── health.py    # Health check endpoints
│   ├── core/
│   │   ├── config.py            # Settings/environment
│   │   └── security.py          # JWT utilities
│   ├── crud/
│   │   └── user.py              # User CRUD operations
│   ├── db/
│   │   ├── base.py              # SQLAlchemy base
│   │   ├── session.py           # DB session
│   │   └── init_db.py           # DB initialization
│   ├── models/
│   │   └── user.py              # User model
│   ├── schemas/
│   │   ├── user.py              # User Pydantic schemas
│   │   └── token.py             # Token schemas
│   ├── services/                # Business logic services
│   └── main.py                  # FastAPI app entry point
├── tests/                       # Tests
├── .env                         # Environment variables
├── .env.example                 # Example environment variables
├── Dockerfile                   # Docker configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Development

### Test User (Created on Startup)
- Username: `admin`
- Password: `admin123`
- Email: `admin@aiwebtest.com`
- Role: `admin`

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Testing

```bash
# Run tests (Week 2)
pytest

# Run with coverage
pytest --cov=app tests/
```


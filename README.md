# Splitwise Clone

# I. Description

Expense splitting application built with FastAPI and PostgreSQL.

Software Engineering course project - Harbour Space University.

# II. Dev setup instructions (step-by-step)

```bash
# 1. Setup PostgreSQL (automated)
bash scripts/setup_postgres.sh

# 2. Test database connection
python scripts/test_db_connection.py

# 3. Install and run
pip-sync api/requirements.txt
python -m api.app.main
```

# III. How to run tests

## Test with curl:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"test123"}'
```
## Test with pytest:
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# With coverage + threshold
pytest tests/ --cov=api.app --cov-report=term-missing --cov-fail-under=90
```

### Test Database Connection

```bash
python scripts/test_db_connection.py
```

# IV. How to run code quality ensuring tools

```bash
# Lint
ruff check .

# Format check
ruff format --check .

# Type checks
mypy domains

# Migration drift check (requires DATABASE_URL in environment)
cd api && alembic check
```

# V. How deployment works

# VI. Environmental variables' descriptions

- Required:
  - `DATABASE_URL` - PostgreSQL connection string
  - `JWT_SECRET_KEY` - Secret for JWT tokens (generate with `openssl rand -hex 32`)
- Optional: 
  - See `.env.example` for all available options.

## Features

- JWT authentication
- Group management
- Expense splitting
- Automatic debt calculation
- Settlement optimization

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL + SQLAlchemy (async)
- **Auth:** JWT with bcrypt
- **Testing:** pytest

## Project Structure

```
splitwise-clone/
├── api/
│   ├── app/
│   │   ├── models/       # Database models
│   │   ├── routers/      # API endpoints
│   │   ├── schemas/      # Request/response schemas
│   │   └── main.py       # Application entry
│   ├── requirements.txt
│   └── requirements.in
├── domains/              # Business logic
│   ├── expense/
│   └── group/
├── tests/               # Test suite
└── scripts/             # Setup scripts
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register user (returns JWT)
- `POST /auth/login` - Login (returns JWT)
- `GET /auth/me` - Get current user

### Groups
- `POST /groups` - Create group
- `GET /groups` - List groups
- `POST /groups/{id}/invite` - Invite member

### Expenses
- `POST /expenses` - Create expense
- `GET /expenses` - List expenses

### Debts
- `GET /debts/{group_id}` - Calculate debts
- `GET /debts/{group_id}/settlements` - Get settlement plan

## API Documentation (Swagger)

Once the server is running, interactive API docs are available at:

| UI           | URL                                |
|--------------|------------------------------------|
| Swagger UI   | http://localhost:8000/docs         |
| ReDoc        | http://localhost:8000/redoc        |
| OpenAPI JSON | http://localhost:8000/openapi.json |

Swagger UI lets you browse all endpoints, view request/response schemas, and send test requests directly from the browser.

## Pre-commit Setup & Local Workflow

```bash
# 1) Install dependencies
cd api
pip-sync requirements.txt
cd ..

# 2) Install git hooks
pre-commit install

# 3) Run all hooks on all files (first-time baseline)
pre-commit run --all-files
```

Recommended local workflow before push:

1. Run `pre-commit run --all-files`
2. Fix issues from ruff/mypy/pytest if any
3. Re-run hooks until clean
4. Push and open a pull request

## Documentation

- **[POSTGRES_SETUP.md](POSTGRES_SETUP.md)** - Database setup
- **[API_TESTING_GUIDE.md](API_TESTING_GUIDE.md)** - Manual testing with curl/Postman
- **[.env.example](.env.example)** - Environment variables

## Development

```bash
# Start PostgreSQL
sudo service postgresql start

# Run with auto-reload
cd api
uvicorn app.main:app --reload

# Validate environment
python api/check_env.py

# Test database
python scripts/test_db_connection.py
```

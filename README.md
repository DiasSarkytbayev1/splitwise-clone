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

This project is designed to be deployed on any cloud platform that supports Python applications with PostgreSQL databases (AWS, GCP, Heroku, Railway, etc.).

**Key deployment considerations:**
- Set all required environment variables (see `VI` below)
- Use Alembic migrations in production (`alembic upgrade head`)
- Run the application with a production ASGI server like Gunicorn or Uvicorn
- Configure CORS settings appropriately for your domain
- Enable HTTPS/TLS for API connections

**Typical deployment steps:**
1. Set `DATABASE_URL` and `JWT_SECRET_KEY` in production environment
2. Run database migrations: `alembic upgrade head`
3. Start the server: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.app.main:app`

# VI. Environment variables' descriptions

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

## Database Migrations

This project uses **Alembic** for database schema management and migrations.

### Migration Workflow

**Development (automatic):**
- The application automatically creates all tables on startup via SQLAlchemy (see `api/app/main.py`)
- This is convenient for local development but should NOT be used in production

**Production (explicit):**
- Always use Alembic migrations in production
- Migrations ensure reproducible, versioned schema changes across environments

### Common Migration Tasks

#### Create a New Migration (after changing models)
```bash
cd api
alembic revision --autogenerate -m "Add new column to users table"
```

#### Review the Migration
Check the generated migration file in `api/alembic/versions/` before applying it.

#### Apply Migrations (Upgrade)
```bash
cd api
# Upgrade to the latest migration
alembic upgrade head

# Upgrade to a specific revision
alembic upgrade <revision_id>

# Upgrade by N steps
alembic upgrade +2
```

#### Rollback Migrations (Downgrade)
```bash
cd api
# Downgrade to the previous migration
alembic downgrade -1

# Downgrade to a specific revision
alembic downgrade <revision_id>

# Downgrade to base (empty schema)
alembic downgrade base
```

#### Check Migration Status
```bash
cd api
# View current revision
alembic current

# View migration history
alembic history

# Check for schema drift
alembic check
```

### Alembic Configuration
- **Location:** `api/alembic.ini` - Main Alembic config file
- **Env script:** `api/alembic/env.py` - Runtime configuration for migrations
- **Versions:** `api/alembic/versions/` - Migration scripts

### Best Practices
1. **Always review auto-generated migrations** before committing
2. **Test migrations locally** before applying to production
3. **Create descriptive migration names** (e.g., `add_phone_column_to_users`)
4. **Never manually edit migration files** after applying them in production
5. **Keep migrations small and focused** on a single schema change
6. **Use `alembic check`** before deployment to verify schema alignment

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


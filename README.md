# Splitwise Clone

Expense splitting application built with FastAPI and PostgreSQL.
Software Engineering course project - Harbour Space University.

## Quick Start

```bash
# 1. Setup PostgreSQL (automated)
bash scripts/setup_postgres.sh

# 2. Test database connection
python scripts/test_db_connection.py

# 3. Install and run
cd api
pip install -r requirements.txt
python -m app.main
```

**Or manually:** See [POSTGRES_SETUP.md](POSTGRES_SETUP.md)

Visit http://localhost:8000/docs

📖 **See [QUICKSTART.md](QUICKSTART.md) for detailed instructions**

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
│   └── requirements.txt
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

Full API documentation: http://localhost:8000/docs

## Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret for JWT tokens (generate with `openssl rand -hex 32`)

Optional: See `.env.example` for all available options.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# With coverage
pytest tests/ --cov=app
```

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Setup instructions
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

# Quick Start Guide

Get the Splitwise Clone API running in a few minutes.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- pip package manager

## Setup Steps

### Option A: Automated Setup (Recommended)

```bash
# Run the setup script
bash scripts/setup_postgres.sh

# Skip to step 3
```

### Option B: Manual Setup

#### 1. Install PostgreSQL

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start
```

#### 2. Create Database

```bash
sudo -u postgres psql
```

In PostgreSQL prompt:
```sql
CREATE DATABASE splitwise_db;
CREATE USER splitwise_user WITH PASSWORD 'your_password';
ALTER DATABASE splitwise_db OWNER TO splitwise_user;
GRANT ALL ON SCHEMA public TO splitwise_user;
\q
```

### 3. Test Database Connection

```bash
python scripts/test_db_connection.py
```

If successful, proceed to step 4.

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:
```bash
DATABASE_URL=postgresql://splitwise_user:your_password@localhost:5432/splitwise_db
JWT_SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
DB_SSL=false
```

### 5. Install Dependencies

```bash
cd api
pip-sync requirements.txt
```

### 6. Run Application

```bash
python -m app.main
```

Visit http://localhost:8000/docs

## Verify Installation

Test the API:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"test123"}'
```

## Common Commands

```bash
# Start PostgreSQL
sudo service postgresql start

# Test database connection
python scripts/test_db_connection.py

# Validate environment
python api/check_env.py

# Run tests
pytest tests/ -v
```

## Troubleshooting

**Connection refused:** Check PostgreSQL is running with `sudo service postgresql status`

**Permission denied:** See [POSTGRES_SETUP.md](POSTGRES_SETUP.md) to fix permissions

**Import errors:** Ensure you're in the `api` directory when running `python -m app.main`

For detailed PostgreSQL setup, see [POSTGRES_SETUP.md](POSTGRES_SETUP.md)

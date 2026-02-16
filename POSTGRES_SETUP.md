# PostgreSQL Setup Guide

## Installation

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start
```

## Create Database and User

### Using postgres superuser

```bash
# Access PostgreSQL as postgres user (no password needed)
sudo -u postgres psql
```

### Setup commands

```sql
-- Create database
CREATE DATABASE splitwise_db;

-- Create user
CREATE USER splitwise_user WITH PASSWORD 'your_secure_password';

-- Transfer ownership
ALTER DATABASE splitwise_db OWNER TO splitwise_user;

-- Grant permissions
\c splitwise_db
GRANT ALL ON SCHEMA public TO splitwise_user;
GRANT CREATE ON SCHEMA public TO splitwise_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO splitwise_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO splitwise_user;

-- Exit
\q
```

## Configure Application

Update `.env` file:
```bash
DATABASE_URL=postgresql://splitwise_user:your_password@localhost:5432/splitwise_db
DB_SSL=false
```

## Automated Setup

Use the provided script:
```bash
bash scripts/setup_postgres.sh
```

This will create the database, user, and configure permissions automatically.

## Common Operations

### Connect to database
```bash
psql -h localhost -U splitwise_user -d splitwise_db
```

### Access as superuser
```bash
sudo -u postgres psql
```

### List databases
```bash
sudo -u postgres psql -l
```

## Useful PostgreSQL Commands

Inside `psql` prompt:

```sql
\l              -- List databases
\c dbname       -- Connect to database
\dt             -- List tables
\du             -- List users
\q              -- Quit
```

## Test Connection

```bash
python scripts/test_db_connection.py
```

## Common Issues

**Can't connect:** Ensure PostgreSQL is running
```bash
sudo service postgresql status
```

**Permission denied:** Make user the database owner
```sql
ALTER DATABASE splitwise_db OWNER TO splitwise_user;
```

**Wrong password:** The postgres user doesn't use a password. Use:
```bash
sudo -u postgres psql
```

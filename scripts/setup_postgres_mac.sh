#!/bin/bash
# PostgreSQL Setup Script for macOS
# This script automates the installation and configuration of PostgreSQL using Homebrew

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_NAME="splitwise_db"
DB_USER="splitwise_user"
DB_PASSWORD="splitwise_dev_password_$(date +%s)"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PostgreSQL Setup for Splitwise Clone (macOS)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

# Step 1: Check for Homebrew & PostgreSQL
echo -e "${YELLOW}[1/7] Checking for Homebrew and PostgreSQL...${NC}"
if ! command -v brew &> /dev/null; then
    echo -e "${RED}✗ Homebrew not found. Please install it from https://brew.sh/${NC}"
    exit 1
fi

if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL is already installed ($(psql --version))${NC}\n"
else
    echo -e "${YELLOW}PostgreSQL not found. Installing via Homebrew...${NC}"
    brew install postgresql@14
    brew link postgresql@14 --force
    echo -e "${GREEN}✓ PostgreSQL installed successfully${NC}\n"
fi

# Step 2: Start PostgreSQL Service
echo -e "${YELLOW}[2/7] Starting PostgreSQL service...${NC}"
# Homebrew uses services start instead of 'sudo service'
brew services start postgresql@14 || brew services restart postgresql@14
sleep 3

if pg_isready > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}\n"
else
    echo -e "${RED}✗ Failed to start PostgreSQL. Check 'brew services list'${NC}"
    exit 1
fi

# Step 3 & 4: Database Creation (macOS postgres usually runs as current user)
echo -e "${YELLOW}[3/4] Checking/Creating database...${NC}"
if psql postgres -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${YELLOW}⚠  Database '$DB_NAME' already exists${NC}"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        psql postgres -c "DROP DATABASE $DB_NAME;"
        psql postgres -c "CREATE DATABASE $DB_NAME;"
        echo -e "${GREEN}✓ Recreated database${NC}"
    else
        echo -e "${YELLOW}Keeping existing database${NC}"
    fi
else
    psql postgres -c "CREATE DATABASE $DB_NAME;"
    echo -e "${GREEN}✓ Database '$DB_NAME' created${NC}"
fi

# Step 5: Create User
echo -e "${YELLOW}[5/7] Configuring database user...${NC}"
if psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo -e "${YELLOW}⚠  User '$DB_USER' already exists${NC}"
    read -p "Recreate user? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        psql postgres -c "DROP USER $DB_USER;"
        psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    else
        read -p "Enter existing password for '$DB_USER': " -s DB_PASSWORD
        echo
    fi
else
    psql postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
fi

# Step 6: Grant Privileges
echo -e "${YELLOW}[6/7] Granting privileges...${NC}"
psql -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
psql -d "$DB_NAME" -c "GRANT ALL ON SCHEMA public TO $DB_USER;"
psql -d "$DB_NAME" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;"
echo -e "${GREEN}✓ Privileges granted${NC}\n"

# Step 7: Update .env
echo -e "${YELLOW}[7/7] Updating .env file...${NC}"
cd "$(dirname "$0")/.."
[ -f .env.example ] && [ ! -f .env ] && cp .env.example .env

DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
# macOS sed requires an empty string for the -i flag
sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" .env
sed -i '' "s|DB_SSL=.*|DB_SSL=false|" .env

# Final connection test
if PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connection test successful!${NC}\n"
else
    echo -e "${RED}✗ Connection test failed.${NC}"
fi

echo -e "${BLUE}Setup Complete!${NC}"
echo -e "Next Step: ${BLUE}python3 -m api.app.main${NC}"
#!/bin/bash
# PostgreSQL Setup Script for Ubuntu WSL
# This script automates the installation and configuration of PostgreSQL

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
DB_PASSWORD="splitwise_dev_password_$(date +%s)"  # Generate unique password

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PostgreSQL Setup for Splitwise Clone${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

# Step 1: Check if PostgreSQL is installed
echo -e "${YELLOW}[1/7] Checking if PostgreSQL is installed...${NC}"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL is already installed ($(psql --version))${NC}\n"
else
    echo -e "${YELLOW}PostgreSQL not found. Installing...${NC}"
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
    echo -e "${GREEN}✓ PostgreSQL installed successfully${NC}\n"
fi

# Step 2: Start PostgreSQL
echo -e "${YELLOW}[2/7] Starting PostgreSQL service...${NC}"
sudo service postgresql start
sleep 2

if sudo service postgresql status | grep -q "online"; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}\n"
else
    echo -e "${RED}✗ Failed to start PostgreSQL${NC}"
    echo -e "${YELLOW}Trying to initialize cluster...${NC}"

    # Try to find the version
    PG_VERSION=$(psql --version | grep -oP '\d+' | head -1)
    sudo pg_ctlcluster $PG_VERSION main start || true
    sleep 2

    if sudo service postgresql status | grep -q "online"; then
        echo -e "${GREEN}✓ PostgreSQL started successfully${NC}\n"
    else
        echo -e "${RED}✗ Could not start PostgreSQL. Please check logs.${NC}"
        exit 1
    fi
fi

# Step 3: Check if database already exists
echo -e "${YELLOW}[3/7] Checking if database exists...${NC}"
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${YELLOW}⚠  Database '$DB_NAME' already exists${NC}"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo -u postgres psql -c "DROP DATABASE $DB_NAME;" 2>/dev/null || true
        echo -e "${GREEN}✓ Dropped existing database${NC}"
    else
        echo -e "${YELLOW}Keeping existing database${NC}"
        DB_EXISTS=true
    fi
fi

# Step 4: Create database
if [ "$DB_EXISTS" != "true" ]; then
    echo -e "${YELLOW}[4/7] Creating database...${NC}"
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
    echo -e "${GREEN}✓ Database '$DB_NAME' created${NC}\n"
else
    echo -e "${YELLOW}[4/7] Skipping database creation${NC}\n"
fi

# Step 5: Check if user exists
echo -e "${YELLOW}[5/7] Creating database user...${NC}"
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo -e "${YELLOW}⚠  User '$DB_USER' already exists${NC}"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo -u postgres psql -c "DROP USER $DB_USER;" 2>/dev/null || true
        sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
        echo -e "${GREEN}✓ User recreated with new password${NC}"
    else
        echo -e "${YELLOW}Keeping existing user (password unchanged)${NC}"
        read -p "Enter the password for existing user '$DB_USER': " -s DB_PASSWORD
        echo
    fi
else
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    echo -e "${GREEN}✓ User '$DB_USER' created${NC}"
fi

# Step 6: Grant privileges
echo -e "${YELLOW}[6/7] Granting privileges...${NC}"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL ON SCHEMA public TO $DB_USER;"
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;"
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;"
sudo -u postgres psql -d $DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;"
sudo -u postgres psql -d $DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;"
echo -e "${GREEN}✓ Privileges granted${NC}\n"

# Step 7: Update .env file
echo -e "${YELLOW}[7/7] Configuring .env file...${NC}"

# Go to project root
cd "$(dirname "$0")/.."

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env from .env.example${NC}"
    else
        echo -e "${RED}✗ .env.example not found${NC}"
        exit 1
    fi
fi

# Update DATABASE_URL in .env
DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"

# Use perl for in-place editing (more reliable in WSL)
perl -i -pe "s|DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" .env
perl -i -pe "s|DB_SSL=.*|DB_SSL=false|" .env

echo -e "${GREEN}✓ Updated .env file${NC}\n"

# Test connection
echo -e "${YELLOW}Testing database connection...${NC}"
if PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connection test successful!${NC}\n"
else
    echo -e "${RED}✗ Connection test failed${NC}"
    echo -e "${YELLOW}You may need to configure pg_hba.conf for password authentication${NC}\n"
fi

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

echo -e "${GREEN}Database Configuration:${NC}"
echo -e "  Database Name: ${BLUE}$DB_NAME${NC}"
echo -e "  Database User: ${BLUE}$DB_USER${NC}"
echo -e "  Database Password: ${BLUE}$DB_PASSWORD${NC}"
echo -e "  Connection URL: ${BLUE}$DATABASE_URL${NC}\n"

echo -e "${GREEN}Your .env file has been updated with the database URL.${NC}\n"

echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Validate environment: ${BLUE}python3 api/check_env.py${NC}"
echo -e "  2. Install dependencies: ${BLUE}pip-sync api/requirements.txt${NC}"
echo -e "  3. Start the application: ${BLUE}python3 -m api.app.main${NC}"
echo -e "  4. Visit API docs: ${BLUE}http://localhost:8000/docs${NC}\n"

echo -e "${YELLOW}To start PostgreSQL in the future:${NC}"
echo -e "  ${BLUE}sudo service postgresql start${NC}\n"

echo -e "${YELLOW}To make PostgreSQL start automatically, add to ~/.bashrc:${NC}"
echo -e "  ${BLUE}echo 'sudo service postgresql start' >> ~/.bashrc${NC}\n"

# Save credentials to a file for reference
CREDS_FILE="$(dirname "$0")/../.postgres_credentials"
cat > "$CREDS_FILE" << EOF
# PostgreSQL Credentials
# Generated on $(date)
# DO NOT COMMIT THIS FILE

DATABASE_NAME=$DB_NAME
DATABASE_USER=$DB_USER
DATABASE_PASSWORD=$DB_PASSWORD
DATABASE_URL=$DATABASE_URL
EOF

echo -e "${GREEN}Credentials saved to: ${BLUE}.postgres_credentials${NC}"
echo -e "${YELLOW}(This file is git-ignored for security)${NC}\n"

echo -e "${GREEN}All done! 🎉${NC}\n"

#!/bin/bash

# Data Governance Platform - Start Script

echo "========================================="
echo "Data Governance Platform - Starting..."
echo "========================================="
echo ""

# Check if PostgreSQL is running
echo "Checking PostgreSQL..."
if docker ps | grep -q governance_postgres; then
    echo "✓ PostgreSQL is running"
else
    echo "✗ PostgreSQL is not running"
    echo "  Starting PostgreSQL with docker-compose..."
    docker-compose up -d
    echo "  Waiting for PostgreSQL to be ready..."
    sleep 5
fi

echo ""
echo "Starting FastAPI backend..."
echo ""

cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

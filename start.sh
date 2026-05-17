#!/bin/bash

# ARIA Startup Script
# This script starts all services and runs the complete system

set -e  # Exit on error

echo "🚀 Starting ARIA System..."
echo "================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

echo -e "${GREEN}✅ Environment file found${NC}"

# Stop any existing containers
echo ""
echo "🛑 Stopping existing containers..."
docker-compose down

# Remove old containers and volumes (optional - uncomment if needed)
# docker-compose down -v

# Build and start all services
echo ""
echo "🏗️  Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting all services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U ${POSTGRES_USER:-aria} > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not ready${NC}"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis is not ready${NC}"
fi

# Check API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is ready${NC}"
else
    echo -e "${YELLOW}⚠️  API is starting (may take a few more seconds)${NC}"
fi

# Run database migrations
echo ""
echo "🗄️  Running database migrations..."
docker-compose exec -T -w /app/api api alembic upgrade head

echo ""
echo "================================"
echo -e "${GREEN}✅ ARIA System Started Successfully!${NC}"
echo ""
echo "📊 Service Status:"
echo "  - API: http://localhost:8000"
echo "  - API Health: http://localhost:8000/health"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "📝 View Logs:"
echo "  - All services: docker-compose logs -f"
echo "  - API only: docker-compose logs -f api"
echo "  - Worker only: docker-compose logs -f worker"
echo ""
echo "🛑 Stop Services:"
echo "  - docker-compose down"
echo ""
echo "🔧 Useful Commands:"
echo "  - Restart API: docker-compose restart api"
echo "  - Restart Worker: docker-compose restart worker"
echo "  - View API logs: docker-compose logs -f api"
echo "  - Shell into API: docker-compose exec api bash"
echo ""

# Made with Bob

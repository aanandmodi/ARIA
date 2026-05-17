# ARIA Startup Script for Windows PowerShell
# This script starts all services and runs the complete system

Write-Host "🚀 Starting ARIA System..." -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "❌ Error: .env file not found" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and configure it" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Environment file found" -ForegroundColor Green

# Stop any existing containers
Write-Host ""
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Build and start all services
Write-Host ""
Write-Host "🏗️  Building Docker images..." -ForegroundColor Cyan
docker-compose build

Write-Host ""
Write-Host "🚀 Starting all services..." -ForegroundColor Green
docker-compose up -d

# Wait for services to be ready
Write-Host ""
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host ""
Write-Host "🔍 Checking service health..." -ForegroundColor Cyan

# Check PostgreSQL
try {
    $pgCheck = docker-compose exec -T postgres pg_isready -U aria 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL is ready" -ForegroundColor Green
    } else {
        Write-Host "❌ PostgreSQL is not ready" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ PostgreSQL check failed" -ForegroundColor Red
}

# Check Redis
try {
    $redisCheck = docker-compose exec -T redis redis-cli ping 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Redis is ready" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis is not ready" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Redis check failed" -ForegroundColor Red
}

# Check API
try {
    $apiCheck = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($apiCheck.StatusCode -eq 200) {
        Write-Host "✅ API is ready" -ForegroundColor Green
    } else {
        Write-Host "⚠️  API is starting (may take a few more seconds)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  API is starting (may take a few more seconds)" -ForegroundColor Yellow
}

# Run database migrations
Write-Host ""
Write-Host "🗄️  Running database migrations..." -ForegroundColor Cyan
docker-compose exec -T -w /app/api api alembic upgrade head

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ ARIA System Started Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Service Status:" -ForegroundColor Cyan
Write-Host "  - API: http://localhost:8000"
Write-Host "  - API Health: http://localhost:8000/health"
Write-Host "  - PostgreSQL: localhost:5432"
Write-Host "  - Redis: localhost:6379"
Write-Host ""
Write-Host "📝 View Logs:" -ForegroundColor Cyan
Write-Host "  - All services: docker-compose logs -f"
Write-Host "  - API only: docker-compose logs -f api"
Write-Host "  - Worker only: docker-compose logs -f worker"
Write-Host ""
Write-Host "🛑 Stop Services:" -ForegroundColor Cyan
Write-Host "  - docker-compose down"
Write-Host ""
Write-Host "🔧 Useful Commands:" -ForegroundColor Cyan
Write-Host "  - Restart API: docker-compose restart api"
Write-Host "  - Restart Worker: docker-compose restart worker"
Write-Host "  - View API logs: docker-compose logs -f api"
Write-Host "  - Shell into API: docker-compose exec api bash"
Write-Host ""

# Made with Bob

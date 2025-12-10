# Docker Quick Start Script (Windows)

Write-Host "🐳 Legal Advisor - Docker Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if .env exists
if (-Not (Test-Path .env)) {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "📝 Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ .env created" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit .env with your API keys before running!" -ForegroundColor Yellow
    Write-Host "   Required: OPENAI_API_KEY, GOOGLE_API_KEY, PINECONE_API_KEY" -ForegroundColor Yellow
    Write-Host ""
    Pause
}

# Build and start containers
Write-Host ""
Write-Host "🏗️  Building Docker images..." -ForegroundColor Cyan
docker-compose build

Write-Host ""
Write-Host "🚀 Starting containers..." -ForegroundColor Cyan
docker-compose up -d

Write-Host ""
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Check health
Write-Host ""
Write-Host "🏥 Health Check:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 API running at: http://localhost:8000" -ForegroundColor Green
Write-Host "📖 API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "🏥 Health: http://localhost:8000/api/health" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Useful Commands:" -ForegroundColor Cyan
Write-Host "   View logs:     docker-compose logs -f api"
Write-Host "   Stop:          docker-compose down"
Write-Host "   Restart:       docker-compose restart api"
Write-Host "   Shell access:  docker-compose exec api bash"
Write-Host ""

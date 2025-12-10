#!/bin/bash
# Docker Quick Start Script

set -e

echo "🐳 Legal Advisor - Docker Setup"
echo "================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env with your API keys before running!"
    echo "   Required: OPENAI_API_KEY, GOOGLE_API_KEY, PINECONE_API_KEY"
    echo ""
    read -p "Press Enter after updating .env to continue..."
fi

# Build and start containers
echo ""
echo "🏗️  Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo ""
echo "🏥 Health Check:"
docker-compose ps

echo ""
echo "📊 Database Status:"
docker-compose exec postgres pg_isready -U legal_advisor || echo "⚠️  Database not ready yet"

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📍 API running at: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🏥 Health: http://localhost:8000/api/health"
echo ""
echo "📝 Useful Commands:"
echo "   View logs:     docker-compose logs -f api"
echo "   Stop:          docker-compose down"
echo "   Restart:       docker-compose restart api"
echo "   Shell access:  docker-compose exec api bash"
echo ""

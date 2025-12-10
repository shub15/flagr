# Docker Deployment Guide

## 🐳 Quick Start (Recommended)

### Windows
```powershell
.\docker-start.ps1
```

### Linux/Mac
```bash
chmod +x docker-start.sh
./docker-start.sh
```

## 📦 Manual Setup

### 1. Prerequisites
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+

### 2. Configure Environment

```bash
# Copy example environment
cp .env.example .env

# Edit with your API keys
nano .env  # or use any editor
```

**Required variables:**
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_ENVIRONMENT`

### 3. Build & Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Verify

```bash
# Check health
curl http://localhost:8000/api/health

# Open API docs
open http://localhost:8000/docs
```

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Legal Advisor  │
│      API        │ :8000
│   (FastAPI)     │
└────────┬────────┘
         │
         │ connects to
         ▼
┌─────────────────┐
│   PostgreSQL    │ :5432
│    Database     │
└─────────────────┘
```

**Containers:**
1. **`api`** - FastAPI application
2. **`postgres`** - PostgreSQL 15 database

**Volumes:**
- `postgres_data` - Database persistence
- `./data/legal_docs` - Legal document uploads
- `./data/temp_uploads` - Temporary contract files
- `./data/exports` - Generated reports

---

## 🔧 Common Commands

### Container Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart API only
docker-compose restart api

# View running containers
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (API only)
docker-compose logs -f api
```

### Database Operations
```bash
# Access PostgreSQL shell
docker-compose exec postgres psql -U legal_advisor -d legal_advisor

# Run migrations (if using Alembic)
docker-compose exec api alembic upgrade head

# Backup database
docker-compose exec postgres pg_dump -U legal_advisor legal_advisor > backup.sql

# Restore database
docker-compose exec -T postgres psql -U legal_advisor legal_advisor < backup.sql
```

### API Container Access
```bash
# Shell access
docker-compose exec api bash

# Run Python commands
docker-compose exec api python -m app.database.session

# Install new package (not recommended, rebuild instead)
docker-compose exec api pip install package_name
```

---

## 🔐 Security Best Practices

### 1. Environment Variables
```bash
# Never commit .env files
# Use strong passwords for production
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

### 2. Production Deployment
```yaml
# docker-compose.prod.yml
services:
  api:
    restart: always
    environment:
      DEBUG: false
      LOG_LEVEL: WARNING
    # Use secrets management
```

### 3. Network Security
```bash
# Restrict PostgreSQL port (don't expose publicly)
# Remove ports mapping in production:
# ports:
#   - "5432:5432"  # Comment this out
```

---

## 📊 Monitoring

### Health Checks
```bash
# API health
curl http://localhost:8000/api/health

# Database health
docker-compose exec postgres pg_isready

# Container health
docker inspect legal_advisor_api | grep -A 10 Health
```

### Logs
```bash
# Real-time logs
docker-compose logs -f --tail=100

# Export logs
docker-compose logs > logs_$(date +%Y%m%d).txt
```

---

## 🚀 Production Deployment

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml legal_advisor

# Scale API
docker service scale legal_advisor_api=3
```

### Kubernetes (Minikube example)
```bash
# Convert docker-compose to k8s
kompose convert

# Deploy to k8s
kubectl apply -f .

# Expose service
kubectl expose deployment api --type=LoadBalancer --port=8000
```

---

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs api

# Check environment
docker-compose config

# Rebuild without cache
docker-compose build --no-cache
```

### Database connection errors
```bash
# Check database health
docker-compose exec postgres pg_isready

# Verify connection string
docker-compose exec api env | grep DATABASE_URL

# Reset database
docker-compose down -v  # WARNING: Deletes data
docker-compose up -d
```

### Port conflicts
```bash
# Check what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Linux/Mac

# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Out of disk space
```bash
# Clean up Docker
docker system prune -a --volumes

# Remove old images
docker image prune -a
```

---

## 📝 Development Workflow

### 1. Local Development with Docker
```bash
# Mount code as volume for hot reload
# Add to docker-compose.yml:
volumes:
  - .:/app
  
# Use development image
docker-compose -f docker-compose.dev.yml up
```

### 2. Testing in Container
```bash
# Run tests
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=app
```

### 3. Debugging
```bash
# Attach debugger
docker-compose up  # No -d for attached mode

# Set breakpoint in code, then
docker-compose exec api python -m pdb app/main.py
```

---

## 🔄 Updates & Maintenance

### Update Dependencies
```bash
# Edit requirements.txt
nano requirements.txt

# Rebuild image
docker-compose build --no-cache

# Restart services
docker-compose up -d
```

### Database Migrations
```bash
# Create migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migration
docker-compose exec api alembic upgrade head

# Rollback
docker-compose exec api alembic downgrade -1
```

---

## 💡 Tips

1. **Use `.env` for secrets** - Never hardcode API keys
2. **Volume mounts** - Use for data persistence and hot reload
3. **Multi-stage builds** - Keep production images small
4. **Health checks** - Ensure containers are actually ready
5. **Resource limits** - Set memory/CPU limits for production

```yaml
# Resource limits example
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## 📚 Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)

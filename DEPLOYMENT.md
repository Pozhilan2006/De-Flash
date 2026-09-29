# Flash Loan Safety Net - Deployment Guide

## 🐳 Docker Deployment

### Local Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Production Deployment

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with production values
nano .env

# 3. Build and start production services
docker-compose -f docker-compose.prod.yml up -d

# 4. Initialize database
docker-compose -f docker-compose.prod.yml exec backend python database_config.py

# 5. Check health
curl http://localhost:8000/health
```

## 📦 Manual Deployment

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/flash_loan_safety"
export REDIS_URL="redis://localhost:6379/0"

# 3. Initialize database
python database_config.py

# 4. Run with Gunicorn
gunicorn api_endpoint:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## 🔒 Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Use strong SECRET_KEY (min 32 characters)
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Enable Redis password authentication
- [ ] Review CORS settings in `api_endpoint.py`
- [ ] Set up monitoring and alerting

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# Docker
docker-compose logs -f backend

# Manual
tail -f /var/log/flash_loan_safety/app.log
```

## 🔄 Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🆘 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready

# Check connection string
echo $DATABASE_URL
```

### Redis Connection Issues
```bash
# Check Redis
docker-compose exec redis redis-cli ping
```

### Backend Not Starting
```bash
# Check logs
docker-compose logs backend

# Check health
docker-compose ps
```

## 📈 Scaling

### Horizontal Scaling
```yaml
# docker-compose.prod.yml
backend:
  deploy:
    replicas: 3
```

### Load Balancing
Use nginx or cloud load balancer to distribute traffic across backend replicas.

---

**Production Ready!** 🚀

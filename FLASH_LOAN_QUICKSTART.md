# Flash Loan Safety Net – Quick Start Guide

Get the Flash Loan Safety Net running in **10 minutes** with step-by-step instructions.

## Prerequisites (2 minutes)

### Required Software
- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Node.js 16+** ([Download](https://nodejs.org/))
- **PostgreSQL 12+** ([Download](https://www.postgresql.org/download/))
- **Redis 6+** ([Download](https://redis.io/download))
- **Git** ([Download](https://git-scm.com/))

### Verify Installations
```bash
python --version      # Should be 3.9+
node --version        # Should be 16+
psql --version        # Should be 12+
redis-cli --version   # Should be 6+
git --version         # Should be 2.0+
```

## Step 1: Clone Repository (1 minute)

```bash
git clone https://github.com/Pozhilan2006/flash-loan-safety-net.git
cd flash-loan-safety-net
```

## Step 2: Setup Backend (3 minutes)

### 2.1 Create Virtual Environment
```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 2.2 Install Dependencies
```bash
pip install -r requirements.txt
```

### 2.3 Configure Environment
```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your editor
```

**Minimal .env for local testing:**
```bash
# Database
DATABASE_URL=postgresql://localhost/flash_loan_dev

# Blockchain (Use free RPC endpoints for testing)
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/demo
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/demo

# Optional: Leave empty for defaults
DISCORD_WEBHOOK=
TELEGRAM_BOT_TOKEN=

# ML Model Path
MODEL_PATH=./models/flash_loan_model.pkl
```

### 2.4 Setup Database
```bash
# Create database
createdb flash_loan_dev

# Run migrations
alembic upgrade head

# Seed with sample data (optional)
python scripts/seed_data.py
```

### 2.5 Start Backend
```bash
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
✓ Uvicorn running on http://0.0.0.0:8000
✓ Database connected
✓ ML models loaded
```

## Step 3: Setup Frontend (2 minutes)

### 3.1 Install Dependencies
```bash
cd ../frontend
npm install
```

### 3.2 Start Development Server
```bash
npm run dev
```

You should see:
```
✓ Local:   http://localhost:5173
✓ Network: http://192.168.x.x:5173
```

## Step 4: Verify Everything Works (2 minutes)

### Open Browser
Go to **http://localhost:5173** - you should see the Flash Loan Safety Net dashboard.

### Test Backend API
```bash
# In a new terminal:
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected",
  "models_loaded": true
}
```

### Test Risk Prediction
```bash
curl -X POST http://localhost:8000/risk/predict \
  -H "Content-Type: application/json" \
  -d '{
    "loan_amount": 1000000,
    "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "protocol": "aave",
    "transaction_type": "swap",
    "chain": "ethereum"
  }'
```

Expected response:
```json
{
  "risk_score": 45,
  "risk_level": "MEDIUM",
  "confidence": 0.92,
  "factors": ["high_loan_amount", "aave_protocol_risk"],
  "timestamp": "2026-01-06T15:30:00Z"
}
```

## Common Issues & Solutions

### Issue: "Connection refused" (PostgreSQL)
**Solution:**
```bash
# Start PostgreSQL service
# Windows:
pg_ctl -D "C:\Program Files\PostgreSQL\data" start

# Mac:
brew services start postgresql

# Linux:
sudo systemctl start postgresql
```

### Issue: "Redis connection error"
**Solution:**
```bash
# Start Redis
# Windows: Run redis-server.exe
# Mac:
brew services start redis

# Linux:
sudo systemctl start redis
```

### Issue: "ModuleNotFoundError: No module named 'torch'"
**Solution:**
```bash
# Install PyTorch (large download, ~2GB)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Issue: Port 8000 already in use
**Solution:**
```bash
# Use different port
python -m uvicorn app:app --reload --port 8001
```

### Issue: "npm ERR! code ERESOLVE"
**Solution:**
```bash
# Use npm legacy flag
npm install --legacy-peer-deps
```

## File Structure Created

After setup, you'll have:
```
flash-loan-safety-net/
├── backend/
│   ├── venv/                 # Virtual environment
│   ├── models/               # ML models
│   ├── app.py               # Main FastAPI app
│   ├── .env                 # Your config
│   └── requirements.txt
│
├── frontend/
│   ├── node_modules/        # NPM packages
│   ├── src/
│   └── package.json
│
└── docs/
```

## What's Running

| Service | URL | Status |
|---------|-----|--------|
| Backend API | http://localhost:8000 | ✓ Running |
| Frontend | http://localhost:5173 | ✓ Running |
| PostgreSQL | localhost:5432 | ✓ Running |
| Redis | localhost:6379 | ✓ Running |

## Next Steps

### 1. Explore Dashboard
- Navigate to Dashboard page
- Select blockchain (Ethereum/Polygon/Arbitrum/Optimism)
- Watch real-time transaction monitoring

### 2. Test Simulator
- Go to "Simulator" page
- Create a hypothetical flash loan scenario
- See predicted risk score

### 3. Monitor Alerts
- Check "Alerts" page
- View recent high-risk transactions
- Set custom alert thresholds

### 4. Read Full Docs
- [API Reference](./API_REFERENCE.md) - All endpoints
- [Architecture](./ARCHITECTURE.md) - System design
- [ML Models](./ML_MODELS.md) - Model details
- [Development Roadmap](./DEVELOPMENT_ROADMAP.md) - Build phases

## Development Tips

### Auto-reload Backend
The `--reload` flag watches for changes:
```bash
python -m uvicorn app:app --reload
```

### Auto-reload Frontend
Vite handles hot module replacement automatically.

### Debug Mode
Set in `.env`:
```bash
LOG_LEVEL=DEBUG
DEBUG=True
```

### Database Inspection
```bash
psql flash_loan_dev
\dt                    # List tables
SELECT * FROM loans;   # View data
```

### Redis CLI
```bash
redis-cli
> KEYS *               # See all cached data
> GET user:123        # Get specific key
```

## Testing Blockchain Integration

### Use Testnet (Recommended)
Edit `.env`:
```bash
ETH_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
POLYGON_RPC_URL=https://rpc-mumbai.maticvigil.com
```

### Get Test ETH
1. Go to [Alchemy Faucet](https://www.alchemy.com/faucets/ethereum-sepolia)
2. Enter your wallet address
3. Receive test ETH

## Performance Check

### Check API Response Time
```bash
time curl http://localhost:8000/health
# Should be <100ms
```

### Monitor Database
```bash
# In PostgreSQL
EXPLAIN ANALYZE SELECT * FROM transactions WHERE risk_score > 70;
```

### Check Memory Usage
```bash
# Python backend
pip install memory-profiler
python -m memory_profiler app.py
```

## Stopping Services

```bash
# Stop Backend (Ctrl+C in backend terminal)
# Stop Frontend (Ctrl+C in frontend terminal)
# Stop PostgreSQL
# Stop Redis
```

## Troubleshooting Checklist

- [ ] Python version 3.9+
- [ ] Node.js version 16+
- [ ] PostgreSQL running
- [ ] Redis running
- [ ] `.env` file configured
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Database migrations run
- [ ] Port 8000 available
- [ ] Port 5173 available

## Get Help

- 📖 Check full [Documentation](./START_HERE.md)
- 🐛 Open [GitHub Issue](https://github.com/Pozhilan2006/flash-loan-safety-net/issues)
- 💬 Join discussions on [GitHub](https://github.com/Pozhilan2006/flash-loan-safety-net/discussions)
- 🔗 Review [API Docs](./API_REFERENCE.md)

---

**You're all set! 🚀**

The Flash Loan Safety Net is now running locally. Navigate to http://localhost:5173 to start monitoring flash loan risks.

# 🚀 Starting the Environment

Quick guide to start the AI Study Companion for demo purposes.

---

## Prerequisites

- ✅ Python 3.11+ installed
- ✅ PostgreSQL database running (or Docker)
- ✅ Virtual environment activated (if using one)
- ✅ Demo accounts created: `python scripts/create_demo_users.py`

---

## Option 1: Docker (Easiest - Recommended)

### Start Everything (Database + API)
```powershell
# Start PostgreSQL and API in Docker
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop everything
docker-compose down
```

**API will be available at:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs

---

## Option 2: Local Development (Manual)

### Step 1: Start PostgreSQL Database

**If using Docker for database only:**
```powershell
docker-compose up -d postgres
```

**Or if PostgreSQL is installed locally:**
- Make sure PostgreSQL is running on port 5432
- Database: `pennygadget`
- User: `postgres`
- Password: (check your `.env` file or use default)

### Step 2: Start Backend API Server

**Option A: Using PowerShell script (Windows)**
```powershell
.\START_SERVER.ps1
```

**Option B: Using Python directly**
```powershell
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Option C: Using run script**
```powershell
python run_server.py
```

**API will be available at:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs

### Step 3: Start Frontend (Optional)

```powershell
cd examples/frontend-starter
npm install  # First time only
npm run dev
```

**Frontend will be available at:** http://localhost:3000

---

## Quick Verification

### Check if API is running:
```powershell
# Test health endpoint
curl http://localhost:8000/health

# Or open in browser:
# http://localhost:8000/docs
```

### Check if database is connected:
```powershell
# Run verification script
python scripts/verify_demo_users.py
```

---

## Demo Account Login

Once the backend is running, you can:

1. **Use the frontend** (if started):
   - Go to http://localhost:3000
   - Login with any demo account:
     - `demo_goal_complete@demo.com` / `demo123`
     - `demo_sat_complete@demo.com` / `demo123`
     - `demo_chemistry@demo.com` / `demo123`
     - `demo_low_sessions@demo.com` / `demo123`
     - `demo_multi_goal@demo.com` / `demo123`

2. **Use API directly**:
   - Open http://localhost:8000/docs
   - Test endpoints with demo user IDs

---

## Troubleshooting

### Database Connection Error
- Make sure PostgreSQL is running
- Check database credentials in `.env` file
- Verify port 5432 is not blocked

### Port Already in Use
- Change port: `--port 8001` (or edit `START_SERVER.ps1`)
- Or stop the process using port 8000

### Module Not Found
- Activate virtual environment: `.\venv\Scripts\Activate.ps1`
- Install dependencies: `pip install -r requirements.txt`

---

## Environment Variables

Create a `.env` file in the root directory (optional, defaults work for local dev):

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pennygadget
DB_USER=postgres
DB_PASSWORD=postgres

# OpenAI (optional for demo)
OPENAI_API_KEY=your_key_here

# Environment
ENVIRONMENT=development
```

---

## Next Steps

1. ✅ Start the environment (choose option above)
2. ✅ Verify demo accounts: `python scripts/verify_demo_users.py`
3. ✅ Open API docs: http://localhost:8000/docs
4. ✅ Demo to your boss! See `_docs/DEMO_USER_GUIDE.md`

---

**Ready to demo! 🎉**


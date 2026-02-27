# 🚀 VaakAI — Complete Setup & Run Guide

> Step-by-step instructions to get VaakAI running from a fresh machine. Follow every step in order.

---

## Table of Contents

1. [Prerequisites — Install Required Software](#1-prerequisites--install-required-software)
2. [Clone & Navigate to the Project](#2-clone--navigate-to-the-project)
3. [Obtain API Keys & Credentials](#3-obtain-api-keys--credentials)
4. [Create the `.env` File](#4-create-the-env-file)
5. [Option A — Run with Docker (Recommended)](#5-option-a--run-with-docker-recommended)
6. [Option B — Run Locally Without Docker](#6-option-b--run-locally-without-docker)
7. [Run Database Migrations](#7-run-database-migrations)
8. [Start the Backend API Server](#8-start-the-backend-api-server)
9. [Start the Celery Worker](#9-start-the-celery-worker)
10. [Set Up & Run the Analytics Dashboard](#10-set-up--run-the-analytics-dashboard)
11. [Verify Everything is Running](#11-verify-everything-is-running)
12. [Optional — Ollama for Local LLM](#12-optional--ollama-for-local-llm)
13. [Optional — LiveKit Server](#13-optional--livekit-server)
14. [Optional — WhatsApp Webhook Setup](#14-optional--whatsapp-webhook-setup)
15. [Running Tests](#15-running-tests)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. Prerequisites — Install Required Software

Install these on your machine before proceeding:

| Software | Version | Download Link | Purpose |
|----------|---------|--------------|---------|
| **Python** | 3.11+ | https://www.python.org/downloads/ | Backend API |
| **Node.js** | 18+ | https://nodejs.org/ | Dashboard frontend |
| **Git** | Latest | https://git-scm.com/ | Version control |
| **Docker Desktop** | Latest | https://www.docker.com/products/docker-desktop/ | Container runtime (Option A) |
| **PostgreSQL** | 15+ | https://www.postgresql.org/download/ | Database (Option B only) |
| **Redis** | 7+ | https://redis.io/download/ (or [Memurai](https://www.memurai.com/) for Windows) | Session store (Option B only) |

### Verify installations

Open a terminal and run:

```bash
python --version        # Should show 3.11.x or higher
node --version          # Should show 18.x or higher
npm --version           # Should show 9.x or higher
git --version           # Should show 2.x+
docker --version        # Should show 24.x+ (only if using Docker)
docker-compose --version
```

> **Windows users**: Make sure Python is added to PATH during installation (check the box "Add Python to PATH"). For Redis, use [Memurai](https://www.memurai.com/) or run Redis inside Docker.

---

## 2. Clone & Navigate to the Project

```bash
# If you have a Git repo
git clone <your-repo-url>
cd vaakai

# Or if you already have the project folder
cd d:\hackathons\SITinnovate2\projectX\vaakai
```

Confirm you can see these files:

```bash
dir          # Windows
# or
ls           # macOS/Linux
```

You should see: `config.py`, `requirements.txt`, `docker-compose.yml`, `Dockerfile`, `manage.py`, `.env.example`, etc.

---

## 3. Obtain API Keys & Credentials

You need API keys from the following services. **Sign up and get keys from each:**

### 3.1 — OpenAI (Required)
1. Go to https://platform.openai.com/signup
2. Sign up or log in
3. Go to **API Keys** → https://platform.openai.com/api-keys
4. Click **"Create new secret key"**
5. Copy the key (starts with `sk-...`)
6. **Add billing**: Go to Settings → Billing → Add payment method (API calls are paid)

### 3.2 — AI4Bharat (Required for Indian languages)
1. Go to https://models.ai4bharat.org
2. Sign up and create an account
3. Go to your dashboard → API Keys section
4. Create a new API key and copy it

> AI4Bharat provides open-source Indian language STT/TTS models (IndicASR, IndicTTS).

### 3.3 — Deepgram (Required for English STT fallback)
1. Go to https://console.deepgram.com/signup
2. Sign up (free tier gives $200 credit)
3. Go to **API Keys** in the dashboard
4. Click **"Create Key"** → copy the key

### 3.4 — ElevenLabs (Required for English TTS)
1. Go to https://elevenlabs.io/sign-up
2. Sign up (free tier available)
3. Go to **Profile** → **API Keys**
4. Copy your API key

### 3.5 — Meta WhatsApp Business API (Optional — only if using WhatsApp)
1. Go to https://developers.facebook.com/
2. Create an app → Select **"Business"** type
3. Add **WhatsApp** product
4. Go to WhatsApp → **API Setup**
5. Copy the **Temporary Access Token** and **Phone Number ID**

### 3.6 — Salesforce (Optional — only if using CRM)
1. Sign up for a Salesforce Developer account: https://developer.salesforce.com/signup
2. Go to Setup → Apps → **Connected Apps** → Create new
3. Enable OAuth → copy **Client ID** and **Client Secret**
4. Set callback URL to `https://login.salesforce.com/services/oauth2/callback`

### 3.7 — Twilio (Optional — only if using phone calls)
1. Go to https://www.twilio.com/try-twilio
2. Sign up and verify your phone number
3. Go to Console Dashboard
4. Copy **Account SID** and **Auth Token**
5. Get a phone number from the **Phone Numbers** section

### 3.8 — SAP / Odoo (Optional — only if using ERP)
- **SAP**: Use your organization's SAP instance URL and API credentials
- **Odoo**: Use your Odoo instance URL + database name + API key

---

## 4. Create the `.env` File

Copy the template and fill in your keys:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Now open `.env` in any text editor and replace the placeholder values:

```dotenv
# ── STT (Speech-to-Text) ──────────────────────────
AI4BHARAT_API_KEY=paste_your_ai4bharat_key_here
DEEPGRAM_API_KEY=paste_your_deepgram_key_here

# ── LLM (Large Language Model) ─────────────────────
OPENAI_API_KEY=sk-paste_your_openai_key_here
LLAMA_API_URL=http://localhost:11434

# ── TTS (Text-to-Speech) ──────────────────────────
ELEVENLABS_API_KEY=paste_your_elevenlabs_key_here

# ── Storage (keep defaults for Docker setup) ───────
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql+asyncpg://vaakai:vaakai_secure_pass@localhost:5432/vaakai

# ── LiveKit ────────────────────────────────────────
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=your_secret

# ── WhatsApp (optional — leave as-is if not using) ─
WHATSAPP_TOKEN=your_meta_token
WHATSAPP_PHONE_NUMBER_ID=your_number_id

# ── CRM (optional) ─────────────────────────────────
CRM_PROVIDER=salesforce
CRM_API_URL=https://yourorg.salesforce.com
CRM_API_KEY=your_crm_oauth_token

# ── ERP (optional) ─────────────────────────────────
ERP_PROVIDER=odoo
ERP_API_URL=https://your-odoo.com
ERP_API_KEY=your_erp_key

# ── Telephony (optional) ──────────────────────────
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+91XXXXXXXXXX

# ── Thresholds ─────────────────────────────────────
FRAUD_SCORE_THRESHOLD=0.75
URGENCY_SCORE_THRESHOLD=7

# ── Application ───────────────────────────────────
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

> ⚠️ **IMPORTANT**: Never commit your `.env` file to Git. It contains secrets. The `.env.example` file is the safe template.

---

## 5. Option A — Run with Docker (Recommended)

This is the easiest way. Docker handles Redis, PostgreSQL, LiveKit, and the API server automatically.

### Step 1: Make sure Docker Desktop is running

Open Docker Desktop and ensure it shows "Engine Running".

### Step 2: Build and start all services

```bash
cd d:\hackathons\SITinnovate2\projectX\vaakai
docker-compose up -d --build
```

This will:
- Build the VaakAI API image from the Dockerfile
- Start **5 containers**: `vaakai-api`, `vaakai-redis`, `vaakai-postgres`, `vaakai-livekit`, `vaakai-celery`
- Automatically run database migrations

### Step 3: Check all containers are running

```bash
docker-compose ps
```

You should see all 5 services with status `Up`:

```
NAME              STATUS          PORTS
vaakai-api        Up (healthy)    0.0.0.0:8000->8000/tcp
vaakai-redis      Up (healthy)    0.0.0.0:6379->6379/tcp
vaakai-postgres   Up (healthy)    0.0.0.0:5432->5432/tcp
vaakai-livekit    Up              0.0.0.0:7880->7880/tcp
vaakai-celery     Up
```

### Step 4: View logs

```bash
# All services
docker-compose logs -f

# Just the API
docker-compose logs -f vaakai-api
```

### Step 5: Stop everything

```bash
docker-compose down          # Stop containers
docker-compose down -v       # Stop + delete data volumes
```

**Skip to [Step 10](#10-set-up--run-the-analytics-dashboard)** for the dashboard setup.

---

## 6. Option B — Run Locally Without Docker

If you prefer running without Docker, follow these manual steps.

### Step 1: Start Redis

**Windows** (using Memurai or WSL):
```bash
# If using Memurai
memurai-server

# If using WSL
wsl
sudo service redis-server start
```

**macOS**:
```bash
brew install redis
brew services start redis
```

**Linux**:
```bash
sudo apt install redis-server
sudo systemctl start redis
```

Verify Redis is running:
```bash
redis-cli ping
# Should respond: PONG
```

### Step 2: Start PostgreSQL

**Windows** (using pgAdmin or CLI):
```bash
# Start the PostgreSQL service if not running
net start postgresql-x64-15    # or your version
```

**macOS**:
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux**:
```bash
sudo apt install postgresql-15
sudo systemctl start postgresql
```

### Step 3: Create the database

```bash
# Connect to PostgreSQL
psql -U postgres

# Inside psql, run:
CREATE USER vaakai WITH PASSWORD 'vaakai_secure_pass';
CREATE DATABASE vaakai OWNER vaakai;
GRANT ALL PRIVILEGES ON DATABASE vaakai TO vaakai;
\q
```

### Step 4: Create a Python virtual environment

```bash
cd d:\hackathons\SITinnovate2\projectX\vaakai

# Create virtual environment
python -m venv venv

# Activate it
# Windows (Command Prompt):
venv\Scripts\activate

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# macOS / Linux:
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### Step 5: Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs ~50 packages including FastAPI, PyTorch, Transformers, OpenAI SDK, etc.

> ⏱️ **Note**: This may take 5–15 minutes depending on your internet speed. PyTorch is ~2GB.

> **If you get errors** on Windows with `psycopg2-binary`, try:
> ```bash
> pip install psycopg2-binary --only-binary :all:
> ```

> **If PyTorch CUDA issues**: Install CPU-only PyTorch first:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> pip install -r requirements.txt
> ```

---

## 7. Run Database Migrations

This creates all the required tables in PostgreSQL:

```bash
# Make sure your virtual environment is activated
# Make sure PostgreSQL is running

python manage.py
```

Expected output:
```
Running database migrations...
Database migrations completed successfully!
Tables created: customers, call_records, conversation_turns, tickets, fraud_flags, retraining_queue
```

---

## 8. Start the Backend API Server

```bash
# Development mode (with auto-reload)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     ✅ Database initialized
INFO:     ✅ VaakAI Orchestrator ready
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test it**: Open http://localhost:8000/api/v1/health in your browser. You should see:

```json
{
  "status": "healthy",
  "redis": "connected",
  "postgres": "connected"
}
```

---

## 9. Start the Celery Worker

Open a **new terminal** (keep the API server running):

```bash
cd d:\hackathons\SITinnovate2\projectX\vaakai

# Activate virtual environment
.\venv\Scripts\Activate.ps1    # Windows PowerShell
# or
source venv/bin/activate       # macOS/Linux

# Start Celery worker
celery -A core.celery_app worker --loglevel=info
```

Expected output:
```
 -------------- celery@your-machine v5.4.0
--- ***** -----
-- ******* ---- [config]
- *** --- * --- .> app:         vaakai:0x...
 -------------- .> broker:      redis://localhost:6379//
                .> results:     redis://localhost:6379//
[tasks]
  . core.qa_agent.task_post_call_qa

[2026-02-26 10:00:00] Connected to redis://localhost:6379//
[2026-02-26 10:00:00] celery@your-machine ready.
```

> The Celery worker handles async post-call QA scoring in the background.

---

## 10. Set Up & Run the Analytics Dashboard

Open a **new terminal** (keep API + Celery running):

```bash
cd d:\hackathons\SITinnovate2\projectX\vaakai\dashboard

# Install Node.js dependencies
npm install
```

This installs React, Vite, Tailwind CSS, Recharts, etc. Takes ~1-2 minutes.

```bash
# Start the development server
npm run dev
```

Expected output:
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.x.x:3000/
  ➜  press h + enter to show help
```

**Open the dashboard**: Go to http://localhost:3000 in your browser.

You'll see the VaakAI Analytics Dashboard with:
- 📊 Overview page with KPI cards and charts
- 📞 Call History with filters
- 💬 Sentiment & Emotion trends
- 🌐 Language distribution
- 🛡️ Fraud alerts
- ⚙️ Settings & system health

> The dashboard proxies API calls to `http://localhost:8000` automatically.

---

## 11. Verify Everything is Running

You should have **3 terminals** open (or Docker handling everything):

| Terminal | Service | URL | Status Check |
|----------|---------|-----|-------------|
| Terminal 1 | API Server | http://localhost:8000 | `GET /api/v1/health` |
| Terminal 2 | Celery Worker | — | Check terminal logs |
| Terminal 3 | Dashboard | http://localhost:3000 | Open in browser |
| (auto) | Redis | localhost:6379 | `redis-cli ping` |
| (auto) | PostgreSQL | localhost:5432 | `psql -U vaakai -d vaakai` |

### Quick health check

```bash
# Test API health
curl http://localhost:8000/api/v1/health

# Test API initiate call endpoint
curl -X POST http://localhost:8000/api/v1/call/initiate \
  -H "Content-Type: application/json" \
  -d "{\"customer_phone\": \"+919876543210\", \"channel\": \"voice\"}"
```

### API documentation (auto-generated)

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 12. Optional — Ollama for Local LLM

Ollama lets you run Llama 3.1 locally as a fallback when OpenAI is unavailable.

### Install Ollama

1. Download from https://ollama.ai/download
2. Install and run it
3. Pull the Llama 3.1 model:

```bash
# 8B parameter model (~4.7GB) — good for simple queries
ollama pull llama3.1:8b

# 70B parameter model (~40GB) — for complex queries (needs 48GB+ RAM)
ollama pull llama3.1:70b
```

4. Verify it's running:

```bash
curl http://localhost:11434/api/tags
```

The `.env` already has `LLAMA_API_URL=http://localhost:11434` — no change needed.

---

## 13. Optional — LiveKit Server

LiveKit provides real-time WebRTC audio streaming. The Docker setup includes it automatically. For local setup:

1. Download from https://docs.livekit.io/home/self-hosting/local/
2. Run in dev mode:

```bash
livekit-server --dev
```

3. Default runs on port 7880. Update `.env`:

```dotenv
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=your_secret
```

---

## 14. Optional — WhatsApp Webhook Setup

To receive WhatsApp messages, you need a public URL. Use **ngrok** for development:

### Step 1: Install ngrok

```bash
# Download from https://ngrok.com/download
# Or install via npm:
npm install -g ngrok
```

### Step 2: Expose your local API

```bash
ngrok http 8000
```

You'll get a public URL like `https://abc123.ngrok-free.app`.

### Step 3: Configure Meta Webhook

1. Go to https://developers.facebook.com/ → Your App → WhatsApp → Configuration
2. Set **Callback URL** to: `https://abc123.ngrok-free.app/api/v1/whatsapp/webhook`
3. Set **Verify Token** to: `vaakai_verify_token`
4. Subscribe to: `messages`

---

## 15. Running Tests

```bash
# Make sure virtual environment is activated
cd d:\hackathons\SITinnovate2\projectX\vaakai

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_language_detect.py -v
pytest tests/test_intent.py -v
pytest tests/test_emotion.py -v
pytest tests/test_fraud.py -v
pytest tests/test_pii.py -v
pytest tests/test_backchannel.py -v
pytest tests/test_api.py -v

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=html
```

Expected output:
```
tests/test_language_detect.py ........                  [  14%]
tests/test_intent.py ........                           [  29%]
tests/test_emotion.py ........                          [  43%]
tests/test_fraud.py ........                            [  57%]
tests/test_pii.py ........                              [  71%]
tests/test_backchannel.py ......                        [  82%]
tests/test_api.py ......                                [100%]

============== 54 passed in 12.34s ==============
```

---

## 16. Troubleshooting

### ❌ `ModuleNotFoundError: No module named 'xxx'`
```bash
# Make sure you're in the virtual environment
.\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
```

### ❌ `Connection refused` on Redis/PostgreSQL
```bash
# Check if services are running
redis-cli ping                          # Should return PONG
psql -U vaakai -d vaakai -c "SELECT 1" # Should return 1

# If using Docker
docker-compose ps     # Check containers are Up
docker-compose up -d  # Restart if needed
```

### ❌ `OPENAI_API_KEY not set` or `Authentication error`
- Open your `.env` file and verify the key is correct
- Make sure there are no extra spaces or quotes around the key
- Verify your OpenAI account has billing set up

### ❌ `torch` installation fails
```bash
# Install CPU-only version (smaller, no GPU required)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### ❌ Port already in use
```bash
# Find what's using port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change the port
uvicorn api.main:app --port 8001
```

### ❌ Dashboard shows "API Error"
- Make sure the backend is running on port 8000
- The Vite dev server proxies `/api` requests to `localhost:8000`
- Check the browser console (F12) for detailed errors

### ❌ `psycopg2` build fails on Windows
```bash
pip install psycopg2-binary
```

### ❌ Docker build fails
```bash
# Clean rebuild
docker-compose down -v
docker system prune -f
docker-compose up -d --build
```

---

## Summary of Running Services

| Service | URL | Purpose |
|---------|-----|---------|
| **FastAPI Backend** | http://localhost:8000 | Main API server |
| **Swagger Docs** | http://localhost:8000/docs | Interactive API docs |
| **Analytics Dashboard** | http://localhost:3000 | React dashboard |
| **Redis** | localhost:6379 | Session memory |
| **PostgreSQL** | localhost:5432 | Persistent storage |
| **LiveKit** | ws://localhost:7880 | WebRTC audio |
| **Ollama** (optional) | http://localhost:11434 | Local LLM |

---

**🎉 You're all set! VaakAI is running and ready to handle multilingual voice conversations.**

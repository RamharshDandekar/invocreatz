# 🎙️ VaakAI — Multilingual AI Voice Chatbot

> **Vaak** (वाक्) — Sanskrit for "voice, speech". A production-grade, voice-first AI chatbot replacing legacy IVR systems with natural, multilingual conversations across 22+ Indian languages.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DPDPA Compliant](https://img.shields.io/badge/DPDPA-Compliant-brightgreen.svg)]()

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        VaakAI Platform                           │
├──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│  Voice   │ WhatsApp │  Widget  │   API    │  Analytics Dashboard │
│ (LiveKit)│ (Meta)   │  (JS)   │ (REST)   │   (React + Vite)    │
├──────────┴──────────┴──────────┴──────────┴─────────────────────┤
│                     FastAPI Gateway (uvicorn)                    │
├─────────┬──────────┬──────────┬───────────┬─────────────────────┤
│  STT    │ Language │   NLU    │  Fraud    │   Backchannel       │
│AI4Bharat│ Detect   │Intent+   │ Detector  │   Engine            │
│Deepgram │ IndicLID │Emotion   │ IF+LSTM   │                     │
├─────────┴──────────┴──────────┴───────────┴─────────────────────┤
│              LLM Router (GPT-4o / Llama 3.1)                    │
├─────────┬──────────┬──────────┬───────────┬─────────────────────┤
│  TTS    │   CRM    │   ERP    │ Compliance│   QA Agent          │
│Eleven   │Salesforce│  SAP     │PII Redact │ Post-call scoring   │
│Labs +   │Zoho,     │  Odoo    │DPDPA      │ Celery async        │
│AI4Bharat│Freshdesk │          │Consent    │                     │
├─────────┴──────────┴──────────┴───────────┴─────────────────────┤
│          Redis (Sessions)  │  PostgreSQL (Persistent)            │
└────────────────────────────┴─────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **22+ Indian Languages** | Hindi, English, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, and more via AI4Bharat |
| **< 500ms Latency** | End-to-end voice response under 500ms with streaming STT/TTS |
| **Real-time Fraud Detection** | Isolation Forest + LSTM + 16 social engineering pattern detectors |
| **Code-Switching** | Seamless handling of Hinglish and mixed-language conversations |
| **DPDPA Compliance** | PII redaction (Aadhaar, PAN, GSTIN), consent management, right-to-erasure |
| **Omnichannel** | Voice (LiveKit/WebRTC), WhatsApp (Meta Cloud API), Web Widget |
| **CRM Integration** | Salesforce, Zoho CRM, Freshdesk with automatic fallback |
| **ERP Integration** | SAP (OData), Odoo (JSON-RPC) with Redis caching |
| **Post-Call QA** | GPT-4o-mini scoring on resolution, tone, accuracy, compliance, CSAT |
| **Analytics Dashboard** | React dashboard with real-time charts (Recharts) |

---

## Project Structure

```
vaakai/
├── config.py                  # Pydantic settings (env-based)
├── manage.py                  # Database migration runner
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Production container
├── docker-compose.yml         # Multi-service orchestration
├── .env.example               # Environment template
│
├── models/
│   ├── database.py            # SQLAlchemy ORM models
│   └── schemas.py             # Pydantic request/response schemas
│
├── memory/
│   ├── redis_client.py        # Session memory, omnichannel context
│   └── postgres_client.py     # Persistent storage repositories
│
├── core/
│   ├── orchestrator.py        # Main pipeline conductor
│   ├── language_detect.py     # IndicLID + Unicode script detection
│   ├── backchannel.py         # Multilingual filler responses
│   ├── fraud_detector.py      # Isolation Forest + pattern matching
│   ├── qa_agent.py            # Post-call QA scoring (Celery)
│   ├── celery_app.py          # Celery configuration
│   │
│   ├── stt/
│   │   ├── ai4bharat.py       # AI4Bharat IndicASR (22 languages)
│   │   └── deepgram.py        # Deepgram Nova-3 (English fallback)
│   │
│   ├── nlu/
│   │   ├── intent.py          # MuRIL BERT intent classifier (24 intents)
│   │   └── emotion.py         # BERT-BiLSTM emotion detector (9 labels)
│   │
│   ├── llm/
│   │   ├── openai_client.py   # OpenAI GPT-4o / 4o-mini
│   │   ├── llama_client.py    # Ollama / Llama 3.1
│   │   └── router.py          # Complexity-based LLM routing
│   │
│   ├── tts/
│   │   ├── elevenlabs.py      # ElevenLabs Flash v2
│   │   └── indic_tts.py       # AI4Bharat Indic TTS
│   │
│   └── tools/
│       ├── __init__.py        # Unified tool registry
│       ├── crm_tools.py       # CRM function calling tools
│       ├── erp_tools.py       # ERP function calling tools
│       └── whatsapp_tools.py  # WhatsApp messaging tools
│
├── compliance/
│   ├── pii_redactor.py        # Presidio + Indian PII patterns
│   └── consent_manager.py     # DPDPA consent management
│
├── integrations/
│   ├── crm/
│   │   ├── salesforce.py      # Salesforce OAuth + SOQL
│   │   ├── zoho.py            # Zoho CRM REST API
│   │   └── freshdesk.py       # Freshdesk API v2
│   ├── erp/
│   │   ├── sap.py             # SAP OData with Redis cache
│   │   └── odoo.py            # Odoo JSON-RPC
│   └── whatsapp/
│       └── meta_cloud.py      # Meta WhatsApp Cloud API
│
├── api/
│   ├── main.py                # FastAPI app factory + middleware
│   ├── call.py                # Call routes + WebSocket + WhatsApp webhook
│   ├── crm.py                 # CRM proxy routes
│   ├── analytics.py           # Analytics & reporting routes
│   └── admin.py               # Admin & compliance routes
│
├── static/
│   └── widget.js              # Embeddable JS chat/voice widget
│
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   ├── test_language_detect.py
│   ├── test_intent.py
│   ├── test_emotion.py
│   ├── test_fraud.py
│   ├── test_pii.py
│   ├── test_backchannel.py
│   └── test_api.py
│
└── dashboard/                 # React Analytics Dashboard
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── index.css
        ├── App.jsx
        ├── api.js
        ├── components/
        │   ├── Sidebar.jsx
        │   └── StatCard.jsx
        └── pages/
            ├── Overview.jsx
            ├── Calls.jsx
            ├── Sentiment.jsx
            ├── Languages.jsx
            ├── Fraud.jsx
            └── Settings.jsx
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for dashboard)
- Docker & Docker Compose
- Redis 7+
- PostgreSQL 15+

### 1. Clone & Configure

```bash
cd vaakai
cp .env.example .env
# Edit .env with your API keys
```

### 2. Docker Compose (Recommended)

```bash
docker-compose up -d
```

This starts 5 services:
- **vaakai-api** — FastAPI on port 8000
- **redis** — Session store on port 6379
- **postgres** — Database on port 5432
- **livekit** — WebRTC server on port 7880
- **celery-worker** — Async task processing

### 3. Local Development

```bash
# Backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py             # Run migrations
uvicorn api.main:app --reload --port 8000

# Dashboard
cd dashboard
npm install
npm run dev                  # http://localhost:3000
```

### 4. Run Tests

```bash
pytest tests/ -v
```

---

## API Endpoints

### Call Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/call/initiate` | Start a new call session |
| POST | `/api/v1/call/{id}/audio` | Send audio chunk for processing |
| POST | `/api/v1/call/{id}/text` | Send text message (WhatsApp/widget) |
| POST | `/api/v1/call/{id}/end` | End call and trigger QA |
| GET | `/api/v1/call/{id}/status` | Get call session status |
| WS | `/api/v1/call/ws/{id}` | WebSocket streaming endpoint |

### WhatsApp
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/whatsapp/webhook` | Incoming message webhook |
| GET | `/api/v1/whatsapp/webhook` | Webhook verification |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/summary` | KPI summary (calls, CSAT, etc.) |
| GET | `/api/v1/analytics/calls` | Call history list |
| GET | `/api/v1/analytics/sentiment-trends` | Sentiment over time |
| GET | `/api/v1/analytics/language-distribution` | Language breakdown |
| GET | `/api/v1/analytics/top-intents` | Most common intents |
| GET | `/api/v1/analytics/fraud-alerts` | Fraud detection alerts |
| GET | `/api/v1/analytics/performance` | Latency & performance metrics |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/sessions` | List active sessions |
| POST | `/api/v1/admin/sessions/{id}/end` | Force-end session |
| GET | `/api/v1/admin/retrain-queue` | Model retrain queue |
| DELETE | `/api/v1/admin/dpdpa/customer/{phone}` | Right to erasure |

---

## Environment Variables

Key configuration (see `.env.example` for full list):

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI GPT-4o API key |
| `AI4BHARAT_API_KEY` | AI4Bharat inference API key |
| `DEEPGRAM_API_KEY` | Deepgram Nova-3 key |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS key |
| `REDIS_URL` | Redis connection string |
| `DATABASE_URL` | PostgreSQL connection string |
| `WHATSAPP_TOKEN` | Meta WhatsApp access token |
| `SALESFORCE_CLIENT_ID` | Salesforce OAuth client |
| `SAP_BASE_URL` | SAP OData endpoint |

---

## Voice Pipeline Flow

```
User Speaks
    │
    ▼
┌─────────────────┐
│   STT Engine    │  AI4Bharat IndicASR (22 langs) / Deepgram (English)
│   < 150ms       │
└────────┬────────┘
         │
    ▼────┴────▼
┌────────┐ ┌──────────┐
│Language │ │Backchannel│  "Hmm...", "Achha..."
│Detect  │ │Engine     │  Sent immediately
└────┬───┘ └──────────┘
     │
     ▼ (parallel)
┌────────┐ ┌────────┐ ┌────────┐
│Intent  │ │Emotion │ │Fraud   │
│Classify│ │Detect  │ │Detect  │
│24 types│ │9 labels│ │16 ptns │
└────┬───┘ └────┬───┘ └────┬───┘
     │          │          │
     ▼──────────▼──────────▼
┌─────────────────────────────┐
│   LLM Router                │
│   Simple → GPT-4o-mini      │
│   Complex → GPT-4o          │
│   + Tool Calling (CRM/ERP)  │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   TTS Engine                │
│   English → ElevenLabs      │
│   Indian → AI4Bharat        │
│   < 200ms                   │
└─────────────────────────────┘
             │
             ▼
        User Hears
```

---

## Embeddable Widget

Add VaakAI to any website with one script tag:

```html
<script src="https://your-domain.com/static/widget.js"></script>
<script>
  VaakAI.init({
    serverUrl: 'https://api.your-domain.com',
    position: 'bottom-right',
    primaryColor: '#6C63FF',
    language: 'hi',
    greeting: 'नमस्ते! मैं VaakAI हूँ। आपकी कैसे मदद कर सकता हूँ?',
    enableVoice: true,
  });
</script>
```

---

## Supported Languages

| # | Language | Code | STT | TTS | NLU |
|---|----------|------|-----|-----|-----|
| 1 | Hindi | hi | ✅ | ✅ | ✅ |
| 2 | English | en | ✅ | ✅ | ✅ |
| 3 | Bengali | bn | ✅ | ✅ | ✅ |
| 4 | Tamil | ta | ✅ | ✅ | ✅ |
| 5 | Telugu | te | ✅ | ✅ | ✅ |
| 6 | Marathi | mr | ✅ | ✅ | ✅ |
| 7 | Gujarati | gu | ✅ | ✅ | ✅ |
| 8 | Kannada | kn | ✅ | ✅ | ✅ |
| 9 | Malayalam | ml | ✅ | ✅ | ✅ |
| 10 | Punjabi | pa | ✅ | ✅ | ✅ |
| 11 | Odia | or | ✅ | ✅ | — |
| 12 | Assamese | as | ✅ | ✅ | — |
| 13-22 | Urdu, Sanskrit, Nepali, Sindhi, Kashmiri, Dogri, Manipuri, Santali, Maithili, Konkani | — | ✅ | — | — |

---

## Compliance & Security

- **PII Redaction**: Aadhaar (12-digit), PAN, GSTIN, UPI IDs, IFSC codes, bank accounts, credit cards, emails, phone numbers — all masked before LLM processing and logging
- **DPDPA Consent**: Multilingual consent prompts, affirmative opt-in, right to erasure, purpose-limited data processing
- **Fraud Detection**: Real-time monitoring with 16 social engineering patterns, behavioral anomaly detection, automatic call escalation
- **Audit Trail**: Every conversation turn stored with timestamps, PII-redacted transcripts, and consent records

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | FastAPI + uvicorn |
| Real-time Audio | LiveKit (WebRTC) |
| STT | AI4Bharat IndicASR, Deepgram Nova-3 |
| Language Detection | IndicLID (AI4Bharat) |
| Intent Classification | MuRIL BERT (google/muril-base-cased) |
| Emotion Detection | BERT-BiLSTM |
| Fraud Detection | Isolation Forest + LSTM |
| LLM | OpenAI GPT-4o / Llama 3.1 via Ollama |
| TTS | ElevenLabs Flash v2, AI4Bharat TTS |
| Session Store | Redis 7 |
| Database | PostgreSQL 15 + SQLAlchemy (async) |
| PII | Microsoft Presidio + custom patterns |
| Task Queue | Celery + Redis |
| CRM | Salesforce, Zoho, Freshdesk |
| ERP | SAP (OData), Odoo (JSON-RPC) |
| Messaging | Meta WhatsApp Cloud API |
| Dashboard | React 18 + Vite 5 + Tailwind CSS + Recharts |
| Deployment | Docker + Docker Compose |

---

## License

MIT License — Built for SIT Innovate 2025 Hackathon.

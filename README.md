<div align="center">

<br/>

```
 █████╗ ██████╗ ██╗ █████╗
██╔══██╗██╔══██╗██║██╔══██╗
███████║██████╔╝██║███████║
██╔══██║██╔══██╗██║██╔══██║
██║  ██║██║  ██║██║██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
```

# ARIA — Autonomous Reply & Intelligence Assistant

**A fully self-hosted, AI-powered personal automation backend that unifies your entire digital life into a single Telegram chat.**

<br/>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA3-F55036?style=for-the-badge&logo=data:image/png;base64,&logoColor=white)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](./LICENSE)

<br/>

> *"Instead of jumping between WhatsApp, Gmail, Slack, Discord, Spotify, Notion, and GitHub — ARIA brings everything to one place: your Telegram chat."*

<br/>

---

</div>

## 📑 Table of Contents

- [Abstract](#-abstract)
- [The Problem ARIA Solves](#-the-problem-aria-solves)
- [Key Features](#-key-features)
- [System Architecture Overview](#-system-architecture-overview)
- [Component Deep Dive](#-component-deep-dive)
- [LLM Pipeline — How Intelligence Works](#-llm-pipeline--how-intelligence-works)
- [Database Architecture & Pipeline](#-database-architecture--pipeline)
- [Communication Flow — Inbound](#-communication-flow--inbound)
- [Communication Flow — Outbound](#-communication-flow--outbound)
- [Integration Map](#-integration-map)
- [Tech Stack](#-tech-stack)
- [Folder Structure](#-folder-structure)
- [Infrastructure — Docker Services](#-infrastructure--docker-services)
- [Quick Start](#-quick-start)
- [Environment Variables](#-environment-variables)
- [How Each Piece Connects](#-how-each-piece-connects)
- [Contributing](#-contributing)

---

## 🧠 Abstract

**ARIA** (Autonomous Reply & Intelligence Assistant) is a self-hosted, multi-agent AI backend designed to eliminate digital context-switching. It acts as a bidirectional intelligence bridge between the user and their entire digital ecosystem.

At its core, ARIA is a webhook-ingestion + intent-parsing engine. It:

1. **Receives** events from Gmail (via Google Pub/Sub), WhatsApp (via Baileys WebSocket), Slack, Discord, and SMS webhooks.
2. **Classifies** every incoming message using Groq's LLaMA 3 model, scoring it for urgency, importance, and tone.
3. **Filters** noise — only messages above a configurable `IMPORTANCE_THRESHOLD` (1–10) trigger a push notification.
4. **Routes** user commands from Telegram to a structured intent parser, then dispatches actions to the correct service (reply via Gmail, post to Notion, control Spotify, etc.).
5. **Persists** everything — messages, intents, expenses, habits, reminders — in PostgreSQL, using MinIO for media/voice note storage.

The result: a single Telegram bot that manages your entire digital life, powered by a real LLM, running entirely on your own hardware.

---

## 💡 The Problem ARIA Solves

```
WITHOUT ARIA                        WITH ARIA
─────────────────────────────────   ─────────────────────────────────
📱 WhatsApp  → open app            🤖 Telegram Bot (1 interface)
📧 Gmail     → open app             │
💬 Slack     → open app             ├── 📩 WhatsApp messages
🎮 Discord   → open app             ├── 📧 Gmail (scored & triaged)
📓 Notion    → open browser         ├── 💬 Slack threads
🎵 Spotify   → open app             ├── 🎮 Discord DMs
💻 GitHub    → open browser         ├── 📓 Notion tasks
📊 Finances  → spreadsheet          ├── 🎵 Spotify controls
                                    ├── 💰 Expense tracking
Context switching = 8 apps          └── 📅 Calendar & reminders
Time lost = significant
                                    Context switching = 0 apps
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🗂 **Unified Smart Inbox** | Gmail, WhatsApp, Discord, Slack, SMS → one Telegram chat |
| 🧮 **AI Importance Scoring** | Every message scored 1–10 for urgency; only high-priority ones alert you |
| ✍️ **Tone-Aware Replies** | Prefix a reply with `professional:` or `casual:` — ARIA reformats for the target platform |
| 🎙 **Voice Note Transcription** | Inbound voice messages auto-transcribed via Groq Whisper |
| 🌅 **Morning Briefing** | Daily digest: weather + calendar + urgent emails + stocks/crypto + HN stories |
| 💬 **Natural Language Commands** | "Remind me to call John tomorrow", "Log $50 food expense", "What's my schedule?" |
| 📊 **Expense Tracking** | Log and summarize financial transactions via natural language |
| ✅ **Habit Tracking** | Track daily habits and receive streak reminders |
| 🔔 **Keyword Alerts** | Monitor RSS feeds and any source for specific keywords |
| 🔒 **Privacy First** | 100% self-hosted. No cloud services own your data. PostgreSQL stays on your machine |
| 🐳 **One-Command Deploy** | Full `docker compose up -d` setup with zero manual config |

---

## 🏗 System Architecture Overview

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ARIA — FULL SYSTEM ARCHITECTURE                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   EXTERNAL WORLD            ARIA CORE                    DATA LAYER          ║
║   ─────────────             ─────────                    ──────────          ║
║                                                                              ║
║   ┌─────────────┐           ┌────────────┐               ┌──────────────┐   ║
║   │  Telegram   │◄─────────►│   Nginx    │               │  PostgreSQL  │   ║
║   │  (Primary   │  HTTPS    │  (Proxy /  │               │  (Primary    │   ║
║   │  Interface) │  Webhook  │  Ingress)  │               │  Database)   │   ║
║   └─────────────┘           └─────┬──────┘               └──────▲───────┘   ║
║                                   │                              │           ║
║   ┌─────────────┐           ┌─────▼──────┐               ┌──────┴───────┐   ║
║   │  Gmail      │──Webhook─►│  FastAPI   │◄─────────────►│    Redis 7   │   ║
║   │  (Pub/Sub)  │           │  Web       │  Async DB     │  (Job Queue  ║   ║
║   └─────────────┘           │  Server    │  Session      │   + Cache)   │   ║
║                             └─────┬──────┘               └──────▲───────┘   ║
║   ┌─────────────┐                 │ Enqueue                      │           ║
║   │  WhatsApp   │◄──REST──────────┤ Jobs                  ┌──────┴───────┐   ║
║   │  (Baileys   │                 │                        │   ARQ Task   │   ║
║   │   Bridge)   │                 └──────────────────────► │   Worker     │   ║
║   └─────────────┘                                          └──────┬───────┘   ║
║                                                                   │           ║
║   ┌─────────────┐           ┌────────────┐               ┌──────▼───────┐   ║
║   │  Slack      │──Webhook─►│   Groq     │◄──────────────│   MinIO      │   ║
║   │  Discord    │           │   LLM      │    LLM Calls  │  (Object     │   ║
║   │  SMS        │           │  (LLaMA 3  │               │  Storage)    │   ║
║   └─────────────┘           │  + Whisper)│               └──────────────┘   ║
║                             └────────────┘                                   ║
║                                                                              ║
║   ─── Third-Party APIs ───────────────────────────────────────────────────   ║
║   Notion · GitHub · Spotify · Weather · Stock/Crypto APIs · HackerNews RSS   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 🔬 Component Deep Dive

### 1. Nginx (Reverse Proxy / Ingress)

Nginx is the single public-facing door to ARIA. It terminates HTTPS, routes incoming webhook requests (from Telegram, Gmail, Slack, etc.) to the FastAPI server, and rate-limits traffic.

```
Internet ──HTTPS──► Nginx :80 ──HTTP──► FastAPI :8000
                     │
                     └── Validates Host headers
                     └── Forwards /webhook/* routes
                     └── Serves static assets if any
```

**File:** `nginx.conf`

---

### 2. FastAPI Server (`api/`)

The brain of ARIA's request handling. It:
- Validates incoming webhook signatures (Telegram, Slack `X-Slack-Signature`, Gmail Pub/Sub JWT)
- Deserializes payloads through **Adapters** into a normalized ARIA message format
- Enqueues background jobs into Redis via **ARQ**
- Returns `200 OK` immediately (webhook best practice — never block on webhook receipt)

```
FastAPI Routes (api/routes/)
├── /webhook/telegram    → Telegram bot updates
├── /webhook/gmail       → Gmail Pub/Sub push
├── /webhook/whatsapp    → Baileys internal bridge
├── /webhook/slack       → Slack Event API
├── /webhook/discord     → Discord gateway events
└── /internal/trigger    → Cron-triggered briefings
```

---

### 3. ARQ Task Worker (`api/workers/`)

An async Python worker that pulls jobs from Redis and executes them. It's the workhorse that:
- Calls the Groq LLM for classification and intent parsing
- Fetches full message bodies from Gmail API
- Downloads and transcribes voice notes from MinIO via Whisper
- Writes processed results to PostgreSQL
- Sends formatted Telegram notifications

```
Worker Job Types:
├── process_inbound_message   → LLM classify → DB store → Telegram notify
├── process_outbound_command  → LLM parse_intent → handler → external service
├── send_morning_briefing     → aggregate sources → format → Telegram send
├── follow_up_reminder        → check DB → send nudge if needed
└── habit_check               → query habit table → send streak update
```

---

### 4. Baileys Bridge (`baileys/`)

A dedicated **Node.js / Express** microservice that maintains the WhatsApp Web multi-device WebSocket session. It:
- Holds the QR-authenticated WhatsApp session in a persistent Docker volume (`baileys_session`)
- Receives inbound WhatsApp messages and POSTs them to the FastAPI `/webhook/whatsapp` endpoint
- Accepts outbound POST requests from the FastAPI `whatsapp_service.py` to send replies

```
WhatsApp Cloud  ←──WebSocket──►  Baileys (Node.js :3001)
                                        │
                     ┌──────────────────┤
                     │ Inbound          │ Outbound
                     ▼                  ▼
              FastAPI POST        FastAPI → POST /send
              /webhook/whatsapp   → Baileys → WA Cloud
```

**Key files:** `baileys/index.js`, `baileys/Dockerfile`

---

### 5. Groq LLM Engine (`api/llm/`)

ARIA uses two Groq models:

| Model | Usage |
|---|---|
| `llama-3.3-70b-versatile` | Message classification, intent parsing, reply reformatting |
| `whisper-large-v3` | Voice note transcription |

The LLM module exposes two primary functions:

**`classify(message)`** — Scores an inbound message and returns structured JSON:
```json
{
  "importance": 8,
  "urgency": "high",
  "summary": "Client asking for invoice by EOD",
  "tone": "professional",
  "suggested_reply": "I'll send it over within the hour."
}
```

**`parse_intent(command)`** — Converts a natural language command to a structured action:
```json
{
  "intent": "reply",
  "platform": "whatsapp",
  "contact": "John",
  "tone": "casual",
  "body": "Sure, see you at 6!"
}
```

---

### 6. Handlers (`api/handlers/`)

Each intent maps to a dedicated handler:

```
Intent Router
├── reply_handler.py      → Reformat text → route to correct service
├── expense_handler.py    → Parse amount/category → save to DB
├── schedule_handler.py   → Parse datetime → Google Calendar API
├── habit_handler.py      → Mark habit complete → update streak in DB
├── reminder_handler.py   → Store reminder → schedule ARQ job
├── summary_handler.py    → Query DB → format digest → Telegram
└── briefing_handler.py   → Aggregate weather/email/stocks → send
```

---

### 7. Services (`api/services/`)

Thin API client wrappers for each external platform:

| Service File | External API | Auth Method |
|---|---|---|
| `gmail_service.py` | Google Gmail API | OAuth 2.0 Refresh Token |
| `whatsapp_service.py` | Baileys REST | Internal HTTP |
| `slack_service.py` | Slack Web API | Bot Token |
| `discord_service.py` | Discord Bot API | Bot Token |
| `notion_service.py` | Notion API | Integration Token |
| `github_service.py` | GitHub REST API | Personal Access Token |
| `spotify_service.py` | Spotify Web API | OAuth 2.0 |
| `telegram_service.py` | Telegram Bot API | Bot Token |
| `sms_service.py` | SMS Gateway | API Token |

---

## 🤖 LLM Pipeline — How Intelligence Works

```
┌─────────────────────────────────────────────────────────────┐
│                    GROQ LLM PIPELINE                         │
└─────────────────────────────────────────────────────────────┘

  INBOUND CLASSIFICATION PIPELINE
  ─────────────────────────────────────────────────────────────

  Raw Message Arrives
         │
         ▼
  ┌─────────────────┐     Adapter normalizes
  │  Vendor Webhook │ ──► vendor-specific format
  │  Payload (raw)  │     into ARIA Message schema
  └─────────────────┘
         │
         ▼
  ┌─────────────────────────────────────────────────────────┐
  │  ARIA Message Schema                                     │
  │  { source, contact, body, timestamp, media_url? }        │
  └─────────────────────────────────────────────────────────┘
         │
         ▼
  ┌───────────────────┐
  │  Groq API Call    │   Model: llama-3.3-70b-versatile
  │  classify()       │   Prompt: System role + message body
  └───────────────────┘   Max tokens: ~200
         │
         ▼
  ┌───────────────────────────────────────────────────────────┐
  │  Classification Result (JSON)                              │
  │  {                                                         │
  │    "importance": 1-10,    ← Core triage score              │
  │    "urgency": "low|med|high",                              │
  │    "summary": "...",      ← Used in Telegram notification  │
  │    "tone": "...",         ← Used to style reply suggestions│
  │    "suggested_reply": "..." ← Optional pre-written reply   │
  │  }                                                         │
  └───────────────────────────────────────────────────────────┘
         │
         ├──── importance < THRESHOLD ──► Stored silently in DB (no notification)
         │
         └──── importance ≥ THRESHOLD ──► Telegram push notification sent


  OUTBOUND INTENT PIPELINE
  ─────────────────────────────────────────────────────────────

  User Types in Telegram
         │
         ▼
  "professional: I can't make it to the meeting"
  or
  "remind me to call John tomorrow at 3pm"
  or
  "play something chill on Spotify"
         │
         ▼
  ┌───────────────────┐
  │  Groq API Call    │   Model: llama-3.3-70b-versatile
  │  parse_intent()   │   Returns structured JSON intent
  └───────────────────┘
         │
         ▼
  ┌───────────────────────────────────────┐
  │  Intent JSON                           │
  │  {                                     │
  │    "intent": "reply|remind|expense     │
  │               |habit|schedule|play     │
  │               |summary|note",          │
  │    "platform": "whatsapp|gmail|...",   │
  │    "params": { ... intent-specific }   │
  │  }                                     │
  └───────────────────────────────────────┘
         │
         ▼
  ┌───────────────────┐
  │   Intent Router   │ ──► Dispatches to correct Handler
  └───────────────────┘
         │
    ┌────┴──────────────────────────┐
    │                               │
    ▼                               ▼
  Handler executes          DB updated
  (e.g. send Gmail reply)   (intent logged)
    │
    ▼
  Confirmation sent to Telegram


  VOICE NOTE PIPELINE
  ─────────────────────────────────────────────────────────────

  Voice Note Received (WhatsApp / Telegram)
         │
         ▼
  Download audio file → Upload to MinIO (aria-storage bucket)
         │
         ▼
  ┌───────────────────┐
  │  Groq Whisper API │   Model: whisper-large-v3
  │  Transcription    │   Input: audio file URL from MinIO
  └───────────────────┘
         │
         ▼
  Transcript text → classify() pipeline → Telegram notification
  (including transcription text in the message)
```

---

## 🗄 Database Architecture & Pipeline

ARIA uses **PostgreSQL 16** with **SQLAlchemy (Async)** as the ORM. Schema migrations are handled by **Alembic**.

### Database Schema

```
╔══════════════════════════════════════════════════════════════════════╗
║                     ARIA — POSTGRESQL SCHEMA                         ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  ┌─────────────────────┐       ┌─────────────────────────────────┐  ║
║  │      messages        │       │           intents                │  ║
║  ├─────────────────────┤       ├─────────────────────────────────┤  ║
║  │ id (UUID PK)         │◄──┐   │ id (UUID PK)                    │  ║
║  │ source (varchar)     │   │   │ user_message (text)             │  ║
║  │ contact (varchar)    │   │   │ parsed_intent (jsonb)           │  ║
║  │ body (text)          │   │   │ handler_result (jsonb)          │  ║
║  │ summary (text)       │   │   │ executed_at (timestamptz)       │  ║
║  │ importance (int)     │   │   │ success (boolean)               │  ║
║  │ urgency (varchar)    │   └───│ message_id (UUID FK)            │  ║
║  │ tone (varchar)       │       └─────────────────────────────────┘  ║
║  │ is_read (boolean)    │                                             ║
║  │ is_replied (boolean) │       ┌─────────────────────────────────┐  ║
║  │ media_url (text)     │       │           expenses               │  ║
║  │ created_at (tz)      │       ├─────────────────────────────────┤  ║
║  └─────────────────────┘       │ id (UUID PK)                    │  ║
║                                 │ amount (numeric)                │  ║
║  ┌─────────────────────┐       │ category (varchar)              │  ║
║  │      reminders       │       │ description (text)              │  ║
║  ├─────────────────────┤       │ logged_at (timestamptz)         │  ║
║  │ id (UUID PK)         │       └─────────────────────────────────┘  ║
║  │ body (text)          │                                             ║
║  │ remind_at (tz)       │       ┌─────────────────────────────────┐  ║
║  │ is_sent (boolean)    │       │           habits                 │  ║
║  │ created_at (tz)      │       ├─────────────────────────────────┤  ║
║  └─────────────────────┘       │ id (UUID PK)                    │  ║
║                                 │ name (varchar)                  │  ║
║  ┌─────────────────────┐       │ streak (int)                    │  ║
║  │   follow_up_queue    │       │ last_completed (date)           │  ║
║  ├─────────────────────┤       │ created_at (timestamptz)        │  ║
║  │ id (UUID PK)         │       └─────────────────────────────────┘  ║
║  │ contact (varchar)    │                                             ║
║  │ platform (varchar)   │       ┌─────────────────────────────────┐  ║
║  │ due_at (tz)          │       │        briefing_cache            │  ║
║  │ is_done (boolean)    │       ├─────────────────────────────────┤  ║
║  │ message_id (UUID FK) │       │ id (UUID PK)                    │  ║
║  └─────────────────────┘       │ briefing_date (date)            │  ║
║                                 │ content (jsonb)                 │  ║
║                                 │ sent_at (timestamptz)           │  ║
║                                 └─────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### Database Write Pipeline

```
  INBOUND MESSAGE → DATABASE
  ──────────────────────────────────────────────────────────

  Webhook Received
       │
       ▼
  ARQ Worker picks up job
       │
       ▼
  LLM classify() called
       │
       ▼
  ┌──────────────────────────────────────────┐
  │  SQLAlchemy Async Session                 │
  │                                           │
  │  async with session.begin():              │
  │    msg = Message(                         │
  │      source   = "whatsapp",               │
  │      contact  = "+919876543210",          │
  │      body     = "Hey, meeting at 3?",    │
  │      summary  = "Meeting request at 3",  │
  │      importance = 7,                      │
  │      urgency    = "high",                 │
  │      is_read    = False,                  │
  │      created_at = utcnow()               │
  │    )                                      │
  │    session.add(msg)                       │
  └──────────────────────────────────────────┘
       │
       ▼
  PostgreSQL commit (ACID guaranteed)
       │
       ▼
  Redis: original job acknowledged & removed


  OUTBOUND COMMAND → DATABASE
  ──────────────────────────────────────────────────────────

  User sends command via Telegram
       │
       ▼
  parse_intent() result stored in `intents` table
       │
       ├──── intent = "expense" ──► Write to `expenses` table
       │
       ├──── intent = "remind"  ──► Write to `reminders` table
       │                            + Schedule ARQ delayed job
       │
       ├──── intent = "habit"   ──► Update `habits` table streak
       │
       └──── intent = "reply"   ──► Set is_replied=True on message
                                    Log to `intents` table
```

### Alembic Migration Pipeline

```
Developer changes SQLAlchemy model
          │
          ▼
  alembic revision --autogenerate -m "add habits table"
          │
          ▼
  New migration script generated in api/db/migrations/versions/
          │
          ▼
  alembic upgrade head   ← Applied automatically on container start
          │
          ▼
  PostgreSQL schema updated
```

---

## 📥 Communication Flow — Inbound

```
╔════════════════════════════════════════════════════════════════════╗
║                    INBOUND MESSAGE FLOW                             ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                     ║
║  Step 1: INGESTION                                                  ║
║  ─────────────────────────────────────────────────────────────     ║
║                                                                     ║
║   Gmail        ──Pub/Sub Push Webhook──►  Nginx                    ║
║   WhatsApp     ──Baileys WebSocket──────► Baileys ──POST──► Nginx  ║
║   Slack        ──Event API Webhook──────► Nginx                    ║
║   Discord      ──Bot Gateway Events────► Nginx                     ║
║   SMS          ──Gateway Webhook───────► Nginx                     ║
║                                              │                      ║
║                                              ▼                      ║
║  Step 2: VALIDATION                   FastAPI Route                 ║
║  ──────────────────────────────  ┌──────────────────────┐         ║
║                                  │ Verify webhook secret │         ║
║                                  │ or signature header   │         ║
║                                  │ Return 200 OK fast    │         ║
║                                  └──────────┬───────────┘         ║
║                                             │                      ║
║  Step 3: NORMALIZATION                      ▼                      ║
║  ─────────────────────────────   ┌──────────────────────┐         ║
║                                  │ Adapter Layer         │         ║
║                                  │ (api/adapters/)       │         ║
║                                  │                       │         ║
║  Gmail payload  → gmail_adapter  │ Vendor JSON           │         ║
║  Slack payload  → slack_adapter  │     │                 │         ║
║  WA payload    → wa_adapter      │     ▼                 │         ║
║                                  │ ARIA Message Schema   │         ║
║                                  └──────────┬───────────┘         ║
║                                             │                      ║
║  Step 4: QUEUING                            ▼                      ║
║  ─────────────────────────────   ┌──────────────────────┐         ║
║                                  │ arq.enqueue_job(      │         ║
║                                  │  "process_inbound",   │         ║
║                                  │  message=msg          │         ║
║                                  │ )                     │         ║
║                                  └──────────┬───────────┘         ║
║                                             │                      ║
║  Step 5: PROCESSING (async)                 ▼                      ║
║  ─────────────────────────────   ┌──────────────────────┐         ║
║                                  │ ARQ Worker            │         ║
║                                  │ process_inbound_msg() │         ║
║                                  │                       │         ║
║                                  │ 1. Fetch full body    │         ║
║                                  │    (Gmail API if mail)│         ║
║                                  │ 2. Download media     │         ║
║                                  │    → MinIO store      │         ║
║                                  │ 3. Whisper transcribe │         ║
║                                  │    (if voice note)    │         ║
║                                  │ 4. Groq classify()    │         ║
║                                  │ 5. Save to PostgreSQL │         ║
║                                  └──────────┬───────────┘         ║
║                                             │                      ║
║  Step 6: NOTIFICATION                       ▼                      ║
║  ─────────────────────────────   importance ≥ THRESHOLD?           ║
║                                        │           │               ║
║                                       YES          NO              ║
║                                        │           │               ║
║                                        ▼           ▼               ║
║                                   Telegram      Stored             ║
║                                   Push Msg      Silently           ║
║                                   with Reply    in DB              ║
║                                   Button                           ║
╚════════════════════════════════════════════════════════════════════╝
```

---

## 📤 Communication Flow — Outbound

```
╔════════════════════════════════════════════════════════════════════╗
║                    OUTBOUND COMMAND FLOW                            ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                     ║
║  User types in Telegram:                                            ║
║  ┌──────────────────────────────────────────────────────────────┐  ║
║  │  "professional: Sorry, I'll need to reschedule our 3pm call" │  ║
║  │  "remind me to follow up with Priya in 3 days"               │  ║
║  │  "spent $40 on lunch, category: food"                        │  ║
║  │  "what's my schedule today?"                                  │  ║
║  │  "play lo-fi hip hop on Spotify"                              │  ║
║  └──────────────────────────────────────────────────────────────┘  ║
║                              │                                      ║
║  Step 1: RECEIVE             ▼                                      ║
║  ─────────── Telegram Webhook → FastAPI /webhook/telegram           ║
║              Validate bot token + user ID whitelist                 ║
║              Enqueue: process_outbound_command job                  ║
║                              │                                      ║
║  Step 2: PARSE INTENT        ▼                                      ║
║  ───────────────── ARQ Worker → Groq parse_intent()                 ║
║                                                                     ║
║   Input: "professional: Sorry, I'll need to reschedule..."         ║
║   Output: {                                                          ║
║     "intent": "reply",                                              ║
║     "platform": "whatsapp",      ← Inferred from context           ║
║     "contact": "Priya",          ← Identified from history         ║
║     "tone": "professional",      ← Detected from prefix            ║
║     "body": "I apologize, could we reschedule our 3pm..."          ║
║   }                                                                  ║
║                              │                                      ║
║  Step 3: ROUTE               ▼                                      ║
║  ──────────────────  Intent Router                                  ║
║                              │                                      ║
║       ┌──────────────────────┼──────────────────────┐              ║
║       │          │           │           │           │              ║
║       ▼          ▼           ▼           ▼           ▼              ║
║  reply_handler  expense  reminder   schedule    spotify             ║
║       │         handler  handler    handler     handler             ║
║       │                                                             ║
║  Step 4: EXECUTE             │                                      ║
║  ─────────────── reply_handler.py                                   ║
║                   │                                                 ║
║                   ├── LLM: rephrase body to match tone              ║
║                   ├── Lookup platform from intents context          ║
║                   ├── whatsapp_service.send_message()               ║
║                   │     POST → Baileys :3001/send                   ║
║                   │     → WhatsApp Cloud → Priya's phone            ║
║                   └── DB: mark original message is_replied=True     ║
║                              │                                      ║
║  Step 5: CONFIRM             ▼                                      ║
║  ────────────  Telegram: "✅ Replied to Priya on WhatsApp"          ║
╚════════════════════════════════════════════════════════════════════╝
```

---

## 🔗 Integration Map

```
                        ┌─────────────────┐
                        │   ARIA CORE     │
                        │  (FastAPI +     │
                        │   ARQ Worker)   │
                        └────────┬────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         │  MESSAGING            │  PRODUCTIVITY         │  MONITORING
         │                       │                       │
    ┌────┴─────┐            ┌────┴─────┐           ┌────┴─────┐
    │ Telegram │            │  Gmail   │           │  Stocks  │
    │ (Primary │            │ (OAuth   │           │  Crypto  │
    │  UI)     │            │  2.0)    │           │ Watchlist│
    └──────────┘            └──────────┘           └──────────┘
    ┌──────────┐            ┌──────────┐           ┌──────────┐
    │WhatsApp  │            │  Notion  │           │   RSS    │
    │ (Baileys │            │ (Tasks + │           │  Feeds   │
    │  Bridge) │            │  Notes)  │           │          │
    └──────────┘            └──────────┘           └──────────┘
    ┌──────────┐            ┌──────────┐           ┌──────────┐
    │  Slack   │            │  GitHub  │           │ HackerNews│
    │ (Bot     │            │  (Repo   │           │   API    │
    │  Token)  │            │  Watch)  │           │          │
    └──────────┘            └──────────┘           └──────────┘
    ┌──────────┐            ┌──────────┐           ┌──────────┐
    │ Discord  │            │ Spotify  │           │  Weather │
    │ (Bot     │            │ (OAuth   │           │   API    │
    │  Token)  │            │  2.0)    │           │          │
    └──────────┘            └──────────┘           └──────────┘
    ┌──────────┐
    │   SMS    │
    │ (Gateway │
    │  Token)  │
    └──────────┘
```

### Integration Authentication Methods

| Integration | Auth Type | Direction | Setup Method |
|---|---|---|---|
| **Telegram** | Bot Token + Webhook Secret | Bidirectional | `aria_register_webhook.py` |
| **Gmail** | OAuth 2.0 (offline refresh token) | Bidirectional | `aria_gmail_auth.py` |
| **WhatsApp** | QR Code → Session file | Bidirectional | `docker logs aria-baileys` |
| **Slack** | Bot Token + Signing Secret | Bidirectional | `.env` config |
| **Discord** | Bot Token | Bidirectional | `.env` config |
| **Notion** | Integration Token | Write only | `.env` config |
| **GitHub** | Personal Access Token | Read only | `.env` config |
| **Spotify** | OAuth 2.0 | Bidirectional | `.env` config |
| **SMS** | Gateway API Token | Bidirectional | `.env` config |

---

## 🛠 Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Language** | Python | 3.11 | Core backend |
| **API Framework** | FastAPI | Latest | Async HTTP server + webhook routing |
| **ASGI Server** | Uvicorn + Gunicorn | Latest | Production ASGI serving |
| **Task Queue** | ARQ | Latest | Async background job processing |
| **Message Broker** | Redis | 7 | Job queue backbone + caching |
| **Database** | PostgreSQL | 16 | Primary persistent data store |
| **ORM** | SQLAlchemy (Async) | 2.x | Database abstraction + query building |
| **Migrations** | Alembic | Latest | Schema versioning and migrations |
| **Object Storage** | MinIO | Latest | Voice notes + media files |
| **LLM Provider** | Groq | API | Fast LLaMA 3 inference |
| **LLM Model** | LLaMA 3.3 70B | Versatile | Classification + intent parsing |
| **STT Model** | Whisper Large V3 | via Groq | Voice note transcription |
| **WhatsApp Bridge** | Baileys | Node.js | WhatsApp multi-device WebSocket |
| **Proxy** | Nginx | 1.25 | Reverse proxy + ingress |
| **Containerization** | Docker Compose | v3.9 | Full stack orchestration |

---

## 📂 Folder Structure

```
ARIA/
│
├── api/                          # 🐍 Python FastAPI backend
│   │
│   ├── adapters/                 # 🔌 Inbound data normalization
│   │   ├── gmail_adapter.py      #    Google Pub/Sub → ARIA Message
│   │   ├── slack_adapter.py      #    Slack Event API → ARIA Message
│   │   ├── discord_adapter.py    #    Discord gateway → ARIA Message
│   │   ├── whatsapp_adapter.py   #    Baileys payload → ARIA Message
│   │   └── sms_adapter.py        #    SMS gateway → ARIA Message
│   │
│   ├── core/                     # ⚙️ Infrastructure & config
│   │   ├── config.py             #    Pydantic Settings (reads .env)
│   │   ├── redis.py              #    ARQ Redis pool setup
│   │   └── logging.py            #    Structured JSON logging
│   │
│   ├── db/                       # 🗄️ Database layer
│   │   ├── models.py             #    SQLAlchemy ORM models
│   │   ├── session.py            #    Async session factory
│   │   └── migrations/           #    Alembic migration scripts
│   │       └── versions/
│   │
│   ├── handlers/                 # 🎯 Intent execution
│   │   ├── reply_handler.py      #    Cross-platform reply logic
│   │   ├── expense_handler.py    #    Financial tracking
│   │   ├── schedule_handler.py   #    Calendar management
│   │   ├── habit_handler.py      #    Habit + streak tracking
│   │   ├── reminder_handler.py   #    Scheduled reminders
│   │   ├── summary_handler.py    #    Data digest generation
│   │   └── briefing_handler.py   #    Morning briefing assembly
│   │
│   ├── llm/                      # 🤖 AI/LLM layer
│   │   ├── classify.py           #    Message importance scoring
│   │   ├── parse_intent.py       #    NL → structured JSON intent
│   │   ├── prompts.py            #    All system/user prompt templates
│   │   └── whisper.py            #    Voice → text via Groq Whisper
│   │
│   ├── routes/                   # 🌐 FastAPI endpoint definitions
│   │   ├── telegram.py           #    /webhook/telegram
│   │   ├── gmail.py              #    /webhook/gmail
│   │   ├── whatsapp.py           #    /webhook/whatsapp
│   │   ├── slack.py              #    /webhook/slack
│   │   ├── discord.py            #    /webhook/discord
│   │   └── internal.py           #    /internal/trigger (cron)
│   │
│   ├── services/                 # 🔧 External API clients
│   │   ├── telegram_service.py   #    Send Telegram messages
│   │   ├── gmail_service.py      #    Read/send Gmail
│   │   ├── whatsapp_service.py   #    Send via Baileys bridge
│   │   ├── slack_service.py      #    Post to Slack
│   │   ├── discord_service.py    #    Send to Discord
│   │   ├── notion_service.py     #    Write to Notion DB
│   │   ├── github_service.py     #    GitHub API queries
│   │   ├── spotify_service.py    #    Spotify playback control
│   │   └── sms_service.py        #    Send SMS
│   │
│   ├── workers/                  # ⚡ Background job processors
│   │   ├── settings.py           #    ARQ WorkerSettings config
│   │   ├── inbound_worker.py     #    process_inbound_message job
│   │   └── outbound_worker.py    #    process_outbound_command job
│   │
│   ├── main.py                   # FastAPI app factory + lifespan
│   └── Dockerfile                # API container build
│
├── baileys/                      # 📱 Node.js WhatsApp bridge
│   ├── index.js                  #    Baileys WA multi-device + Express
│   ├── package.json
│   └── Dockerfile
│
├── .env.example                  # 🔑 Environment variable template
├── .gitignore
├── alembic.ini                   # Alembic migration config
├── aria_gmail_auth.py            # 📧 Gmail OAuth setup wizard
├── aria_register_webhook.py      # 🔗 Telegram webhook registration
├── aria_setup.py                 # 🚀 Interactive .env generator
├── docker-compose.yml            # 🐳 Full stack orchestration
└── nginx.conf                    # 🔀 Reverse proxy config
```

---

## 🐳 Infrastructure — Docker Services

```
┌─────────────────────────────────────────────────────────────────┐
│                  DOCKER COMPOSE SERVICES                         │
├─────────────┬──────────────┬──────────┬─────────────────────── ┤
│  Service    │  Image/Build │  Port    │  Role                   │
├─────────────┼──────────────┼──────────┼────────────────────────┤
│ nginx       │ nginx:1.25   │ 80→8000  │ Reverse proxy / ingress │
│ api         │ ./api build  │ 8000     │ FastAPI + Gunicorn       │
│ worker      │ ./api build  │ —        │ ARQ background jobs      │
│ baileys     │ ./baileys    │ 3001     │ WhatsApp WS bridge       │
│ postgres    │ postgres:16  │ 5432     │ Primary database         │
│ redis       │ redis:7      │ 6379     │ Job queue + cache        │
│ minio       │ minio/minio  │ 9000     │ Object storage           │
└─────────────┴──────────────┴──────────┴────────────────────────┘

  Docker Network: aria-net (bridge)
  All services communicate internally — nothing exposed except Nginx

  Persistent Volumes:
  ├── postgres_data   → PostgreSQL data files
  ├── redis_data      → Redis AOF + RDB persistence
  ├── minio_data      → Media + voice note files
  └── baileys_session → WhatsApp QR session auth
```

### Service Dependency Graph

```
        nginx
          │
          ▼
         api ─────────────────────────────────┐
          │                                   │
    ┌─────┼──────┐                            │
    ▼     ▼      ▼                            ▼
postgres redis  minio                      worker
                                        ┌────┬────┐
                                        ▼    ▼    ▼
                                    postgres redis minio
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose v2+
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- A Groq API Key (from [console.groq.com](https://console.groq.com))
- A public URL (Ngrok free tier works perfectly)

---

### Step 1 — Clone & Configure

```bash
git clone https://github.com/aanandmodi/ARIA.git
cd ARIA

# Run the interactive setup wizard (recommended)
python aria_setup.py

# OR manually copy and edit
cp .env.example .env
```

The setup wizard walks you through every config value interactively and auto-generates secure secrets.

---

### Step 2 — Start All Services

```bash
docker compose up -d
```

This spins up 7 containers: nginx, api, worker, baileys, postgres, redis, minio.

---

### Step 3 — Expose & Register Webhook

Telegram requires a public HTTPS URL. Use Ngrok for local development:

```bash
ngrok http 80
# Copy the https://xxxx.ngrok-free.app URL

python aria_register_webhook.py
# Paste your Ngrok URL when prompted
```

---

### Step 4 — Connect Integrations

**WhatsApp:**
```bash
docker logs aria-baileys --follow
# Scan the QR code with WhatsApp → Linked Devices
```

**Gmail:**
```bash
python aria_gmail_auth.py
# Follow the OAuth browser flow — saves refresh token to .env
```

**Discord / Slack:**
Add bot tokens to `.env` and restart:
```bash
docker compose restart api worker
```

---

### Step 5 — Start Using ARIA

Send `/start` to your Telegram bot. You're live.

```
You: remind me to call John tomorrow at 3pm
ARIA: ✅ Reminder set for tomorrow at 3:00 PM

You: what's my schedule today?
ARIA: 📅 Today's Schedule:
      • 10:00 AM — Team standup
      • 3:00 PM — Call John
      • 5:30 PM — Gym

You: professional: I'll need to reschedule our meeting
ARIA: ✅ Replied to Priya on WhatsApp:
      "I sincerely apologize, but I'll need to reschedule our meeting..."
```

---

## 🔧 Environment Variables

### Required (Minimum to run)

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `TELEGRAM_USER_ID` | Your Telegram numeric user ID |
| `GROQ_API_KEY` | Groq cloud API key |

### LLM Settings

| Variable | Default | Description |
|---|---|---|
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Text classification + intent model |
| `GROQ_WHISPER_MODEL` | `whisper-large-v3` | Voice transcription model |
| `IMPORTANCE_THRESHOLD` | `6` | Min score (1-10) to trigger notifications |
| `DRAFT_MODE` | `false` | If `true`, shows replies for approval before sending |

### Database (Auto-configured for Docker)

| Variable | Default |
|---|---|
| `POSTGRES_DB` | `aria` |
| `POSTGRES_USER` | `aria` |
| `POSTGRES_HOST` | `postgres` |
| `REDIS_HOST` | `redis` |
| `MINIO_HOST` | `minio` |
| `MINIO_BUCKET` | `aria-storage` |

### Integrations (All Optional)

| Variable | Service |
|---|---|
| `GMAIL_CLIENT_ID / SECRET / REFRESH_TOKEN` | Gmail OAuth |
| `DISCORD_BOT_TOKEN` | Discord |
| `SLACK_BOT_TOKEN / SIGNING_SECRET` | Slack |
| `NOTION_TOKEN / NOTES_DB_ID / TASKS_DB_ID` | Notion |
| `GITHUB_TOKEN / USERNAME / REPOS` | GitHub |
| `SPOTIFY_CLIENT_ID / SECRET` | Spotify |
| `SMS_GATEWAY_URL / TOKEN` | SMS |

### Preferences

| Variable | Default | Description |
|---|---|---|
| `BRIEFING_TIME` | `08:00` | Time for morning digest (HH:MM) |
| `TIMEZONE` | `Asia/Kolkata` | Your timezone |
| `FOLLOW_UP_DAYS` | `3` | Days before auto follow-up reminder |
| `LANGUAGE` | `en` | Response language |

---

## 🔄 How Each Piece Connects

```
┌────────────────────────────────────────────────────────────────┐
│              ARIA FULL CONNECTION MAP                           │
│                                                                  │
│  ┌──────────┐   webhook   ┌──────────┐  enqueue  ┌──────────┐ │
│  │ External │ ──────────► │  Nginx   │ ─────────► │  Redis   │ │
│  │ Services │             │    +     │            │  Queue   │ │
│  │(WA,Gmail │             │  FastAPI │            └────┬─────┘ │
│  │ Slack..) │             │          │                 │       │
│  └──────────┘             └──────────┘                 │       │
│                                │                       │       │
│                                │ direct writes         │poll   │
│                                ▼                       ▼       │
│                           ┌──────────┐          ┌──────────┐  │
│                           │PostgreSQL│◄─────────│   ARQ    │  │
│                           │          │  reads   │  Worker  │  │
│                           │ messages │  writes  │          │  │
│                           │ intents  │          └────┬─────┘  │
│                           │ reminders│               │        │
│                           │ expenses │               │ calls  │
│                           │ habits   │               ▼        │
│                           └──────────┘          ┌──────────┐  │
│                                                  │  Groq    │  │
│                           ┌──────────┐           │  LLM     │  │
│                           │  MinIO   │◄──────────│  API     │  │
│                           │ (media)  │  upload   │(LLaMA 3  │  │
│                           └──────────┘  download │+Whisper) │  │
│                                                  └────┬─────┘  │
│                                                       │        │
│                                                 notify▼        │
│                                             ┌──────────────┐   │
│                                             │   Telegram   │   │
│                                             │   Bot API    │   │
│                                             │  (User sees  │   │
│                                             │   results)   │   │
│                                             └──────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### Data Flow Summary

| Step | From | To | Via | What Happens |
|---|---|---|---|---|
| 1 | External service | Nginx | HTTPS webhook | Message arrives |
| 2 | Nginx | FastAPI | Internal HTTP | Signature validated |
| 3 | FastAPI | Adapter | Function call | Payload normalized |
| 4 | FastAPI | Redis | ARQ enqueue | Job queued |
| 5 | Redis | ARQ Worker | Job poll | Worker picks up job |
| 6 | ARQ Worker | Groq API | HTTPS | Message classified |
| 7 | ARQ Worker | PostgreSQL | SQLAlchemy | Results persisted |
| 8 | ARQ Worker | MinIO | S3 API | Media stored |
| 9 | ARQ Worker | Telegram API | HTTPS | User notified |
| 10 | Telegram | FastAPI | Webhook | User replies |
| 11 | FastAPI | ARQ Worker | Redis queue | Command queued |
| 12 | ARQ Worker | Groq API | HTTPS | Intent parsed |
| 13 | ARQ Worker | Handler | Function call | Action dispatched |
| 14 | Handler | External service | Service API | Action executed |
| 15 | Handler | Telegram | HTTPS | Confirmation sent |

---

## 🤝 Contributing

Contributions are warmly welcome! Here's how to get started:

```bash
# 1. Fork the repository
# 2. Create your feature branch
git checkout -b feature/add-new-integration

# 3. Add a new service in api/services/
# 4. Add corresponding adapter in api/adapters/
# 5. Add handler logic in api/handlers/
# 6. Update .env.example with new variables

# 7. Test locally
docker compose up -d
python aria_register_webhook.py

# 8. Open a Pull Request
```

**Areas for contribution:**
- New service integrations (Linear, Jira, Trello, etc.)
- Improved LLM prompts for better classification accuracy
- Web dashboard for message history visualization
- Mobile-friendly admin interface
- Additional language support
- Unit and integration tests

---

<div align="center">

---

**Built with ❤️ by [Aanand Modi](https://github.com/aanandmodi)**

*ARIA is MIT licensed. Your data stays on your machine. Always.*

[![GitHub Stars](https://img.shields.io/github/stars/aanandmodi/ARIA?style=social)](https://github.com/aanandmodi/ARIA)

</div>

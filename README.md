<div align="center">

```
 █████╗ ██████╗ ██╗ █████╗
██╔══██╗██╔══██╗██║██╔══██╗
███████║██████╔╝██║███████║
██╔══██║██╔══██╗██║██╔══██║
██║  ██║██║  ██║██║██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
```

# ✦ ARIA - Autonomous Reply & Intelligence Assistant

### *Your entire digital life. One Telegram chat. Zero context switching.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3-F55036?style=for-the-badge&logoColor=white)](https://groq.com)
[![Node.js](https://img.shields.io/badge/Node.js-Baileys-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](./LICENSE)
[![Self Hosted](https://img.shields.io/badge/Self--Hosted-100%25-blueviolet?style=for-the-badge&logo=homeassistant&logoColor=white)](https://github.com/aanandmodi/ARIA)

<br/>

> *"Instead of jumping between WhatsApp, Gmail, Slack, Discord, Spotify, Notion, and GitHub -*
> *ARIA brings everything to one place: your Telegram chat."*

<br/>

---

</div>

## 📑 Table of Contents

- [🧠 Abstract](#-abstract)
- [💡 The Problem ARIA Solves](#-the-problem-aria-solves)
- [✨ Key Features](#-key-features)
- [🏗 System Architecture](#-system-architecture)
- [🔬 Component Deep Dive](#-component-deep-dive)
  - [Nginx — Ingress](#1-nginx--reverse-proxy--ingress)
  - [FastAPI Server](#2-fastapi-server-api)
  - [ARQ Task Worker](#3-arq-task-worker-apiworkers)
  - [Baileys Bridge](#4-baileys-whatsapp-bridge-baileys)
  - [Groq LLM Engine](#5-groq-llm-engine-apillm)
  - [Handlers](#6-handlers-apihandlers)
  - [Services](#7-services-apiservices)
- [🤖 LLM Pipeline](#-llm-pipeline--how-intelligence-works)
- [🗄 Database Architecture](#-database-architecture--pipeline)
- [📥 Inbound Communication Flow](#-communication-flow--inbound)
- [📤 Outbound Command Flow](#-communication-flow--outbound)
- [🔗 Integration Map](#-integration-map)
- [🛠 Tech Stack](#-tech-stack)
- [📂 Folder Structure](#-folder-structure)
- [🐳 Docker Infrastructure](#-infrastructure--docker-services)
- [🚀 Quick Start](#-quick-start)
- [🔧 Environment Variables](#-environment-variables)
- [🔄 Full Connection Map](#-how-each-piece-connects)
- [🤝 Contributing](#-contributing)

---

## 🧠 Abstract

**ARIA** *(Autonomous Reply & Intelligence Assistant)* is a self-hosted, multi-agent AI backend that eliminates digital context-switching. It acts as a **bidirectional intelligence bridge** between you and your entire digital ecosystem.

At its core, ARIA is a **webhook-ingestion + intent-parsing engine**:

| Step | What ARIA Does |
|:----:|----------------|
| **①** | **Receives** events from Gmail, WhatsApp, Slack, Discord, and SMS |
| **②** | **Classifies** every message with Groq LLaMA 3 — scoring urgency, importance & tone |
| **③** | **Filters** noise — only messages above your `IMPORTANCE_THRESHOLD` alert you |
| **④** | **Routes** your Telegram commands through an intent parser to the right service |
| **⑤** | **Persists** everything — messages, intents, expenses, habits — in PostgreSQL |

> The result: a single Telegram bot that manages your entire digital life, powered by a real LLM, running entirely on your own hardware.

---

## 💡 The Problem ARIA Solves

<table>
<tr>
<td width="50%">

### ❌ Without ARIA

```
📱 WhatsApp  → open app
📧 Gmail     → open app
💬 Slack     → open app
🎮 Discord   → open app
📓 Notion    → open browser
🎵 Spotify   → open app
💻 GitHub    → open browser
📊 Finances  → spreadsheet

  ╔══════════════════════╗
  ║  8 apps to manage    ║
  ║  Constant switching  ║
  ║  Hours lost daily    ║
  ╚══════════════════════╝
```

</td>
<td width="50%">

### ✅ With ARIA

```
🤖 Telegram Bot  (1 interface)
│
├── 📩 WhatsApp messages
├── 📧 Gmail (scored & triaged)
├── 💬 Slack threads
├── 🎮 Discord DMs
├── 📓 Notion tasks
├── 🎵 Spotify controls
├── 💰 Expense tracking
└── 📅 Calendar & reminders

  ╔══════════════════════╗
  ║  0 context switches  ║
  ║  1 unified interface ║
  ║  AI does the work    ║
  ╚══════════════════════╝
```

</td>
</tr>
</table>

---

## ✨ Key Features

<table>
<tr><th>Feature</th><th>Description</th></tr>
<tr><td>🗂 <b>Unified Smart Inbox</b></td><td>Gmail, WhatsApp, Discord, Slack, SMS → one Telegram chat</td></tr>
<tr><td>🧮 <b>AI Importance Scoring</b></td><td>Every message scored 1–10 for urgency; only high-priority ones alert you</td></tr>
<tr><td>✍️ <b>Tone-Aware Replies</b></td><td>Prefix with <code>professional:</code> or <code>casual:</code> — ARIA reformats for the target platform</td></tr>
<tr><td>🎙 <b>Voice Note Transcription</b></td><td>Inbound voice messages auto-transcribed via Groq Whisper</td></tr>
<tr><td>🌅 <b>Morning Briefing</b></td><td>Daily digest: weather + calendar + urgent emails + stocks/crypto + HN stories</td></tr>
<tr><td>💬 <b>Natural Language Commands</b></td><td>"Remind me to call John tomorrow", "Log $50 food expense", "What's my schedule?"</td></tr>
<tr><td>📊 <b>Expense Tracking</b></td><td>Log and summarize financial transactions via natural language</td></tr>
<tr><td>✅ <b>Habit Tracking</b></td><td>Track daily habits and receive streak reminders</td></tr>
<tr><td>🔔 <b>Keyword Alerts</b></td><td>Monitor RSS feeds and any source for specific keywords</td></tr>
<tr><td>🔒 <b>Privacy First</b></td><td>100% self-hosted. No cloud services own your data. PostgreSQL stays on your machine</td></tr>
<tr><td>🐳 <b>One-Command Deploy</b></td><td>Full <code>docker compose up -d</code> setup with zero manual config</td></tr>
</table>

---

## 🏗 System Architecture

```mermaid
graph TB
    subgraph EXTERNAL["🌐 External World"]
        TG["📱 Telegram\n(Primary UI)"]
        GM["📧 Gmail\n(Pub/Sub)"]
        WA["💬 WhatsApp\n(Baileys)"]
        SL["🔵 Slack\n(Event API)"]
        DC["🎮 Discord\n(Gateway)"]
        SMS["📟 SMS\n(Gateway)"]
    end

    subgraph INGRESS["🚪 Ingress Layer"]
        NX["⚙️ Nginx\nReverse Proxy :80"]
        BA["🟢 Baileys\nNode.js Bridge :3001"]
    end

    subgraph CORE["⚡ ARIA Core"]
        FA["🐍 FastAPI\nWeb Server :8000"]
        WK["👷 ARQ Worker\nBackground Jobs"]
    end

    subgraph AI["🤖 AI Layer"]
        GQ["🧠 Groq API\nLLaMA 3.3-70B\nWhisper Large v3"]
    end

    subgraph DATA["🗄 Data Layer"]
        PG["🐘 PostgreSQL 16\nPrimary Database"]
        RD["⚡ Redis 7\nJob Queue + Cache"]
        MN["📦 MinIO\nObject Storage"]
    end

    subgraph THIRDPARTY["🔌 Third-Party APIs"]
        NT["📓 Notion"]
        GH["💻 GitHub"]
        SP["🎵 Spotify"]
        WE["☁️ Weather"]
        ST["📈 Stocks/Crypto"]
        HN["📰 HackerNews"]
    end

    TG -- "HTTPS Webhook" --> NX
    GM -- "Pub/Sub Push" --> NX
    WA -- "WebSocket" --> BA
    SL -- "Event API" --> NX
    DC -- "Gateway Events" --> NX
    SMS -- "Gateway Webhook" --> NX

    BA -- "POST /webhook/whatsapp" --> NX
    NX -- "Proxy :8000" --> FA

    FA -- "Enqueue Jobs" --> RD
    RD -- "Poll Jobs" --> WK
    WK -- "LLM Calls" --> GQ
    WK -- "Read/Write" --> PG
    WK -- "Media Store" --> MN
    WK -- "Push Notify" --> TG
    WK -- "Send via Bridge" --> BA

    WK --> NT
    WK --> GH
    WK --> SP
    WK --> WE
    WK --> ST
    WK --> HN

    style EXTERNAL fill:#1a1a2e,stroke:#e94560,color:#fff
    style INGRESS fill:#16213e,stroke:#0f3460,color:#fff
    style CORE fill:#0f3460,stroke:#533483,color:#fff
    style AI fill:#533483,stroke:#e94560,color:#fff
    style DATA fill:#1a1a2e,stroke:#533483,color:#fff
    style THIRDPARTY fill:#16213e,stroke:#e94560,color:#fff
```

---

## 🔬 Component Deep Dive

### 1. Nginx — Reverse Proxy / Ingress

Nginx is the **single public-facing door** to ARIA. It terminates HTTPS, routes webhook requests, and rate-limits traffic.

```mermaid
flowchart LR
    A["🌍 Internet\nHTTPS"] -->|Port 80| B["⚙️ Nginx"]
    B -->|Validate Host| C{"Route?"}
    C -->|/webhook/*| D["🐍 FastAPI :8000"]
    C -->|Rate Limited| E["🚫 Rejected"]
    B --> F["✔ Forward Headers\n✔ SSL Termination\n✔ Host Validation"]

    style A fill:#e94560,color:#fff
    style B fill:#0f3460,color:#fff
    style D fill:#009688,color:#fff
    style E fill:#c0392b,color:#fff
```

**Config file:** `nginx.conf`

---

### 2. FastAPI Server (`api/`)

The brain of ARIA's request handling.

```mermaid
graph LR
    subgraph ROUTES["📍 Routes (api/routes/)"]
        R1["/webhook/telegram"]
        R2["/webhook/gmail"]
        R3["/webhook/whatsapp"]
        R4["/webhook/slack"]
        R5["/webhook/discord"]
        R6["/internal/trigger"]
    end

    subgraph PROCESS["🔄 Processing"]
        V["✔️ Validate\nSignature"]
        A["🔌 Adapter\nNormalize"]
        Q["📬 Enqueue\nARQ Job"]
        OK["200 OK\n(Immediate)"]
    end

    R1 & R2 & R3 & R4 & R5 & R6 --> V
    V --> A --> Q --> OK

    style ROUTES fill:#1a1a2e,stroke:#e94560,color:#fff
    style PROCESS fill:#0f3460,stroke:#533483,color:#fff
```

---

### 3. ARQ Task Worker (`api/workers/`)

The async **workhorse** that processes every job from Redis.

```mermaid
graph TD
    RD["⚡ Redis Queue"] -->|Poll| WK["👷 ARQ Worker"]

    WK --> J1["📥 process_inbound_message\n→ LLM classify → DB store → Telegram notify"]
    WK --> J2["📤 process_outbound_command\n→ LLM parse_intent → handler → external service"]
    WK --> J3["🌅 send_morning_briefing\n→ aggregate sources → format → send"]
    WK --> J4["🔔 follow_up_reminder\n→ check DB → send nudge if needed"]
    WK --> J5["✅ habit_check\n→ query habit table → send streak update"]

    style RD fill:#DC382D,color:#fff
    style WK fill:#0f3460,color:#fff
    style J1 fill:#1a1a2e,stroke:#009688,color:#fff
    style J2 fill:#1a1a2e,stroke:#009688,color:#fff
    style J3 fill:#1a1a2e,stroke:#009688,color:#fff
    style J4 fill:#1a1a2e,stroke:#009688,color:#fff
    style J5 fill:#1a1a2e,stroke:#009688,color:#fff
```

---

### 4. Baileys WhatsApp Bridge (`baileys/`)

A dedicated **Node.js / Express** microservice maintaining the WhatsApp Web multi-device WebSocket session.

```mermaid
sequenceDiagram
    participant WA as 💬 WhatsApp Cloud
    participant BA as 🟢 Baileys :3001
    participant FA as 🐍 FastAPI
    participant US as 👤 User (Telegram)

    WA->>BA: Inbound WebSocket message
    BA->>FA: POST /webhook/whatsapp
    FA->>FA: Normalize + Enqueue
    FA-->>US: Telegram push notification

    US->>FA: Reply command
    FA->>BA: POST /send {contact, body}
    BA->>WA: Send via WebSocket
    WA-->>US: ✅ Message delivered
```

**Key files:** `baileys/index.js`, `baileys/Dockerfile`

#### 📱 WhatsApp JID Namespace & Companion LID Resolution Heuristic
WhatsApp personal contact routing has a highly complex, protocol-level division that standard bridges fail to support:
* **Standard JIDs (`@s.whatsapp.net`):** Normal phone accounts (e.g. `918829095225@s.whatsapp.net`).
* **LID JIDs (`@lid`):** WhatsApp's companion device/hidden identifiers (e.g. `38302585458926@lid`).
* **Group JIDs (`@g.us`):** Group channels (e.g. `120363422974535988@g.us`).

If you attempt to send an LID message using `@s.whatsapp.net`, the WhatsApp server silently discards it into a black hole! 

To solve this, ARIA implements a **mathematical JID length-and-prefix resolution heuristic** right in the handler layer:

```mermaid
flowchart TD
    A["Target Contact JID\n(Without @ suffix)"] --> B{"Contains '-' or\nLength > 15?"}
    B -->|Yes| C["Qualify as Group Chat:\nJID + '@g.us'"]
    B -->|No| D{"Length in\n(13, 14, 15)?"}
    D -->|Yes| E["Qualify as Companion Device LID:\nJID + '@lid'"]
    D -->|No| F["Qualify as Standard Account JID:\nJID + '@s.whatsapp.net'"]

    style A fill:#e94560,color:#fff
    style C fill:#27ae60,color:#fff
    style E fill:#f39c12,color:#fff
    style F fill:#2b5278,color:#fff
```

##### JID Namespace Comparison Table

| Format | Length (digits) | Prefix Characteristics | Suffix Appended | Delivery Namespace |
| :--- | :---: | :--- | :---: | :--- |
| **Standard Phone** | Exactly 12 | Starts with Country Code (e.g. `91` for India) | `@s.whatsapp.net` | Standard Chat |
| **Companion LID** | 13, 14, or 15 | Starts with companion nodes (`18`, `27`, `38`, `95`) | `@lid` | Companion/Hidden Account |
| **Group Chat** | > 15 | Starts with `1203` | `@g.us` | Group Threads |

---

### 5. Groq LLM Engine (`api/llm/`)

ARIA uses **two Groq models** for different tasks:

| Model | Task | Max Tokens |
|-------|------|-----------|
| `llama-3.3-70b-versatile` | Classification, intent parsing, reply reformatting | ~200 |
| `whisper-large-v3` | Voice note transcription | — |

**`classify(message)`** — Returns structured importance scoring:

```json
{
  "importance": 8,
  "urgency": "high",
  "summary": "Client asking for invoice by EOD",
  "tone": "professional",
  "suggested_reply": "I'll send it over within the hour."
}
```

**`parse_intent(command)`** — Converts natural language to a structured action:

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

Each parsed intent maps to a dedicated handler:

```mermaid
graph TD
    IR["🔀 Intent Router"] --> H1["💬 reply_handler.py\nReformat → route to correct service"]
    IR --> H2["💰 expense_handler.py\nParse amount/category → save to DB"]
    IR --> H3["📅 schedule_handler.py\nParse datetime → Google Calendar API"]
    IR --> H4["✅ habit_handler.py\nMark complete → update streak in DB"]
    IR --> H5["⏰ reminder_handler.py\nStore → schedule ARQ delayed job"]
    IR --> H6["📊 summary_handler.py\nQuery DB → format digest → Telegram"]
    IR --> H7["🌅 briefing_handler.py\nAggregate weather/email/stocks → send"]

    style IR fill:#533483,color:#fff
    style H1 fill:#1a1a2e,stroke:#009688,color:#fff
    style H2 fill:#1a1a2e,stroke:#009688,color:#fff
    style H3 fill:#1a1a2e,stroke:#009688,color:#fff
    style H4 fill:#1a1a2e,stroke:#009688,color:#fff
    style H5 fill:#1a1a2e,stroke:#009688,color:#fff
    style H6 fill:#1a1a2e,stroke:#009688,color:#fff
    style H7 fill:#1a1a2e,stroke:#009688,color:#fff
```

---

### 7. Services (`api/services/`)

Thin API client wrappers for each external platform:

| Service File | External API | Auth Method | Direction |
|---|---|---|---|
| `telegram_service.py` | Telegram Bot API | Bot Token | Bidirectional |
| `gmail_service.py` | Google Gmail API | OAuth 2.0 Refresh Token | Bidirectional |
| `whatsapp_service.py` | Baileys REST | Internal HTTP | Bidirectional |
| `slack_service.py` | Slack Web API | Bot Token | Bidirectional |
| `discord_service.py` | Discord Bot API | Bot Token | Bidirectional |
| `notion_service.py` | Notion API | Integration Token | Write only |
| `github_service.py` | GitHub REST API | Personal Access Token | Read only |
| `spotify_service.py` | Spotify Web API | OAuth 2.0 | Bidirectional |
| `sms_service.py` | SMS Gateway | API Token | Bidirectional |

---

## 🤖 LLM Pipeline — How Intelligence Works

### 📥 Inbound Classification Pipeline

```mermaid
flowchart TD
    A["📨 Raw Message Arrives\n(Gmail / WhatsApp / Slack / Discord / SMS)"] --> B

    B["🔌 Adapter Layer\nNormalize vendor payload"] --> C

    C["📋 ARIA Message Schema\n{ source, contact, body, timestamp, media_url? }"] --> D

    D["🧠 Groq API Call\nllama-3.3-70b-versatile\nSystem role + message body\nMax tokens: ~200"] --> E

    E["📊 Classification Result\n{ importance: 1-10, urgency, summary, tone, suggested_reply }"] --> F

    F{{"importance\n≥ THRESHOLD?"}}
    F -->|YES| G["📱 Telegram Push\nNotification sent\nwith Reply Button"]
    F -->|NO| H["🗃️ Stored Silently\nin PostgreSQL\nNo notification"]

    style A fill:#e94560,color:#fff
    style D fill:#533483,color:#fff
    style E fill:#0f3460,color:#fff
    style G fill:#27ae60,color:#fff
    style H fill:#7f8c8d,color:#fff
```

### 📤 Outbound Intent Pipeline

```mermaid
flowchart TD
    A["👤 User types in Telegram\ne.g. 'professional: Sorry I need to reschedule'\nor 'remind me to call John at 3pm'\nor 'play lo-fi on Spotify'"] --> B

    B["🧠 Groq API Call\nparse_intent()\nllama-3.3-70b-versatile"] --> C

    C["📋 Intent JSON\n{ intent, platform, contact, tone, params }"] --> D

    D["🔀 Intent Router\nDispatches to correct Handler"] --> E

    E{{"Intent Type?"}}
    E -->|reply| F["💬 reply_handler\nRephrase → Send via Service"]
    E -->|remind| G["⏰ reminder_handler\nStore + Schedule ARQ job"]
    E -->|expense| H["💰 expense_handler\nParse → Save to DB"]
    E -->|habit| I["✅ habit_handler\nMark → Update streak"]
    E -->|schedule| J["📅 schedule_handler\nCalendar API call"]
    E -->|play| K["🎵 spotify_handler\nSpotify playback control"]

    F & G & H & I & J & K --> L["✅ Confirmation\nSent to Telegram"]

    style A fill:#e94560,color:#fff
    style B fill:#533483,color:#fff
    style D fill:#0f3460,color:#fff
    style L fill:#27ae60,color:#fff
```

### 🎙 Voice Note Pipeline

```mermaid
flowchart LR
    A["🎙 Voice Note\n(WhatsApp / Telegram)"] --> B["⬇️ Download\naudio file"]
    B --> C["📦 Upload to\nMinIO bucket"]
    C --> D["🧠 Groq Whisper API\nwhisper-large-v3"]
    D --> E["📝 Transcript Text"]
    E --> F["🔁 classify()\nPipeline"]
    F --> G["📱 Telegram\nNotification\n(with transcript)"]

    style A fill:#e94560,color:#fff
    style D fill:#533483,color:#fff
    style G fill:#27ae60,color:#fff
```

### 🔄 Context-Aware NLU Pipeline (Sliding Window Classifier)

Standard chatbots suffer from context dropouts on short replies (e.g. you say `"yes"`, `"do it"`, or `"hi"` and the bot defaults to generic conversational chatter). 

ARIA implements a **V2 Context-Aware Sliding Window Intent Classifier** (`intent_unified.py`) that formats and injects the last 3 conversation turns from your Telegram Redis cache directly into the system prompt. This allows LLaMA 3.3 to resolve vague pronouns and follow-up replies perfectly.

```mermaid
flowchart TD
    A["👤 User Command\n(e.g., 'yes please')"] --> B["⚡ Redis Cache\n(CONV_KEY)"]
    B --> C["🔄 Fetch last 3 turns\n(User/Assistant history)"]
    C --> D["📝 Format sliding window context\n[System Prompt + Context]"]
    D --> E["🧠 Groq LLaMA 3.3 70B\nparse_intent_unified()"]
    E --> F["📋 UnifiedIntentResult\n{ intent: 'send_whatsapp', confidence: 0.95 }"]
    F --> G["🔀 Route to Handler\n(Resolves targets contextually)"]

    style A fill:#e94560,color:#fff
    style B fill:#DC382D,color:#fff
    style E fill:#533483,color:#fff
    style F fill:#009688,color:#fff
```

### 🐙 GitHub Watcher & Monitored Repository Watcher Pipeline

ARIA keeps you updated on your codebase asynchronously using a highly optimized background cron task worker:

```mermaid
flowchart TD
    A["⏰ Background Cron Trigger\n(cron:poll_github)"] --> B["🌐 GitHub REST API\n(Fetch PRs, commits, issues)"]
    B --> C["📝 Compare with Database\n(Filter out duplicates)"]
    C --> D["🗃️ Store new items\nin PostgreSQL"]
    D --> E["📱 Forward digest notifications\nto Telegram Bot"]
    E --> F["💡 Suggesters & Review Actions\n(Merges, Comments, Closes)"]

    style A fill:#f39c12,color:#fff
    style B fill:#1a1a2e,stroke:#e94560,color:#fff
    style D fill:#336791,color:#fff
    style E fill:#27ae60,color:#fff
```

---

## 🗄 Database Architecture & Pipeline

ARIA uses **PostgreSQL 16** with **SQLAlchemy Async ORM**. Migrations managed by **Alembic**.

### Entity Relationship Diagram

```mermaid
erDiagram
    messages {
        UUID id PK
        varchar source
        varchar contact
        text body
        text summary
        int importance
        varchar urgency
        varchar tone
        boolean is_read
        boolean is_replied
        text media_url
        timestamptz created_at
    }

    intents {
        UUID id PK
        text user_message
        jsonb parsed_intent
        jsonb handler_result
        timestamptz executed_at
        boolean success
        UUID message_id FK
    }

    expenses {
        UUID id PK
        numeric amount
        varchar category
        text description
        timestamptz logged_at
    }

    reminders {
        UUID id PK
        text body
        timestamptz remind_at
        boolean is_sent
        timestamptz created_at
    }

    habits {
        UUID id PK
        varchar name
        int streak
        date last_completed
        timestamptz created_at
    }

    follow_up_queue {
        UUID id PK
        varchar contact
        varchar platform
        timestamptz due_at
        boolean is_done
        UUID message_id FK
    }

    briefing_cache {
        UUID id PK
        date briefing_date
        jsonb content
        timestamptz sent_at
    }

    messages ||--o{ intents : "triggers"
    messages ||--o{ follow_up_queue : "queues"
```

### Database Write Pipeline

```mermaid
flowchart TD
    A["📨 Inbound Webhook"] --> B["👷 ARQ Worker\npicks up job"]
    B --> C["🧠 LLM classify()"]
    C --> D["🔐 SQLAlchemy\nAsync Session"]
    D --> E["🐘 PostgreSQL Commit\n(ACID guaranteed)"]
    E --> F["⚡ Redis\nJob acknowledged & removed"]

    G["👤 User Command\nvia Telegram"] --> H["🧠 parse_intent()"]
    H --> I{{"Intent Type?"}}
    I -->|expense| J["💰 Write to\nexpenses table"]
    I -->|remind| K["⏰ Write to reminders\n+ Schedule ARQ job"]
    I -->|habit| L["✅ Update habits\nstreak counter"]
    I -->|reply| M["✏️ Set is_replied=True\nLog to intents table"]

    style A fill:#e94560,color:#fff
    style G fill:#e94560,color:#fff
    style E fill:#336791,color:#fff
    style F fill:#DC382D,color:#fff
```

### Alembic Migration Pipeline

```mermaid
flowchart LR
    A["✏️ Developer changes\nSQLAlchemy model"] --> B["alembic revision\n--autogenerate"]
    B --> C["📄 New migration script\napi/db/migrations/versions/"]
    C --> D["alembic upgrade head\n(auto on container start)"]
    D --> E["🐘 PostgreSQL\nschema updated"]

    style A fill:#1a1a2e,stroke:#e94560,color:#fff
    style E fill:#336791,color:#fff
```

---

## 📥 Communication Flow — Inbound

```mermaid
sequenceDiagram
    participant EXT as 🌍 External Service
    participant NX as ⚙️ Nginx
    participant FA as 🐍 FastAPI
    participant AD as 🔌 Adapter
    participant RD as ⚡ Redis
    participant WK as 👷 ARQ Worker
    participant GQ as 🧠 Groq API
    participant PG as 🐘 PostgreSQL
    participant MN as 📦 MinIO
    participant TG as 📱 Telegram

    EXT->>NX: HTTPS Webhook (Gmail / Slack / Discord / SMS)
    NX->>FA: Proxy to :8000
    FA->>FA: Validate signature
    FA->>AD: Deserialize payload
    AD->>FA: Normalized ARIA Message
    FA->>RD: arq.enqueue_job("process_inbound")
    FA-->>EXT: 200 OK (immediate)

    RD->>WK: Poll & pickup job
    WK->>GQ: Fetch full body (Gmail API)
    WK->>MN: Download & store media
    WK->>GQ: Whisper transcribe (if voice)
    WK->>GQ: classify(message)
    GQ-->>WK: { importance, urgency, summary, tone }
    WK->>PG: Save Message record

    alt importance ≥ THRESHOLD
        WK->>TG: Push notification + Reply button
    else importance < THRESHOLD
        WK->>PG: Store silently (no notification)
    end
```

---

## 📤 Communication Flow — Outbound

```mermaid
sequenceDiagram
    participant US as 👤 User
    participant TG as 📱 Telegram
    participant FA as 🐍 FastAPI
    participant RD as ⚡ Redis
    participant WK as 👷 ARQ Worker
    participant GQ as 🧠 Groq API
    participant HD as 🎯 Handler
    participant SV as 🔧 Service
    participant EXT as 🌍 External Platform

    US->>TG: "professional: Sorry, need to reschedule"
    TG->>FA: Webhook POST /webhook/telegram
    FA->>FA: Validate bot token + user whitelist
    FA->>RD: Enqueue process_outbound_command
    FA-->>TG: 200 OK

    RD->>WK: Poll & pickup job
    WK->>GQ: parse_intent(command)
    GQ-->>WK: { intent, platform, contact, tone, body }
    WK->>HD: Dispatch to reply_handler
    HD->>GQ: Rephrase body for tone
    GQ-->>HD: Reformatted reply text
    HD->>SV: whatsapp_service.send_message()
    SV->>EXT: POST Baileys :3001/send
    EXT-->>US: ✅ Message delivered
    HD->>TG: "✅ Replied to Priya on WhatsApp"
```

---

## 🔗 Integration Map

```mermaid
graph TB
    CORE["⚡ ARIA CORE\nFastAPI + ARQ Worker"]

    subgraph MSG["💬 Messaging"]
        TG["📱 Telegram\nPrimary UI"]
        WA["💬 WhatsApp\nBaileys Bridge"]
        SL["🔵 Slack\nBot Token"]
        DC["🎮 Discord\nBot Token"]
        SM["📟 SMS\nGateway"]
    end

    subgraph PROD["📋 Productivity"]
        GM["📧 Gmail\nOAuth 2.0"]
        NT["📓 Notion\nTasks + Notes"]
        GH["💻 GitHub\nRepo Watch"]
        SP["🎵 Spotify\nPlayback"]
        CA["📅 Calendar\nGoogle Cal"]
    end

    subgraph MON["📊 Monitoring"]
        ST["📈 Stocks\nCrypto Watch"]
        WE["☁️ Weather\nAPI"]
        HN["📰 HackerNews\nRSS"]
        RS["🔔 RSS Feeds\nKeyword Alerts"]
    end

    CORE <--> TG & WA & SL & DC & SM
    CORE <--> GM & NT & GH & SP & CA
    CORE --> ST & WE & HN & RS

    style CORE fill:#533483,color:#fff
    style MSG fill:#1a1a2e,stroke:#e94560,color:#fff
    style PROD fill:#1a1a2e,stroke:#009688,color:#fff
    style MON fill:#1a1a2e,stroke:#f39c12,color:#fff
```

### Integration Authentication Reference

| Integration | Auth Type | Direction | Setup |
|---|---|---|---|
| **Telegram** | Bot Token + Webhook Secret | Bidirectional | `aria_register_webhook.py` |
| **Gmail** | OAuth 2.0 offline refresh token | Bidirectional | `aria_gmail_auth.py` |
| **WhatsApp** | QR Code → Session file | Bidirectional | `docker logs aria-baileys` |
| **Slack** | Bot Token + Signing Secret | Bidirectional | `.env` config |
| **Discord** | Bot Token | Bidirectional | `.env` config |
| **Notion** | Integration Token | Write only | `.env` config |
| **GitHub** | Personal Access Token | Read only | `.env` config |
| **Spotify** | OAuth 2.0 | Bidirectional | `.env` config |
| **SMS** | Gateway API Token | Bidirectional | `.env` config |

---

## 🛠 Tech Stack

```mermaid
graph LR
    subgraph LANG["Language"]
        PY["🐍 Python 3.11"]
        JS["🟢 Node.js\n(Baileys)"]
    end

    subgraph API["API Layer"]
        FA["⚡ FastAPI"]
        UV["🦄 Uvicorn\n+ Gunicorn"]
    end

    subgraph QUEUE["Job Queue"]
        ARQ["📬 ARQ\nAsync Worker"]
        RD["⚡ Redis 7\nBroker + Cache"]
    end

    subgraph DB["Database"]
        PG["🐘 PostgreSQL 16"]
        SA["🔧 SQLAlchemy\nAsync ORM"]
        AL["🗂 Alembic\nMigrations"]
    end

    subgraph STORAGE["Storage"]
        MN["📦 MinIO\nObject Store\nS3-compatible"]
    end

    subgraph AI["AI / LLM"]
        GQ["🧠 Groq Cloud"]
        LL["LLaMA 3.3 70B\nClassification + Intent"]
        WH["Whisper Large V3\nVoice Transcription"]
    end

    subgraph INFRA["Infrastructure"]
        NX["⚙️ Nginx 1.25\nReverse Proxy"]
        DC["🐳 Docker Compose\nOrchestration"]
    end

    PY --> FA --> UV
    ARQ --> RD
    SA --> PG
    AL --> PG
    GQ --> LL & WH

    style LANG fill:#1a1a2e,stroke:#3776AB,color:#fff
    style API fill:#1a1a2e,stroke:#009688,color:#fff
    style QUEUE fill:#1a1a2e,stroke:#DC382D,color:#fff
    style DB fill:#1a1a2e,stroke:#336791,color:#fff
    style STORAGE fill:#1a1a2e,stroke:#f39c12,color:#fff
    style AI fill:#1a1a2e,stroke:#533483,color:#fff
    style INFRA fill:#1a1a2e,stroke:#2496ED,color:#fff
```

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
├── 🐍 api/                              ← Python FastAPI Backend
│   │
│   ├── 🔌 adapters/                     ← Inbound Data Normalization
│   │   ├── gmail_adapter.py             │  Google Pub/Sub → ARIA Message
│   │   ├── slack_adapter.py             │  Slack Event API → ARIA Message
│   │   ├── discord_adapter.py           │  Discord Gateway → ARIA Message
│   │   ├── whatsapp_adapter.py          │  Baileys Payload → ARIA Message
│   │   └── sms_adapter.py              ─┘  SMS Gateway → ARIA Message
│   │
│   ├── ⚙️ core/                         ← Infrastructure & Config
│   │   ├── config.py                    │  Pydantic Settings (reads .env)
│   │   ├── redis.py                     │  ARQ Redis pool setup
│   │   └── logging.py                  ─┘  Structured JSON logging
│   │
│   ├── 🗄️ db/                           ← Database Layer
│   │   ├── models.py                    │  SQLAlchemy ORM models
│   │   ├── session.py                   │  Async session factory
│   │   └── migrations/                 ─┘  Alembic migration scripts
│   │       └── versions/
│   │
│   ├── 🎯 handlers/                     ← Intent Execution
│   │   ├── reply_handler.py             │  Cross-platform reply logic
│   │   ├── expense_handler.py           │  Financial tracking
│   │   ├── schedule_handler.py          │  Calendar management
│   │   ├── habit_handler.py             │  Habit + streak tracking
│   │   ├── reminder_handler.py          │  Scheduled reminders
│   │   ├── summary_handler.py           │  Data digest generation
│   │   └── briefing_handler.py         ─┘  Morning briefing assembly
│   │
│   ├── 🤖 llm/                          ← AI / LLM Layer
│   │   ├── classify.py                  │  Message importance scoring
│   │   ├── parse_intent.py              │  NL → structured JSON intent
│   │   ├── prompts.py                   │  All system/user prompt templates
│   │   └── whisper.py                  ─┘  Voice → text via Groq Whisper
│   │
│   ├── 🌐 routes/                       ← FastAPI Endpoint Definitions
│   │   ├── telegram.py                  │  /webhook/telegram
│   │   ├── gmail.py                     │  /webhook/gmail
│   │   ├── whatsapp.py                  │  /webhook/whatsapp
│   │   ├── slack.py                     │  /webhook/slack
│   │   ├── discord.py                   │  /webhook/discord
│   │   └── internal.py                 ─┘  /internal/trigger (cron)
│   │
│   ├── 🔧 services/                     ← External API Clients
│   │   ├── telegram_service.py          │  Send Telegram messages
│   │   ├── gmail_service.py             │  Read/send Gmail
│   │   ├── whatsapp_service.py          │  Send via Baileys bridge
│   │   ├── slack_service.py             │  Post to Slack
│   │   ├── discord_service.py           │  Send to Discord
│   │   ├── notion_service.py            │  Write to Notion DB
│   │   ├── github_service.py            │  GitHub API queries
│   │   ├── spotify_service.py           │  Spotify playback control
│   │   └── sms_service.py              ─┘  Send SMS
│   │
│   ├── ⚡ workers/                      ← Background Job Processors
│   │   ├── settings.py                  │  ARQ WorkerSettings config
│   │   ├── inbound_worker.py            │  process_inbound_message job
│   │   └── outbound_worker.py          ─┘  process_outbound_command job
│   │
│   ├── main.py                          ← FastAPI app factory + lifespan
│   └── Dockerfile                       ← API container build
│
├── 📱 baileys/                          ← Node.js WhatsApp Bridge
│   ├── index.js                         │  Baileys WA multi-device + Express
│   ├── package.json                     │
│   └── Dockerfile                      ─┘
│
├── 🔑 .env.example                      ← Environment variable template
├── 📋 alembic.ini                       ← Alembic migration config
├── 📧 aria_gmail_auth.py                ← Gmail OAuth setup wizard
├── 🔗 aria_register_webhook.py          ← Telegram webhook registration
├── 🚀 aria_setup.py                     ← Interactive .env generator
├── 🐳 docker-compose.yml                ← Full stack orchestration
└── 🔀 nginx.conf                        ← Reverse proxy config
```

---

## 🐳 Infrastructure — Docker Services

### Service Overview

```mermaid
graph TB
    subgraph DOCKER["🐳 Docker Network: aria-net (bridge)"]
        NX["⚙️ nginx\nnginx:1.25\n:80 → :8000\nReverse proxy / ingress"]
        FA["🐍 api\n./api build\n:8000\nFastAPI + Gunicorn"]
        WK["👷 worker\n./api build\nno port\nARQ background jobs"]
        BA["📱 baileys\n./baileys\n:3001\nWhatsApp WS bridge"]
        PG["🐘 postgres\npostgres:16\n:5432\nPrimary database"]
        RD["⚡ redis\nredis:7\n:6379\nJob queue + cache"]
        MN["📦 minio\nminio/minio\n:9000\nObject storage"]
    end

    subgraph VOLS["💾 Persistent Volumes"]
        V1["postgres_data"]
        V2["redis_data"]
        V3["minio_data"]
        V4["baileys_session"]
    end

    NX --> FA
    FA --> PG & RD & MN & BA
    WK --> PG & RD & MN
    FA -.->|same image| WK

    PG --- V1
    RD --- V2
    MN --- V3
    BA --- V4

    style DOCKER fill:#1a1a2e,stroke:#2496ED,color:#fff
    style VOLS fill:#16213e,stroke:#f39c12,color:#fff
```

### Service Dependency Graph

```mermaid
graph TD
    NX["⚙️ nginx"] --> FA["🐍 api"]
    FA --> PG["🐘 postgres"]
    FA --> RD["⚡ redis"]
    FA --> MN["📦 minio"]
    FA --> BA["📱 baileys"]
    FA -.->|same build| WK["👷 worker"]
    WK --> PG & RD & MN

    style NX fill:#0f3460,color:#fff
    style FA fill:#009688,color:#fff
    style WK fill:#533483,color:#fff
    style PG fill:#336791,color:#fff
    style RD fill:#DC382D,color:#fff
    style MN fill:#f39c12,color:#000
    style BA fill:#27ae60,color:#fff
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Details |
|---|---|
| 🐳 Docker & Docker Compose v2+ | Container orchestration |
| 📱 Telegram Bot Token | From [@BotFather](https://t.me/BotFather) |
| 🧠 Groq API Key | From [console.groq.com](https://console.groq.com) |
| 🌐 Public HTTPS URL | Ngrok free tier works perfectly |

---

### Step 1 — Clone & Configure

```bash
git clone https://github.com/aanandmodi/ARIA.git
cd ARIA

# 🪄 Run the interactive setup wizard (recommended)
python aria_setup.py

# OR manually copy and edit
cp .env.example .env
nano .env
```

> The setup wizard walks you through every config value interactively and auto-generates secure secrets.

---

### Step 2 — Start All Services

```bash
docker compose up -d
```

This spins up **7 containers**: `nginx`, `api`, `worker`, `baileys`, `postgres`, `redis`, `minio`.

---

### Step 3 — Expose & Register Webhook

```bash
# 1. Start a public tunnel
ngrok http 80
# → Copy the https://xxxx.ngrok-free.app URL

# 2. Register your webhook with Telegram
python aria_register_webhook.py
# → Paste your Ngrok URL when prompted
```

---

### Step 4 — Connect Integrations

**📱 WhatsApp:**
```bash
docker logs aria-baileys --follow
# → Scan the QR code with WhatsApp → Linked Devices
```

**📧 Gmail:**
```bash
python aria_gmail_auth.py
# → Follow the OAuth browser flow — saves refresh token to .env
```

**🔵 Discord / Slack:**
```bash
# Add bot tokens to .env and restart
docker compose restart api worker
```

---

### Step 5 — Start Using ARIA

Send `/start` to your Telegram bot. You're live. 🎉

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

### 🔴 Required (Minimum to run)

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `TELEGRAM_USER_ID` | Your Telegram numeric user ID |
| `GROQ_API_KEY` | Groq cloud API key |

### 🤖 LLM Settings

| Variable | Default | Description |
|---|---|---|
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Text classification + intent model |
| `GROQ_WHISPER_MODEL` | `whisper-large-v3` | Voice transcription model |
| `IMPORTANCE_THRESHOLD` | `6` | Min score (1–10) to trigger notifications |
| `DRAFT_MODE` | `false` | If `true`, shows replies for approval before sending |

### 🐘 Database (Auto-configured for Docker)

| Variable | Default |
|---|---|
| `POSTGRES_DB` | `aria` |
| `POSTGRES_USER` | `aria` |
| `POSTGRES_HOST` | `postgres` |
| `REDIS_HOST` | `redis` |
| `MINIO_HOST` | `minio` |
| `MINIO_BUCKET` | `aria-storage` |

### 🔌 Integrations (All Optional)

| Variable | Service |
|---|---|
| `GMAIL_CLIENT_ID` / `SECRET` / `REFRESH_TOKEN` | Gmail OAuth |
| `DISCORD_BOT_TOKEN` | Discord |
| `SLACK_BOT_TOKEN` / `SIGNING_SECRET` | Slack |
| `NOTION_TOKEN` / `NOTES_DB_ID` / `TASKS_DB_ID` | Notion |
| `GITHUB_TOKEN` / `USERNAME` / `REPOS` | GitHub |
| `SPOTIFY_CLIENT_ID` / `SECRET` | Spotify |
| `SMS_GATEWAY_URL` / `TOKEN` | SMS |

### ⚙️ Preferences

| Variable | Default | Description |
|---|---|---|
| `BRIEFING_TIME` | `08:00` | Time for morning digest (HH:MM) |
| `TIMEZONE` | `Asia/Kolkata` | Your timezone |
| `FOLLOW_UP_DAYS` | `3` | Days before auto follow-up reminder |
| `LANGUAGE` | `en` | Response language |

---

## 🔄 How Each Piece Connects

```mermaid
flowchart TD
    EXT["🌍 External Services\n(WhatsApp, Gmail, Slack...)"]
    NX["⚙️ Nginx\nReverse Proxy"]
    FA["🐍 FastAPI\nWeb Server"]
    RD["⚡ Redis\nJob Queue"]
    WK["👷 ARQ Worker"]
    GQ["🧠 Groq LLM API\n(LLaMA 3 + Whisper)"]
    PG["🐘 PostgreSQL\nmessages · intents\nreminders · expenses\nhabits"]
    MN["📦 MinIO\nMedia Storage"]
    TG["📱 Telegram\nUser sees results"]

    EXT -->|HTTPS webhook| NX
    NX -->|Proxy :8000| FA
    FA -->|Enqueue jobs| RD
    RD -->|Poll jobs| WK
    WK -->|LLM calls| GQ
    WK -->|Read/Write| PG
    WK -->|Upload/Download| MN
    WK -->|Push notify| TG
    TG -->|User replies| FA
    FA -->|direct writes| PG

    style EXT fill:#e94560,color:#fff
    style NX fill:#0f3460,color:#fff
    style FA fill:#009688,color:#fff
    style RD fill:#DC382D,color:#fff
    style WK fill:#533483,color:#fff
    style GQ fill:#533483,color:#fff
    style PG fill:#336791,color:#fff
    style MN fill:#f39c12,color:#000
    style TG fill:#2b5278,color:#fff
```

### Data Flow Summary

| Step | From | To | Via | What Happens |
|:---:|---|---|---|---|
| **1** | External service | Nginx | HTTPS webhook | Message arrives |
| **2** | Nginx | FastAPI | Internal HTTP | Signature validated |
| **3** | FastAPI | Adapter | Function call | Payload normalized |
| **4** | FastAPI | Redis | ARQ enqueue | Job queued |
| **5** | Redis | ARQ Worker | Job poll | Worker picks up job |
| **6** | ARQ Worker | Groq API | HTTPS | Message classified |
| **7** | ARQ Worker | PostgreSQL | SQLAlchemy | Results persisted |
| **8** | ARQ Worker | MinIO | S3 API | Media stored |
| **9** | ARQ Worker | Telegram API | HTTPS | User notified |
| **10** | Telegram | FastAPI | Webhook | User replies |
| **11** | FastAPI | ARQ Worker | Redis queue | Command queued |
| **12** | ARQ Worker | Groq API | HTTPS | Intent parsed |
| **13** | ARQ Worker | Handler | Function call | Action dispatched |
| **14** | Handler | External service | Service API | Action executed |
| **15** | Handler | Telegram | HTTPS | Confirmation sent |

---

##  Gotchas & Production Troubleshooting Guide

### 1. 📱 WhatsApp: "Sent successfully" but not showing up on target phone
* **Reason:** The target contact in the database is saved under an **LID namespace** (13, 14, or 15-digit number) but was incorrectly qualified with `@s.whatsapp.net`. The message went into a black hole!
* **Solution:** Run the automatic contact synchronization script:
  ```bash
  docker exec -it aria-worker python api/scripts/sync_whatsapp_contacts.py
  ```
  This will query Baileys and resolve all contact numbers to their true namespaces in PostgreSQL. ARIA will now automatically use the `@lid` qualifier!

### 2. 🐙 GitHub: "Failed to fetch commits" with 404 Error
* **Reason:** When you ask *"whats the last commit of ARIA repo?"*, the LLM extracts the repository name as `"ARIA repo"`, expanding to `"Aanandmodi/ARIA repo"`. This returns a 404 since the repo on GitHub is named `"Aanandmodi/ARIA"`.
* **Solution:** ARIA has an automatic suffix-cleanup loop implemented. Verify that the repository configuration in your `.env` does not contain conversational terms:
  ```bash
  # Check your GITHUB_REPOS value in .env
  GITHUB_REPOS=Aanandmodi/ARIA
  ```

### 3. 🚨 LLM Wrapper Signature crash (TypeError)
* **Reason:** Custom model properties like `max_tokens` or `temperature` were passed but not supported by the underlying client wrapper method, causing intent parsing to fail silently.
* **Solution:** Patch has been fully deployed. Ensure your FastAPI/Worker containers are restarted to load the latest client patches:
  ```bash
  docker compose restart api worker
  ```

---

## 🤝 Contributing

Contributions are warmly welcome! Here's how to get started:

```bash
# 1. Fork the repository on GitHub

# 2. Create your feature branch
git checkout -b feature/add-new-integration

# 3. Add your integration
#    → api/services/    (new API client)
#    → api/adapters/    (new inbound normalizer)
#    → api/handlers/    (new intent handler)
#    → .env.example     (new config vars)

# 4. Test locally
docker compose up -d
python aria_register_webhook.py

# 5. Open a Pull Request 🎉
```

### Areas for Contribution

| Area | Description |
|---|---|
| 🔌 **New Integrations** | Linear, Jira, Trello, Obsidian, etc. |
| 🧠 **LLM Prompt Tuning** | Better classification + intent accuracy |
| 📊 **Web Dashboard** | Message history visualization UI |
| 📱 **Mobile Admin** | Mobile-friendly management interface |
| 🌍 **i18n Support** | Additional language support |
| 🧪 **Tests** | Unit and integration test coverage |

---

<div align="center">

---

### Built with ❤️ by [Aanand Modi](https://github.com/aanandmodi)

*ARIA is MIT licensed. Your data stays on your machine. Always.*

[![GitHub Stars](https://img.shields.io/github/stars/aanandmodi/ARIA?style=social)](https://github.com/aanandmodi/ARIA)
[![GitHub Forks](https://img.shields.io/github/forks/aanandmodi/ARIA?style=social)](https://github.com/aanandmodi/ARIA)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

</div>

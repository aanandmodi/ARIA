# ✦ ARIA Jarvis Roadmap: The Next 30 Big Things
This roadmap details the architectural blueprints, data flows, and contributor checkpoints for transforming **ARIA** from a Telegram-bound assistant into a cross-platform, self-hosted, autonomous Jarvis ecosystem.

---

## 📑 Roadmap Categories
- [🌐 Category I: Multi-Platform Clients & Interfaces](#-category-i-multi-platform-clients--interfaces) (Items 1–6)
- [🧠 Category II: Advanced AI Brain & Cognitive Upgrades](#-category-ii-advanced-ai-brain--cognitive-upgrades) (Items 7–12)
- [🔌 Category III: Deep Digital & Physical Integrations](#-category-iii-deep-digital--physical-integrations) (Items 13–20)
- [👥 Category IV: Collaboration & Multi-Tenant Scaling](#-category-iv-collaboration--multi-tenant-scaling) (Items 21–24)
- [🛡️ Category V: Security, Privacy, & Enterprise Infrastructure](#-category-v-security-privacy--enterprise-infrastructure) (Items 25–30)

---

## 🌐 Category I: Multi-Platform Clients & Interfaces

### 1. Next.js Admin & Command Dashboard (Web UI)
* **Description**: A unified web-based control room to configure integrations, visualize the system status, view interactive financial reports, manage active habits, browse transcribed notes, and chat directly with ARIA.
* **Code Connection**: Connects to the existing API structure via a new routing package `api/routes/web_dashboard.py` and registers it in [main.py](file:///d:/ARIA/api/main.py). It reads data directly from database models in [models.py](file:///d:/ARIA/api/db/models.py) (e.g., `Message`, `Expense`, `UserProfile`).
* **Data Flow**:
  ```
  [Next.js Client] ──(HTTPS/WSS)──> [FastAPI Web Router] ──> [db/session.py] ──> [PostgreSQL]
  ```
* **Contributor Checkpoints**:
  - [ ] Implement token-based JWT authentication and endpoint protection in a new auth middleware.
  - [ ] Create API endpoints `/api/v1/dashboard/stats` for database telemetry (message volumes, cache hits).
  - [ ] Build the Next.js React client with Tailwind CSS, showing charts of expenses (`Expense`) and habit streaks (`Habit`).
  - [ ] Implement an interactive terminal widget using WebSockets (`/ws/chat`) to chat with the LLM pipeline directly.

### 2. ARIA Companion Chrome Extension
* **Description**: A browser extension that acts as ARIA's eyes on the web, letting users clip articles, save pages to Notion, highlight text to create memories, and autofill forms based on ARIA's memory database.
* **Code Connection**: Invokes endpoints in `api/routes/notes.py` (which uses [notion_service.py](file:///d:/ARIA/api/services/notion_service.py)) and `api/routes/internal.py`.
* **Data Flow**:
  ```
  [Chrome Web Page] ──(Extension API)──> [FastAPI /webhook/note] ──> [ARQ Worker] ──> [Notion & MinIO]
  ```
* **Contributor Checkpoints**:
  - [ ] Write the Chrome manifest v3 configuration and popup UI.
  - [ ] Implement a right-click context menu: "Send to ARIA Notes".
  - [ ] Build content scripts to extract page text, metadata, and screenshots.
  - [ ] Connect the extension to ARIA's backend API using an API key header.

### 3. Tauri Cross-Platform Desktop Overlay (Spotlight/Raycast for ARIA)
* **Description**: A desktop widget triggered by a keyboard shortcut (e.g., `Alt + Space`) allowing instant query submittal, hotkey voice transcription, system metrics display, and local file sharing.
* **Code Connection**: Interacts with the backend via [api/workers/telegram_processor.py](file:///d:/ARIA/api/workers/telegram_processor.py)'s text processing core by exposing a unified endpoint `/api/v1/query`.
* **Data Flow**:
  ```
  [Desktop (Alt+Space)] ──> [Tauri App] ──> [FastAPI API] ──> [intent_unified.py] ──> [Response Payload]
  ```
* **Contributor Checkpoints**:
  - [ ] Initialize the Rust-based Tauri project scaffolding.
  - [ ] Register global shortcuts for key bindings across Windows, macOS, and Linux.
  - [ ] Implement voice-record shortcut binding that records audio and sends it to `/webhook/telegram` as a simulated voice note.
  - [ ] Build a sleek glassmorphic interface that floats above other apps.

### 4. Interactive CLI Tool (`aria-cli`)
* **Description**: A terminal client for developers to communicate with ARIA, check system logs, run migrations, and log activities directly from shell terminals.
* **Code Connection**: Integrates with [api/main.py](file:///d:/ARIA/api/main.py)'s management commands.
* **Data Flow**:
  ```
  Terminal Command (e.g., `aria log -m "Lunch 200"`) ──> [aria-cli] ──> [FastAPI Endpoint] ──> [PostgreSQL]
  ```
* **Contributor Checkpoints**:
  - [ ] Build a Python Click-based or Go-based CLI program.
  - [ ] Implement command execution pipelines: `aria status`, `aria search <query>`, `aria expense <amount> <category>`.
  - [ ] Add a secure credential manager (using system keyring) to save API URLs and tokens.
  - [ ] Add terminal shell auto-completion scripts.

### 5. Native Flutter Mobile App (iOS/Android)
* **Description**: A lightweight mobile app providing native push notifications, local SQLite cache, background location tracking (to trigger reminders based on location), and device sensor integration (e.g., battery levels).
* **Code Connection**: Exposes `/api/v1/mobile/register-device` to store mobile tokens and routes notifications through Firebase Cloud Messaging (FCM).
* **Data Flow**:
  ```
  [PostgreSQL Trigger] ──> [ARQ worker/alerts.py] ──> [FCM Gateway] ──> [Flutter Client App]
  ```
* **Contributor Checkpoints**:
  - [ ] Create the Flutter workspace.
  - [ ] Set up FCM push notification handlers for foreground and background states.
  - [ ] Implement a location service that polls coordinates in the background and hits `/api/v1/location/update`.
  - [ ] Create a local offline SQLite database to display cached notes (`Note`) and habits (`Habit`).

### 6. Wake-Word Hardware / Smart Speaker Interface
* **Description**: Hardware integration allowing hands-free voice interaction. Triggered by a wake word (e.g., "Aria"), it records voice, streams it to Groq's Whisper API, and speaks the response back using Text-to-Speech (TTS).
* **Code Connection**: Calls [transcribe.py](file:///d:/ARIA/api/llm/transcribe.py) and a new TTS service `api/services/tts_service.py`.
* **Data Flow**:
  ```
  [ESP32 / Pi Mic] ──(PCM Stream)──> [FastAPI Stream API] ──> [Groq Whisper] ──> [LLM] ──> [TTS] ──> [PCM Audio Out]
  ```
* **Contributor Checkpoints**:
  - [ ] Set up an ESP32 or Raspberry Pi voice capture script using PyAudio.
  - [ ] Integrate a lightweight local wake-word engine (like Picovoice Porcupine or open-source OpenWakeWord).
  - [ ] Build a FastAPI WebSocket route (`/ws/audio-stream`) for streaming real-time raw audio.
  - [ ] Add TTS conversion (e.g., using ElevenLabs, Kokoro, or edge-tts) and stream audio buffers back.

---

## 🧠 Category II: Advanced AI Brain & Cognitive Upgrades

### 7. Graph Database Memory System (Neo4j / SQLite Graph)
* **Description**: Replaces flat facts with connected relationships. ARIA will know not just that "John is a programmer", but that "John works with Priya at Acme Corp, which uses GitHub, and Priya hates late replies".
* **Code Connection**: Modifies the `Memory` database model in [models.py](file:///d:/ARIA/api/db/models.py#L277) and refactors `api/llm/personal_context.py` to run graph queries.
* **Data Flow**:
  ```
  [User Message] ──> [Memory Extractor] ──> [Graph Update (Cypher/SQL)] ──> [Entity Node Map]
  ```
* **Contributor Checkpoints**:
  - [ ] Design a Graph schema with nodes (`Person`, `Organization`, `Preference`, `Skill`) and edges (`WORKS_WITH`, `LIKES`, `BELONGS_TO`).
  - [ ] Implement a lightweight SQLite-based graph library (like `sqlite-utils` graph helper) or Neo4j driver client.
  - [ ] Update [memory_extractor.py](file:///d:/ARIA/api/llm/memory_extractor.py) to output relational triples: `(Subject, Predicate, Object)`.
  - [ ] Rebuild [personal_context.py](file:///d:/ARIA/api/llm/personal_context.py) to fetch 2-hop neighbor nodes of extracted entities for the system prompt.

### 8. Vector Database Semantic Search (pgvector Integration)
* **Description**: Allows ARIA to do deep semantic searches across all stored emails, notes, and messages instead of raw keyword matching, supporting queries like "What did we decide about the hosting budget?"
* **Code Connection**: Integrates `pgvector` into the PostgreSQL container and updates [models.py](file:///d:/ARIA/api/db/models.py). Modifies [search_handler.py](file:///d:/ARIA/api/handlers/search_handler.py) and [search_service.py](file:///d:/ARIA/api/services/search_service.py).
* **Data Flow**:
  ```
  [Inbound Message/Note] ──> [Embedding Model (FastAPI/Local)] ──> [Vector Column in PG]
  ```
* **Contributor Checkpoints**:
  - [ ] Update `docker-compose.yml` to use a pgvector-compatible PostgreSQL image (`ankane/pgvector`).
  - [ ] Add vector columns to `Message` and `Note` tables via Alembic migrations.
  - [ ] Set up an embedding generation client in the LLM service folder (supporting OpenAI, HuggingFace, or local Ollama embeddings).
  - [ ] Implement a cosine similarity query route in `search_service.py` to fetch top-k context.

### 9. Multi-Modal Vision and File Agent
* **Description**: Allows ARIA to accept and analyze images, PDFs, and spreadsheets. Users can send a screenshot of a bug or a PDF invoice, and ARIA will inspect it, extract data, and save it.
* **Code Connection**: Modifies [inbound.py](file:///d:/ARIA/api/workers/inbound.py)'s message handling flow where attachments are processed and stored in MinIO.
* **Data Flow**:
  ```
  [Telegram Photo/Doc] ──> [inbound.py] ──> [MinIO Storage] ──> [Groq Vision LLaMA 3.2] ──> [Parsed Data Saved]
  ```
* **Contributor Checkpoints**:
  - [ ] Update the attachment downloader in [minio_service.py](file:///d:/ARIA/api/services/minio_service.py) to extract file extensions and formats.
  - [ ] Add a PDF text extractor (e.g. using `pypdf` or `pdfplumber`) to convert text documents directly to context.
  - [ ] Integrate Groq's multi-modal model (like `llama-3.2-11b-vision-preview`) in [client.py](file:///d:/ARIA/api/llm/client.py).
  - [ ] Modify the inbound processor to send images to the vision model when the user asks questions about them.

### 10. Proactive Follow-up & Autopilot Routines
* **Description**: An autonomous background agent that periodically inspects the outbox, alerts the user to unanswered queries, suggests follow-ups, and drafts emails or messages ahead of time.
* **Code Connection**: Extends [followup.py](file:///d:/ARIA/api/workers/followup.py) and schedules a periodic cron task in `api/workers/settings.py`.
* **Data Flow**:
  ```
  [Cron Trigger] ──> [Scan Database] ──> [Select Needs Reply & No Response] ──> [Draft Reply] ──> [Send Notification]
  ```
* **Contributor Checkpoints**:
  - [ ] Add a background cron schedule for `analyze_unanswered_threads` running every 4 hours.
  - [ ] Write SQL queries to find contacts where `last_seen` was outbound and no message has been received since `follow_up_days` passed.
  - [ ] Integrate a drafting prompt that creates a gentle reminder message tailored to the contact's style.
  - [ ] Send the drafted reminder to the user as a Telegram notification with button options: `[Send Now]`, `[Edit]`, `[Ignore]`.

### 11. LangGraph Multi-Agent Routing Engine
* **Description**: Replaces the basic intent dispatcher with an advanced stateful agent graph. This allows ARIA to execute complex, multi-step agent conversations and coordinate work between specialized agents.
* **Code Connection**: Extends [supervisor.py](file:///d:/ARIA/api/agents/supervisor.py), [base_agent.py](file:///d:/ARIA/api/agents/base_agent.py), and replaces [router.py](file:///d:/ARIA/api/handlers/router.py).
* **Data Flow**:
  ```
  [User Intent] ──> [Supervisor Node] ──> [Specialized Agent Nodes] ──> [LangGraph State Compilation] ──> [Result]
  ```
* **Contributor Checkpoints**:
  - [ ] Add `langgraph` package to `requirements.txt`.
  - [ ] Define the global system state class using Pydantic or Python Dataclasses.
  - [ ] Create nodes for existing agents (`inbox`, `dev`) and newly proposed agents.
  - [ ] Wire up conditional edges, compile the state graph, and expose it through the dispatcher.

### 12. Playwright Web Browsing & Research Agent
* **Description**: Empowers ARIA to search the web, visit pages, extract information, and bypass paywalls or captchas to perform deep research (e.g., booking flights, finding documentation, summarizing papers).
* **Code Connection**: Invokes a new tool in the agent registry. Utilizes [websearch_handler.py](file:///d:/ARIA/api/handlers/websearch_handler.py).
* **Data Flow**:
  ```
  [Research Query] ──> [Websearch Handler] ──> [Playwright Microservice] ──> [Markdown Content] ──> [LLM Digest]
  ```
* **Contributor Checkpoints**:
  - [ ] Add a Playwright docker service or install Playwright binaries inside the worker container.
  - [ ] Create `api/services/browser_service.py` to handle async page loading, element clicking, and HTML scraping.
  - [ ] Add a search engine API wrapper (like SearXNG, Tavily, or Google Custom Search).
  - [ ] Implement a text chunking and extraction script to retrieve relevant page sections without blowing up LLM context.

---

## 🔌 Category III: Deep Digital & Physical Integrations

### 13. Smart Calendar Scheduling & Meeting Auto-Negotiator
* **Description**: Connects to Google Calendar or Outlook and uses natural language to coordinate meetings. It reads schedules, suggests times, emails contacts, and registers meetings automatically.
* **Code Connection**: Builds on the existing [calendar_service.py](file:///d:/ARIA/api/services/calendar_service.py) and [schedule_handler.py](file:///d:/ARIA/api/handlers/schedule_handler.py).
* **Data Flow**:
  ```
  "Schedule coffee with Priya" ──> [schedule_handler] ──> [Find free slots] ──> [Email Priya draft] ──> [Book slot]
  ```
* **Contributor Checkpoints**:
  - [ ] Implement OAuth credential handling for Google Calendar API and Microsoft Graph API.
  - [ ] Write a slot finder that checks calendars for conflicts and extracts block times.
  - [ ] Implement an email coordination prompt that composes calendar-booking invitations.
  - [ ] Add timezone adjustment logic to schedule meetings correctly across varying user locations.

### 14. Plaid Finance Integration & Automatic Bookkeeping
* **Description**: Replaces manual expense logging. Connects to the Plaid API to fetch real bank transactions, categorize them automatically, track monthly budgets, and send low-balance alerts.
* **Code Connection**: Connects to [expense_handler.py](file:///d:/ARIA/api/handlers/expense_handler.py) and reads/writes to the `Expense` model in [models.py](file:///d:/ARIA/api/db/models.py#L183).
* **Data Flow**:
  ```
  [Plaid Bank Hook] ──> [FastAPI Endpoint] ──> [LLM Transaction Classifier] ──> [Write to DB] ──> [Telegram Digest]
  ```
* **Contributor Checkpoints**:
  - [ ] Add Plaid SDK credentials and client initialization code.
  - [ ] Set up the webhook listener route `/webhook/plaid` to capture incoming bank events.
  - [ ] Build a categorization module that groups transactions (e.g. food, bills, travel) using an LLM.
  - [ ] Add budget limit checking and notify the user if they exceed categories.

### 15. Home Assistant IoT Smart Home Gateway
* **Description**: Allows physical world controls via natural language (e.g., "Aria, turn off the living room lights and set the AC to 22").
* **Code Connection**: Connects via a new `api/services/home_assistant.py` and registers a `home_assistant` intent.
* **Data Flow**:
  ```
  "Turn off bedroom lights" ──> [NLU] ──> [HA Service Client] ──(REST API)──> [Physical Light State Change]
  ```
* **Contributor Checkpoints**:
  - [ ] Store the Home Assistant URL and Long-Lived Access Token in config variables.
  - [ ] Create a service file to query the Home Assistant entity registry (`/api/states`).
  - [ ] Build a state control command wrapper to dispatch entity services (`/api/services/light/turn_off`).
  - [ ] Add a confirmation message to be sent to the user after commands execute successfully.

### 16. Auto-DevOps GitHub Code Reviewer & Repository Assistant
* **Description**: Expands the Dev Agent. ARIA will monitor pull requests, run linting or test scripts, post review summaries, and compile project builds automatically.
* **Code Connection**: Connects via [github_handler.py](file:///d:/ARIA/api/handlers/github_handler.py) and [github_service.py](file:///d:/ARIA/api/services/github_service.py).
* **Data Flow**:
  ```
  [PR Opened Webhook] ──> [FastAPI] ──> [Dev Agent] ──> [Run Local Tests] ──> [Post GitHub Comment]
  ```
* **Contributor Checkpoints**:
  - [ ] Set up GitHub webhook routing for events: `pull_request`, `push`, `workflow_job`.
  - [ ] Implement a checkout script that pulls code changes into a temporary local directory.
  - [ ] Add subprocess executor to run test commands (e.g. `pytest`, `npm test`) inside container.
  - [ ] Build a code review generator that comments directly on target code lines using the GitHub REST API.

### 17. News Curation & Intelligent Feeds Agent
* **Description**: Scrapes HackerNews, Reddit, Substack, and RSS feeds for keywords you track, filters out clickbait, and delivers a daily summary of high-value industry updates.
* **Code Connection**: Connects to [news_scraper.py](file:///d:/ARIA/api/services/news_scraper.py), [reddit_service.py](file:///d:/ARIA/api/services/reddit_service.py), [hn_service.py](file:///d:/ARIA/api/services/hn_service.py), and [rss_service.py](file:///d:/ARIA/api/services/rss_service.py).
* **Data Flow**:
  ```
  [Cron Trigger] ──> [Poll RSS/HN/Reddit] ──> [Filter Keywords] ──> [LLM Summarize] ──> [Morning Briefing]
  ```
* **Contributor Checkpoints**:
  - [ ] Add Substack RSS scraping functions to retrieve newsletters.
  - [ ] Implement duplicate detection and deduplication to prevent showing identical news stories.
  - [ ] Build a semantic scoring filter that scores headlines (1-10) for relevance before showing them.
  - [ ] Integrate feed summaries into [briefing.py](file:///d:/ARIA/api/workers/briefing.py)'s final output.

### 18. Gmail Auto-Drafting & Smart Replies Pipeline
* **Description**: Automatically reviews incoming high-priority emails, drafts appropriate response messages, and queues them in Gmail's draft folder for user approval.
* **Code Connection**: Interfaces with [gmail_service.py](file:///d:/ARIA/api/services/gmail_service.py) and the `Outbox` model.
* **Data Flow**:
  ```
  [Important Email] ──> [ARQ Worker] ──> [Generate Draft] ──(Gmail API)──> [Saved to Drafts Folder] ──> [Notify User]
  ```
* **Contributor Checkpoints**:
  - [ ] Implement `create_draft` in `gmail_service.py` using Google API Client.
  - [ ] Build email reply templates that inherit user preferences (from `UserProfile`).
  - [ ] Add the draft link directly to the Telegram notification button (`[Approve & Send]`, `[View Draft]`).
  - [ ] Add automatic threading headers (`In-Reply-To`, `References`) to draft payloads.

### 19. Unified Social Media Manager & Publisher
* **Description**: Schedule and post updates across X (Twitter), LinkedIn, and Discord. You can say: "Aria, post to X and LinkedIn that our v3 build is live with a link to the repo".
* **Code Connection**: Exposes new services: `twitter_service.py`, `linkedin_service.py`.
* **Data Flow**:
  ```
  "Post to X: hello world" ──> [Intent Parser] ──> [Social Media Router] ──> [Platform SDKs] ──> [Live Post]
  ```
* **Contributor Checkpoints**:
  - [ ] Add Twitter API v2 and LinkedIn OAuth client integrations.
  - [ ] Create a unified payload format for text, image links, and tagging references.
  - [ ] Implement an approval step for posting to prevent accidental posts.
  - [ ] Build scheduling hooks to schedule posts for later execution.

### 20. Multi-Device Spotify control & Smart Playlist Generator
* **Description**: Extends the basic Spotify control. Allows users to transfer playback between devices, search playlists, search tracks, create mood playlists, and request context-based song additions.
* **Code Connection**: Extends [spotify_service.py](file:///d:/ARIA/api/services/spotify_service.py) and [spotify_handler.py](file:///d:/ARIA/api/handlers/spotify_handler.py).
* **Data Flow**:
  ```
  "Play lo-fi on Living Room speaker" ──> [Spotify API Search Devices] ──> [Transfer Playback] ──> [Play URI]
  ```
* **Contributor Checkpoints**:
  - [ ] Implement active device polling using the `/v1/me/player/devices` Spotify endpoint.
  - [ ] Add device name resolution to allow mapping name strings (e.g. "TV speaker") to device IDs.
  - [ ] Build a contextual playlist compiler based on query mood ("Focus music", "Workout tracks").
  - [ ] Add current playback telemetry parsing (e.g. track name, progress bar) for dashboard display.

---

## 👥 Category IV: Collaboration & Multi-Tenant Scaling

### 21. Multi-Tenant Workspace Partitioning
* **Description**: Allows hosting ARIA for multiple users on the same infrastructure, keeping databases, secrets, keys, and configurations isolated.
* **Code Connection**: Modifies `postgres_user` and settings in [config.py](file:///d:/ARIA/api/core/config.py) and updates all database queries to include a `tenant_id` filter.
* **Data Flow**:
  ```
  [User Update] ──> [Extract Tenant JWT] ──> [FastAPI Route Filter] ──> [Isolated DB Query]
  ```
* **Contributor Checkpoints**:
  - [ ] Add a `tenants` model to hold user account secrets and settings.
  - [ ] Include a foreign key `tenant_id` across database tables (`messages`, `contacts`, `notes`, `expenses`).
  - [ ] Refactor FastAPI request states to verify tenant authorization headers.
  - [ ] Update background workers to fetch parameters using task tenant context keys.

### 22. Guest Access & Shared Household Calendars
* **Description**: Allows giving family members or colleagues limited access to ARIA. They can query shared calendars or add items to lists without accessing private emails.
* **Code Connection**: Modifies access control filters in [telegram.py](file:///d:/ARIA/api/routes/telegram.py#L75) and [telegram_processor.py](file:///d:/ARIA/api/workers/telegram_processor.py).
* **Data Flow**:
  ```
  [Guest Telegram Message] ──> [Verify Sender ID] ──> [Restrict Intent Options] ──> [Execute Safe Handler]
  ```
* **Contributor Checkpoints**:
  - [ ] Build a `GuestUser` table mapping guest chat IDs to allowed tools.
  - [ ] Modify the access validation middleware to support a list of authorized IDs instead of a single ID.
  - [ ] Implement role-based scopes (e.g., `guest:read:calendar`, `guest:write:grocery_list`).
  - [ ] Filter out sensitive items (e.g., bank expenses, emails) from search results if queried by guest accounts.

### 23. Granular Role-Based Access Control (RBAC) & Biometric Verification
* **Description**: Protects sensitive actions (like deleting code, transferring funds, or fetching emails) by requiring face ID/fingerprint authorization or a secondary verification code via a mobile companion app.
* **Code Connection**: Connects to the Telegram Webhook handler and integrates with the mobile companion app auth gateway.
* **Data Flow**:
  ```
  [Sensitive Action Requested] ──> [Send FCM Push to Mobile] ──> [Verify Fingerprint] ──> [Release Action Lock]
  ```
* **Contributor Checkpoints**:
  - [ ] Define high-risk intents in a configuration list (e.g., `github:merge`, `finance:transfer`).
  - [ ] Create an action lock table in the database to hold pending operations.
  - [ ] Implement push-to-verify requests that prompt for validation on registered devices.
  - [ ] Release action locks and proceed with task execution upon receiving validation confirmation.

### 24. Multi-Channel Conversation State Synchronizer
* **Description**: Keeps conversation states, chat history, and contexts synced. If you start a chat on the web dashboard, you can continue it on Telegram or Discord without losing context.
* **Code Connection**: Links the Redis conversation caching in [conversation_service.py](file:///d:/ARIA/api/services/conversation_service.py) to a unified state provider.
* **Data Flow**:
  ```
  [Web Chat Response] ──> [Write to Redis Session] ──> [Sync to Telegram/Discord thread]
  ```
* **Contributor Checkpoints**:
  - [ ] Redesign conversation session keys to use a global user identifier instead of a channel-specific ID.
  - [ ] Build a synchronization router that forwards notifications and updates across all configured channels.
  - [ ] Implement cross-channel typing indicators to show activity status.
  - [ ] Support transferring media files from one channel directly to other active sessions.

---

## 🛡️ Category V: Security, Privacy, & Enterprise Infrastructure

### 25. Local LLM Air-Gapped Mode (Ollama / vLLM Integration)
* **Description**: Allows running ARIA completely offline using local models (like LLaMA-3-8B or Mistral-7B via Ollama), removing dependencies on external APIs like Groq for enhanced privacy.
* **Code Connection**: Modifies the ChatGroq model client in [client.py](file:///d:/ARIA/api/llm/client.py) and [base_agent.py](file:///d:/ARIA/api/agents/base_agent.py#L36).
* **Data Flow**:
  ```
  [User Message] ──> [Local LLM Route] ──(Ollama API)──> [Local LLaMA Model Inference] ──> [Response]
  ```
* **Contributor Checkpoints**:
  - [ ] Add configurations to support local base URLs and local model names.
  - [ ] Create a fallback mechanism: use Groq when online, use Ollama/Local when offline.
  - [ ] Add an Ollama container orchestration template to the `docker-compose.yml` file.
  - [ ] Benchmark local model outputs to adjust system prompts for smaller context sizes.

### 26. Database Envelope Encryption (AES-256-GCM)
* **Description**: Encrypts sensitive fields (like note bodies, emails, credentials, and expenses) in the database using AES-GCM before writing to disk, protecting your data even if the DB is compromised.
* **Code Connection**: Modifies SQLAlchemy models in [models.py](file:///d:/ARIA/api/db/models.py) and uses a cryptographically secure key provider.
* **Data Flow**:
  ```
  [Raw Note Content] ──(AES Key/Encrypt)──> [Encrypted Binary Data] ──> [PostgreSQL Commit]
  ```
* **Contributor Checkpoints**:
  - [ ] Add the `cryptography` library to dependencies.
  - [ ] Create an encryption utility class to handle key derivation and encrypt/decrypt functions.
  - [ ] Define custom SQLAlchemy column types (e.g. `EncryptedText`) that encrypt data on save and decrypt it on load.
  - [ ] Use a secure environment variable or hardware key module to manage master keys.

### 27. Distributed Task Worker Queue Scaling
* **Description**: Replaces the single worker setup with a distributed worker pool, separating quick tasks (like sending notifications) from heavy tasks (like scraping or image processing) to prevent queue bottlenecks.
* **Code Connection**: Refactors configuration files in [settings.py](file:///d:/ARIA/api/workers/settings.py) and changes worker startup flags.
* **Data Flow**:
  ```
                 ┌──> [Fast Worker Queue] ──> [Notifications / Webhooks]
  [Redis Broker] ┼──> [Slow Worker Queue] ──> [Web Scraping / Research]
                 └──> [Heavy Worker Queue] ──> [Vision / Embeddings]
  ```
* **Contributor Checkpoints**:
  - [ ] Define distinct queues (e.g., `high`, `default`, `low`) inside the Redis client settings.
  - [ ] Update the `enqueue` function to route tasks to appropriate queues based on priority.
  - [ ] Update `docker-compose.yml` to launch separate worker containers pointing to specific queues.
  - [ ] Set up auto-scaling scripts to spin up additional workers as queue sizes grow.

### 28. Sandboxed Code Execution Engine (WebAssembly/gVisor)
* **Description**: Allows ARIA to safely run Python scripts, compile code, and run system tasks in a secure, sandboxed container (like gVisor or WebAssembly) without risking the host machine.
* **Code Connection**: Integrates with [dev_agent.py](file:///d:/ARIA/api/agents/dev_agent.py) to enable code testing and execution capabilities.
* **Data Flow**:
  ```
  "Execute python: print(1+1)" ──> [dev_agent] ──> [Sandboxed WASM Runtime] ──> [Return stdout]
  ```
* **Contributor Checkpoints**:
  - [ ] Build a microservice wrapper around WebAssembly runtime (Wasmtime) or a secure gVisor container.
  - [ ] Implement timeout constraints and resource limits (e.g., maximum memory, CPU caps) for scripts.
  - [ ] Build a file system mock layer to protect local project files from modification during test runs.
  - [ ] Route code outputs back to the chat response window.

### 29. System Telemetry & Grafana Monitoring Dashboard
* **Description**: Real-time performance tracking. Monitor webhook response times, intent parsing accuracy, queue delays, API rates, database query performance, and cache hit rates in a Grafana dashboard.
* **Code Connection**: Integrates Prometheus instrumentation middleware in [main.py](file:///d:/ARIA/api/main.py).
* **Data Flow**:
  ```
  [FastAPI Request] ──> [Prometheus Metrics] ──> [Prometheus Server] ──> [Grafana Dashboard]
  ```
* **Contributor Checkpoints**:
  - [ ] Add the `prometheus-fastapi-instrumentator` package to backend dependencies.
  - [ ] Expose a secure `/metrics` endpoint in FastAPI.
  - [ ] Create a Prometheus configuration template to scrape backend logs.
  - [ ] Build a Grafana dashboard JSON model displaying telemetry (latencies, queue sizes, cache metrics).

### 30. Self-Healing Integration Agent & Webhook Auto-Recovery
* **Description**: Automatically detects and recovers from broken connections, session logouts, expired tokens, or webhook failures across Gmail, WhatsApp, and Slack integrations.
* **Code Connection**: Integrates with the health check system in [main.py](file:///d:/ARIA/api/main.py#L120) and background monitoring workers.
* **Data Flow**:
  ```
  [Health Check Failure] ──> [Self-Healing Agent] ──> [Re-auth Loop / Refresh Token] ──> [System Online]
  ```
* **Contributor Checkpoints**:
  - [ ] Build a background monitor that checks integration status endpoints (e.g., Baileys session state, Gmail watch expiration).
  - [ ] Write repair actions (e.g. trigger OAuth refresh token requests, reload WhatsApp session sockets).
  - [ ] Send alert notifications if an issue requires user intervention (such as scanning a new QR code).
  - [ ] Log healing attempts and outcomes to track stability trends.

---

## 🚀 Execution & Phase checkpoints

### Phase 1: Foundations & pgvector (Short-term)
- [ ] Connect pgvector and implement Semantic Search.
- [ ] Build the Next.js admin dashboard framework.
- [ ] Complete local Ollama testing for air-gapped support.

### Phase 2: Platform Extension (Medium-term)
- [ ] Build the Tauri desktop shortcut widget and Chrome Extension.
- [ ] Implement the mobile app with FCM push notifications.
- [ ] Enhance the Dev Agent with GitHub webhook reviews and Playwright scraping.

### Phase 3: Autonomous Jarvis (Long-term)
- [ ] Deploy the Neo4j Graph database memory model.
- [ ] Deploy the gVisor sandbox environment for custom code execution.
- [ ] Complete multi-tenant isolation and the self-healing integration agent.

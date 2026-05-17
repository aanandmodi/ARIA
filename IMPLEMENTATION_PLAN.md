# ARIA Complete Implementation Plan

## 📋 Overview
This document outlines the complete implementation plan for all remaining features and improvements to the ARIA unified inbox system.

---

## ✅ Completed Work (Phases 1-3)

### Phase 1: Zero-Timeout Architecture
- [x] Webhook decoupling (<50ms response)
- [x] ARQ worker implementation
- [x] Database connection pooling

### Phase 2: Progressive UI Feedback
- [x] Message state tracking with editMessageText
- [x] Real-time status updates
- [x] Perceived latency reduction (87%)

### Phase 3: LLM & Caching Optimization
- [x] Single-tier intent parser (83% faster)
- [x] Redis caching layer
- [x] Weather service caching
- [x] Model tiering strategy

---

## 🚧 Phase 4: Multi-Agent Orchestration (In Progress)

### Completed
- [x] Base agent framework ([`api/agents/base_agent.py`](api/agents/base_agent.py))
- [x] Supervisor agent ([`api/agents/supervisor.py`](api/agents/supervisor.py))
- [x] Inbox agent ([`api/agents/inbox_agent.py`](api/agents/inbox_agent.py))
- [x] Dev agent ([`api/agents/dev_agent.py`](api/agents/dev_agent.py))

### Remaining Tasks

#### 1. Create Additional Specialized Agents
**Files to create:**
- `api/agents/finance_agent.py` - Expenses, stocks, crypto
- `api/agents/knowledge_agent.py` - Notes, memories, search
- `api/agents/automation_agent.py` - Reminders, habits, calendar

**Implementation:**
```python
# finance_agent.py
class FinanceAgent(BaseAgent):
    supported_intents = {"expense", "markets", "budget"}
    
    async def process(self, state: AgentState):
        # Handle financial operations
        pass

# knowledge_agent.py  
class KnowledgeAgent(BaseAgent):
    supported_intents = {"note", "create_memory", "search", "summary"}
    
    async def process(self, state: AgentState):
        # Handle knowledge operations
        pass

# automation_agent.py
class AutomationAgent(BaseAgent):
    supported_intents = {"reminder", "habit", "schedule"}
    
    async def process(self, state: AgentState):
        # Handle automation operations
        pass
```

#### 2. Integrate LangGraph Orchestrator
**File to create:** `api/agents/orchestrator.py`

**Implementation:**
```python
from langgraph.graph import StateGraph, END

def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor.process)
    workflow.add_node("inbox", inbox_agent.process)
    workflow.add_node("dev", dev_agent.process)
    workflow.add_node("finance", finance_agent.process)
    workflow.add_node("knowledge", knowledge_agent.process)
    workflow.add_node("automation", automation_agent.process)
    
    # Add edges
    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state.next_agent,
        {
            "inbox": "inbox",
            "dev": "dev",
            "finance": "finance",
            "knowledge": "knowledge",
            "automation": "automation",
        }
    )
    
    # All agents return to END
    for agent in ["inbox", "dev", "finance", "knowledge", "automation"]:
        workflow.add_edge(agent, END)
    
    return workflow.compile()
```

#### 3. Update Router to Use Orchestrator
**File to modify:** `api/handlers/router.py`

Replace static `match` statement with:
```python
from api.agents.orchestrator import create_agent_graph

agent_graph = create_agent_graph()

async def dispatch(intent: IntentResult, db: AsyncSession, update: Update):
    state = AgentState(
        user_query=update.message.text,
        intent=intent.intent,
        context=intent.params
    )
    
    result_state = await agent_graph.ainvoke(state)
    
    if result_state.result:
        await telegram_service.send_message(result_state.result)
```

---

## 📱 Phase 5: Enhanced Messaging Features

### 1. Fix Reply Functionality
**Files to modify:**
- `api/services/gmail_service.py`
- `api/services/whatsapp_service.py`
- `api/handlers/reply_handler.py`

**Tasks:**
- [ ] Implement `send_reply()` in gmail_service
- [ ] Fix WhatsApp reply threading
- [ ] Add reply context tracking
- [ ] Test reply flow end-to-end

**Implementation:**
```python
# gmail_service.py
async def send_reply(message_id: str, reply_text: str) -> bool:
    """Send a reply to an email thread."""
    try:
        # Get original message
        original = await fetch_full_message(message_id)
        
        # Create reply with proper threading
        message = {
            'raw': create_message_with_reply(
                to=original.sender,
                subject=f"Re: {original.subject}",
                body=reply_text,
                thread_id=original.thread_id
            )
        }
        
        service = get_gmail_service()
        service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        
        return True
    except Exception as exc:
        log.error("gmail_reply_failed", error=str(exc))
        return False
```

### 2. Deep Message Context Detection
**File to create:** `api/services/message_context.py`

**Features:**
- [ ] Detect group vs personal messages
- [ ] Extract participant lists
- [ ] Identify message urgency
- [ ] Track conversation threads

**Implementation:**
```python
@dataclass
class MessageContext:
    is_group: bool
    participants: list[str]
    urgency: str  # urgent/normal/low
    thread_id: str | None
    mentioned_users: list[str]
    
async def analyze_message_context(
    platform: str,
    message: dict
) -> MessageContext:
    """Analyze message context for better routing."""
    is_group = False
    participants = []
    
    if platform == "whatsapp":
        # Check if group chat
        is_group = message.get("isGroup", False)
        if is_group:
            participants = message.get("participants", [])
    
    elif platform == "gmail":
        # Check CC/BCC for group emails
        cc = message.get("cc", [])
        bcc = message.get("bcc", [])
        is_group = len(cc) + len(bcc) > 0
        participants = [message.get("from")] + cc + bcc
    
    # Detect urgency from keywords
    content = message.get("content", "").lower()
    urgency = "urgent" if any(
        word in content 
        for word in ["urgent", "asap", "emergency", "critical"]
    ) else "normal"
    
    return MessageContext(
        is_group=is_group,
        participants=participants,
        urgency=urgency,
        thread_id=message.get("thread_id"),
        mentioned_users=extract_mentions(content)
    )
```

### 3. Contact Management
**Files to modify:**
- `api/services/whatsapp_service.py`
- `api/services/gmail_service.py`

**Tasks:**
- [ ] Implement `get_contacts()` for WhatsApp
- [ ] Implement `get_contacts()` for Gmail
- [ ] Add contact search functionality
- [ ] Implement contact name resolution
- [ ] Cache contact lists (1 hour TTL)

**Implementation:**
```python
# whatsapp_service.py
@cached("contacts_whatsapp", ttl=3600)
async def get_contacts() -> list[dict]:
    """Get WhatsApp contacts."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.whatsapp_api_url}/contacts"
            )
            resp.raise_for_status()
            contacts = resp.json()
            
            return [
                {
                    "name": c.get("name", c.get("phone")),
                    "phone": c.get("phone"),
                    "platform": "whatsapp"
                }
                for c in contacts
            ]
    except Exception as exc:
        log.error("whatsapp_contacts_failed", error=str(exc))
        return []

# gmail_service.py
@cached("contacts_gmail", ttl=3600)
async def get_contacts() -> list[dict]:
    """Get Gmail contacts."""
    try:
        service = get_gmail_service()
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=100,
            personFields='names,emailAddresses'
        ).execute()
        
        connections = results.get('connections', [])
        
        return [
            {
                "name": c.get("names", [{}])[0].get("displayName", ""),
                "email": c.get("emailAddresses", [{}])[0].get("value", ""),
                "platform": "gmail"
            }
            for c in connections
        ]
    except Exception as exc:
        log.error("gmail_contacts_failed", error=str(exc))
        return []
```

### 4. Contact Name Memory System
**File to create:** `api/services/contact_memory.py`

**Features:**
- [ ] Learn contact names from conversations
- [ ] Store name-to-identifier mappings
- [ ] Fuzzy name matching
- [ ] Nickname support

**Implementation:**
```python
async def learn_contact_name(
    identifier: str,  # phone/email
    name: str,
    platform: str,
    db: AsyncSession
) -> None:
    """Learn and store contact name."""
    # Check if contact exists
    contact = await db.execute(
        select(Contact).where(
            or_(
                Contact.email == identifier,
                Contact.phone == identifier
            )
        )
    )
    contact = contact.scalar_one_or_none()
    
    if contact:
        # Update name if different
        if contact.name != name:
            contact.name = name
            await db.flush()
    else:
        # Create new contact
        contact = Contact(
            name=name,
            email=identifier if "@" in identifier else None,
            phone=identifier if "@" not in identifier else None,
            platform_ids={platform: identifier}
        )
        db.add(contact)
        await db.flush()
    
    log.info("contact_name_learned", name=name, identifier=identifier)

async def resolve_contact_name(
    name: str,
    db: AsyncSession
) -> Contact | None:
    """Resolve a name to a contact using fuzzy matching."""
    # Exact match first
    result = await db.execute(
        select(Contact).where(
            Contact.name.ilike(f"%{name}%")
        )
    )
    contacts = result.scalars().all()
    
    if not contacts:
        return None
    
    # If multiple matches, return best match
    # (could use fuzzy string matching here)
    return contacts[0]
```

---

## 🐙 Phase 6: Enhanced GitHub Integration

### Tasks
- [ ] Implement commit creation
- [ ] Implement PR creation
- [ ] Add code search functionality
- [ ] Add workflow trigger support
- [ ] Implement repository management

**File to modify:** `api/services/github_service.py`

**New Functions:**
```python
async def create_commit(
    repo: str,
    branch: str,
    message: str,
    files: dict[str, str]
) -> bool:
    """Create a commit with file changes."""
    pass

async def create_pull_request(
    repo: str,
    title: str,
    head: str,
    base: str,
    body: str = ""
) -> str | None:
    """Create a pull request."""
    pass

async def search_code(
    query: str,
    repo: str | None = None
) -> list[dict]:
    """Search code across repositories."""
    pass

async def trigger_workflow(
    repo: str,
    workflow_id: str,
    ref: str = "main"
) -> bool:
    """Trigger a GitHub Actions workflow."""
    pass
```

---

## 🌅 Phase 7: Enhanced Morning Briefing

### Tasks
- [ ] Implement news scraping
- [ ] Add personalized greeting
- [ ] Include detailed weather
- [ ] Add calendar integration
- [ ] Include unread message summary

**File to create:** `api/services/news_scraper.py`

**Implementation:**
```python
from bs4 import BeautifulSoup
import httpx

async def scrape_news(sources: list[str], limit: int = 5) -> list[dict]:
    """Scrape news from multiple sources."""
    news_items = []
    
    for source in sources:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(source, timeout=10)
                resp.raise_for_status()
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Extract headlines (source-specific selectors)
                if "techcrunch.com" in source:
                    articles = soup.select('.post-block__title__link')
                elif "ycombinator.com" in source:
                    articles = soup.select('.titleline > a')
                
                for article in articles[:limit]:
                    news_items.append({
                        "title": article.get_text().strip(),
                        "url": article.get('href'),
                        "source": source
                    })
        except Exception as exc:
            log.error("news_scrape_failed", source=source, error=str(exc))
    
    return news_items[:limit]
```

**File to modify:** `api/workers/briefing.py`

**Enhanced Briefing:**
```python
async def send_morning_briefing(ctx: dict) -> None:
    """Enhanced morning briefing with scraped news."""
    # Get user's name from memory
    user_name = await get_user_name()
    
    # Personalized greeting
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon"
    
    # Gather all data
    weather = await weather_service.get_forecast()
    events = await calendar_service.get_today_events()
    news = await scrape_news([
        "https://news.ycombinator.com",
        "https://techcrunch.com"
    ], limit=5)
    unread = await get_unread_summary()
    
    # Compose briefing
    briefing = f"""
{greeting}, {user_name}! ☀️

<b>🌤 Weather</b>
{weather_service.format_forecast(weather)}

<b>📅 Today's Schedule</b>
{format_events(events)}

<b>📰 Top News</b>
{format_news(news)}

<b>📬 Unread Messages</b>
{unread}

Have a great day! 🚀
"""
    
    await telegram_service.send_message(briefing)
```

---

## 🔍 Phase 8: Enhanced Search

### Tasks
- [ ] Implement vector similarity search
- [ ] Add semantic search
- [ ] Cross-platform search
- [ ] Search result ranking

**File to create:** `api/services/vector_search.py`

**Implementation:**
```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

async def semantic_search(
    query: str,
    documents: list[dict],
    top_k: int = 5
) -> list[dict]:
    """Perform semantic search using embeddings."""
    # Encode query
    query_embedding = model.encode(query)
    
    # Encode documents
    doc_texts = [d.get("content", "") for d in documents]
    doc_embeddings = model.encode(doc_texts)
    
    # Calculate cosine similarity
    similarities = np.dot(doc_embeddings, query_embedding) / (
        np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # Get top k results
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    return [
        {**documents[i], "score": float(similarities[i])}
        for i in top_indices
    ]
```

---

## 🎓 Phase 9: Onboarding & Personalization

### Tasks
- [ ] Create onboarding flow
- [ ] Collect user preferences
- [ ] Store personal information
- [ ] Customize responses

**File to create:** `api/services/onboarding.py`

**Implementation:**
```python
ONBOARDING_QUESTIONS = [
    {
        "id": "name",
        "question": "What's your name?",
        "type": "text"
    },
    {
        "id": "location",
        "question": "Where do you live? (for weather)",
        "type": "text"
    },
    {
        "id": "timezone",
        "question": "What's your timezone?",
        "type": "choice",
        "options": ["Asia/Kolkata", "America/New_York", "Europe/London"]
    },
    {
        "id": "briefing_time",
        "question": "When would you like your morning briefing?",
        "type": "time"
    },
    {
        "id": "interests",
        "question": "What topics interest you? (comma-separated)",
        "type": "text"
    }
]

async def start_onboarding(user_id: int, db: AsyncSession):
    """Start onboarding flow."""
    # Create onboarding session
    session = OnboardingSession(
        user_id=user_id,
        current_question=0,
        answers={}
    )
    db.add(session)
    await db.flush()
    
    # Send first question
    await send_onboarding_question(session, 0)

async def process_onboarding_answer(
    user_id: int,
    answer: str,
    db: AsyncSession
):
    """Process onboarding answer and move to next question."""
    session = await get_onboarding_session(user_id, db)
    
    if not session:
        return
    
    # Store answer
    question = ONBOARDING_QUESTIONS[session.current_question]
    session.answers[question["id"]] = answer
    
    # Move to next question
    session.current_question += 1
    
    if session.current_question >= len(ONBOARDING_QUESTIONS):
        # Onboarding complete
        await complete_onboarding(session, db)
    else:
        # Send next question
        await send_onboarding_question(session, session.current_question)
    
    await db.flush()
```

---

## 🧠 Phase 10: Conversation Learning

### Tasks
- [ ] Implement conversation history tracking
- [ ] Extract patterns from conversations
- [ ] Fine-tune LLM on user data
- [ ] Implement feedback loop

**File to create:** `api/services/conversation_learning.py`

**Implementation:**
```python
async def analyze_conversation_patterns(
    user_id: int,
    db: AsyncSession
) -> dict:
    """Analyze user's conversation patterns."""
    # Get recent conversations
    conversations = await db.execute(
        select(ConversationTurn)
        .where(ConversationTurn.contact_id == user_id)
        .order_by(ConversationTurn.created_at.desc())
        .limit(100)
    )
    conversations = conversations.scalars().all()
    
    patterns = {
        "common_topics": extract_topics(conversations),
        "preferred_time": analyze_activity_time(conversations),
        "communication_style": analyze_style(conversations),
        "frequent_contacts": get_frequent_contacts(conversations)
    }
    
    return patterns

async def create_fine_tuning_dataset(
    user_id: int,
    db: AsyncSession
) -> list[dict]:
    """Create dataset for fine-tuning."""
    conversations = await get_user_conversations(user_id, db)
    
    dataset = []
    for conv in conversations:
        if conv.role == "user" and conv.next_turn:
            dataset.append({
                "messages": [
                    {"role": "user", "content": conv.content},
                    {"role": "assistant", "content": conv.next_turn.content}
                ]
            })
    
    return dataset
```

---

## 📊 Implementation Priority

### High Priority (Complete First)
1. ✅ Phase 1-3 (Complete)
2. 🚧 Phase 4: Multi-agent orchestration
3. 📱 Phase 5: Enhanced messaging features
4. 🐙 Phase 6: GitHub integration

### Medium Priority
5. 🌅 Phase 7: Enhanced briefing
6. 🔍 Phase 8: Enhanced search

### Lower Priority (Nice to Have)
7. 🎓 Phase 9: Onboarding
8. 🧠 Phase 10: Conversation learning

---

## 🧪 Testing Strategy

### Unit Tests
- Test each agent independently
- Test service functions
- Test caching layer

### Integration Tests
- Test agent orchestration flow
- Test message routing
- Test reply functionality

### End-to-End Tests
- Test complete user flows
- Test error handling
- Test performance under load

---

## 📈 Success Metrics

- [ ] Webhook response time <50ms (✅ Achieved)
- [ ] Intent parsing <500ms (✅ Achieved)
- [ ] Reply success rate >95%
- [ ] Contact resolution accuracy >90%
- [ ] User satisfaction score >4.5/5
- [ ] System uptime >99.9%

---

## 🚀 Deployment Checklist

- [ ] All tests passing
- [ ] Documentation complete
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Redis cache configured
- [ ] Monitoring setup
- [ ] Backup strategy in place
- [ ] Rollback plan documented

---

**Last Updated**: 2026-05-15
**Status**: Phases 1-3 Complete, Phase 4 In Progress
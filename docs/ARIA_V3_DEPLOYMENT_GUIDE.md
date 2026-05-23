# ARIA v3 — Deployment & Testing Guide

## 🚀 Quick Start: Get ARIA v3 Running

This guide will get your conversational ARIA bot running in **under 10 minutes**.

---

## ✅ Prerequisites Check

Before deploying, verify you have:

```bash
# 1. Docker & Docker Compose
docker --version  # Should be 20.10+
docker compose version  # Should be 2.0+

# 2. Environment variables set
cat .env | grep -E "GROQ_API_KEY|TELEGRAM_BOT_TOKEN|DATABASE_URL|REDIS_URL"

# 3. Services running
docker compose ps  # Should show postgres, redis, api, baileys
```

---

## 📦 Step 1: Apply Database Migration

The new schema adds critical fields for conversation memory and session tracking.

```bash
# Navigate to API directory
cd api

# Generate migration from model changes
alembic revision --autogenerate -m "v3_conversation_memory_and_sessions"

# Review the generated migration file
# It should add columns like:
# - user_profile.draft_mode
# - contacts.is_group, avg_response_hours, last_outbound_at
# - telegram_sessions.last_sender_id, last_sender_name, last_thread_id
# - reminders.repeat
# - notes.pinned, updated_at
# - outbox table (new)

# Apply migration
alembic upgrade head

# Verify migration succeeded
alembic current
# Should show: v3_conversation_memory_and_sessions (head)
```

**If migration fails:**
```bash
# Rollback
alembic downgrade -1

# Check what went wrong
alembic history --verbose

# Fix issues in migration file, then retry
alembic upgrade head
```

---

## 🔄 Step 2: Restart Services

```bash
# From project root
cd ..

# Rebuild API container (includes new code)
docker compose build api

# Restart all services
docker compose down
docker compose up -d

# Watch logs for errors
docker compose logs -f api
```

**Expected log output:**
```
api_1     | INFO:     Application startup complete.
api_1     | INFO:     Uvicorn running on http://0.0.0.0:8000
redis_1   | Ready to accept connections
postgres_1| database system is ready to accept connections
```

---

## 🧪 Step 3: Test Conversation Flow

### Test 1: First-Time Setup
```
You → Telegram Bot: "hi"
ARIA: "Nice to meet you, [YourName]! I'm ARIA, your personal AI assistant..."
```

**What's happening:**
- Bot detects no `UserProfile` exists
- Creates profile with your name
- Stores conversation turn in Redis

### Test 2: Context Memory
```
You: "remind me about dinner at 7pm"
ARIA: "⏰ Reminder set for 7:00 PM today..."

You: "actually make it 8pm"
ARIA: "✅ Updated reminder to 8:00 PM"
```

**What's happening:**
- First message stored in conversation history
- Second message uses history to understand "it" = dinner reminder
- `get_history()` retrieves context from Redis

### Test 3: Personal Context
```
You: "what's my name?"
ARIA: "Your name is [YourName]"
```

**What's happening:**
- `build_system_prompt()` injects user profile
- Groq receives: "User's name: [YourName]" in system prompt

### Test 4: Memory Extraction
```
You: "I prefer emails over calls"
ARIA: "Got it, I'll remember that"

[Later]
You: "how should I contact clients?"
ARIA: "Based on what you told me, you prefer emails over calls..."
```

**What's happening:**
- `extract_and_store()` runs after first exchange
- Creates `Memory` entry: "prefers emails over calls"
- `build_system_prompt()` retrieves this memory for second message

---

## 🔍 Step 4: Verify Core Components

### Check Conversation History (Redis)
```bash
# Connect to Redis
docker compose exec redis redis-cli

# Check if conversation is being stored
LRANGE aria:conv 0 -1
# Should show JSON objects with role/content

# Check conversation summary
GET aria:conv_summary
# Should show summary if >15 exchanges

# Exit Redis
exit
```

### Check Memories (PostgreSQL)
```bash
# Connect to database
docker compose exec postgres psql -U aria -d aria

# Check user profile
SELECT * FROM user_profile;
# Should show your name, timezone, preferences

# Check memories
SELECT entity_key, fact, confidence FROM memories ORDER BY created_at DESC LIMIT 10;
# Should show extracted facts

# Check conversation turns (backup)
SELECT role, LEFT(content, 50), created_at FROM conversation_turns ORDER BY created_at DESC LIMIT 10;

# Exit PostgreSQL
\q
```

### Check Logs for Errors
```bash
# API logs
docker compose logs api --tail=100 | grep -i error

# Should see NO errors related to:
# - groq_chat_failed
# - get_history_failed
# - build_system_prompt_failed
# - memory_extraction_failed (warnings OK, errors not OK)
```

---

## 🐛 Troubleshooting

### Issue: "Bot doesn't remember previous messages"

**Diagnosis:**
```bash
# Check Redis connection
docker compose exec api python -c "
from api.core.queue import get_redis
import asyncio
async def test():
    redis = await get_redis()
    await redis.ping()
    print('Redis OK')
asyncio.run(test())
"
```

**Fix:**
- Ensure Redis is running: `docker compose ps redis`
- Check Redis URL in `.env`: `REDIS_URL=redis://redis:6379/0`
- Restart services: `docker compose restart`

---

### Issue: "Bot gives generic responses, no personalization"

**Diagnosis:**
```bash
# Check if UserProfile exists
docker compose exec postgres psql -U aria -d aria -c "SELECT * FROM user_profile;"
```

**Fix:**
- If no profile: Send "hi" to bot to trigger setup
- If profile exists but no name: Send your name
- Check logs: `docker compose logs api | grep "build_system_prompt"`

---

### Issue: "Memory extraction not working"

**Diagnosis:**
```bash
# Check Groq API key
docker compose exec api python -c "
from api.core.config import settings
print(f'Groq API Key: {settings.groq_api_key[:10]}...')
"

# Check memory table
docker compose exec postgres psql -U aria -d aria -c "SELECT COUNT(*) FROM memories;"
```

**Fix:**
- Verify `GROQ_API_KEY` in `.env`
- Check Groq rate limits: https://console.groq.com/
- Memory extraction failures are logged as warnings (non-blocking)

---

### Issue: "Migration fails with 'column already exists'"

**Fix:**
```bash
# Check current schema
docker compose exec postgres psql -U aria -d aria -c "\d contacts"

# If column exists, skip that part of migration
# Edit migration file to remove duplicate column additions

# Or reset database (CAUTION: loses data)
docker compose down -v
docker compose up -d
cd api && alembic upgrade head
```

---

## 📊 Performance Monitoring

### Redis Memory Usage
```bash
# Check Redis memory
docker compose exec redis redis-cli INFO memory | grep used_memory_human

# Should be <50MB for normal usage
# If >100MB, conversation history might not be compressing
```

### Groq API Usage
```bash
# Count API calls in logs
docker compose logs api | grep "groq_chat" | wc -l

# Check for rate limit errors
docker compose logs api | grep "rate_limit"
```

### Database Size
```bash
# Check table sizes
docker compose exec postgres psql -U aria -d aria -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## 🎯 Success Criteria

Your ARIA v3 deployment is successful if:

- ✅ Bot responds to "hi" with personalized greeting
- ✅ Bot remembers your name across messages
- ✅ "what did I just say?" returns accurate context
- ✅ Memories table grows after conversations
- ✅ Redis shows conversation history
- ✅ No errors in logs (warnings OK)
- ✅ Response time <3 seconds for simple queries

---

## 🔐 Security Checklist

Before production deployment:

- [ ] Change default PostgreSQL password
- [ ] Use strong `TELEGRAM_WEBHOOK_SECRET`
- [ ] Enable HTTPS for webhook endpoint
- [ ] Restrict database access to internal network
- [ ] Rotate Groq API key regularly
- [ ] Enable Redis password authentication
- [ ] Set up log rotation
- [ ] Configure firewall rules

---

## 📈 Next Steps

Once basic conversation works:

1. **Add more integrations** (see ARIA_V3_IMPLEMENTATION_STATUS.md)
2. **Tune memory extraction** - adjust confidence thresholds
3. **Customize system prompts** - edit `personal_context.py`
4. **Add quick replies** - implement `quick_reply_service.py`
5. **Enable draft mode** - set `UserProfile.draft_mode = True`

---

## 🆘 Getting Help

If you're stuck:

1. Check logs: `docker compose logs api --tail=200`
2. Review status doc: `ARIA_V3_IMPLEMENTATION_STATUS.md`
3. Test individual components:
   ```bash
   # Test LLM client
   docker compose exec api python -c "
   from api.llm.client import groq_client
   import asyncio
   async def test():
       result = await groq_client.chat('Say hello')
       print(result)
   asyncio.run(test())
   "
   
   # Test conversation service
   docker compose exec api python -c "
   from api.services.conversation_service import append_turn, get_history
   from api.core.queue import get_redis
   import asyncio
   async def test():
       redis = await get_redis()
       await append_turn(redis, 'user', 'test message')
       history = await get_history(redis)
       print(f'History: {len(history)} turns')
   asyncio.run(test())
   "
   ```

---

**Last Updated**: 2026-05-17  
**Version**: 3.0  
**Status**: Ready for deployment
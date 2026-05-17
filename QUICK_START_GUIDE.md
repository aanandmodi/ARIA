# ARIA Refactored System - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Docker (optional)

### Installation

1. **Install Dependencies**
```bash
cd api
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_USER_ID=your_telegram_user_id
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/aria

# Redis
REDIS_URL=redis://localhost:6379

# Groq LLM
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# Services
GITHUB_TOKEN=your_github_token
WHATSAPP_API_URL=http://localhost:3000
```

3. **Run Database Migrations**
```bash
cd api
alembic upgrade head
```

4. **Start Services**

**Option A: Docker Compose (Recommended)**
```bash
docker-compose up -d
```

**Option B: Manual**
```bash
# Terminal 1: Start FastAPI
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start ARQ Worker
arq api.workers.settings.WorkerSettings

# Terminal 3: Start Baileys (WhatsApp)
cd baileys
npm install
node index.js
```

---

## 🧪 Testing the Refactored System

### 1. Test Webhook Response Time

```bash
# Should return 200 OK in <50ms
time curl -X POST http://localhost:8000/telegram \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: your_secret" \
  -d '{
    "update_id": 123,
    "message": {
      "message_id": 1,
      "from": {"id": YOUR_USER_ID, "first_name": "Test"},
      "chat": {"id": YOUR_USER_ID, "type": "private"},
      "date": 1234567890,
      "text": "test message"
    }
  }'
```

**Expected**: Response in <50ms with status 200

### 2. Test Progressive UI Feedback

Send a message to your bot:
```
What's the weather like?
```

**Expected behavior:**
1. Immediate response: `🔍 Processing...`
2. Update: `🧠 Understanding your request...`
3. Update: `🌤 Fetching weather...`
4. Final: Weather forecast displayed

### 3. Test Intent Parsing Speed

```bash
# Check worker logs
docker logs -f aria-worker

# Look for:
# intent_unified_parsed: intent=weather confidence=0.95 latency<500ms
```

### 4. Test Redis Caching

```bash
# First request (cache miss)
curl http://localhost:8000/internal/weather

# Second request (cache hit - should be <10ms)
curl http://localhost:8000/internal/weather

# Check Redis
redis-cli
> KEYS weather:*
> TTL weather:Asia/Kolkata
```

---

## 📱 Testing Commands

### Basic Commands
```
/start          - Welcome message
/briefing       - Morning briefing
/markets        - Stock/crypto prices
/status         - System health check
/websearch      - Web search
```

### Natural Language Examples

**Weather:**
```
What's the weather?
Will it rain today?
```

**Reminders:**
```
Remind me to call John at 3pm
Set a reminder for tomorrow 9am
```

**Expenses:**
```
Spent 500 on dinner
I paid $50 for groceries
```

**GitHub:**
```
Check my GitHub PRs
Show me open issues
Merge PR #123 in myrepo
```

**Search:**
```
Search emails about project
Find messages from John
```

**Memory:**
```
Remember that John prefers email
I live in New York
My favorite color is blue
```

---

## 🔍 Monitoring & Debugging

### Check System Status
```bash
# Via Telegram
/status

# Via API
curl http://localhost:8000/internal/health
```

### Monitor Worker Queue
```bash
# Check ARQ jobs
redis-cli
> KEYS arq:*
> LLEN arq:queue

# Monitor worker logs
docker logs -f aria-worker
```

### Check Cache Performance
```bash
redis-cli
> INFO stats
> KEYS *
> GET weather:Asia/Kolkata
```

### Database Connections
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'aria';

-- Check slow queries
SELECT query, calls, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

---

## 🐛 Troubleshooting

### Issue: Webhook Timeouts
**Solution**: Check if ARQ worker is running
```bash
docker ps | grep worker
docker logs aria-worker
```

### Issue: Slow Intent Parsing
**Solution**: Verify Groq API key and rate limits
```bash
# Check logs for rate limit errors
grep "groq_rate_limited" logs/aria.log
```

### Issue: Cache Not Working
**Solution**: Verify Redis connection
```bash
redis-cli ping
# Should return: PONG
```

### Issue: Database Connection Errors
**Solution**: Check connection pool
```bash
# In Python shell
from api.db.session import engine
print(engine.pool.status())
```

---

## 📊 Performance Benchmarks

### Expected Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Webhook Response | 2-5s | <50ms | 99% |
| Intent Parsing | 2-3s | <500ms | 83% |
| Weather API (cached) | 800ms | <10ms | 99% |
| Timeout Rate | 15-20% | 0% | 100% |
| User Latency | 5-8s | <1s | 87% |

### Load Testing

```bash
# Install Apache Bench
apt-get install apache2-utils

# Test webhook throughput
ab -n 1000 -c 10 -p test_payload.json \
   -T application/json \
   -H "X-Telegram-Bot-Api-Secret-Token: your_secret" \
   http://localhost:8000/telegram

# Expected: >200 requests/second
```

---

## 🔐 Security Checklist

- [ ] Webhook secret token configured
- [ ] User ID authorization enabled
- [ ] API keys in environment variables (not code)
- [ ] Redis password set (production)
- [ ] Database SSL enabled (production)
- [ ] Rate limiting configured
- [ ] HTTPS enabled (production)

---

## 📈 Next Steps

1. **Test all commands** listed above
2. **Monitor performance** for 24 hours
3. **Check error logs** for any issues
4. **Verify cache hit rates** (should be >80%)
5. **Test under load** (100+ messages/minute)

---

## 🆘 Getting Help

### Logs Location
```bash
# Application logs
tail -f logs/aria.log

# Worker logs
docker logs -f aria-worker

# Nginx logs (if using)
tail -f /var/log/nginx/access.log
```

### Health Checks
```bash
# FastAPI
curl http://localhost:8000/health

# Redis
redis-cli ping

# PostgreSQL
psql -U aria -d aria -c "SELECT 1"

# ARQ Worker
redis-cli LLEN arq:queue
```

---

## 📝 Configuration Tips

### Optimize for Your Use Case

**High Message Volume:**
```python
# api/workers/settings.py
max_jobs = 20  # Increase worker concurrency
job_timeout = 120  # Increase timeout
```

**Low Latency Priority:**
```python
# api/core/cache.py
DEFAULT_TTLS = {
    "weather": 900,   # Reduce to 15 min
    "crypto": 60,     # Reduce to 1 min
}
```

**Memory Constrained:**
```python
# api/db/session.py
pool_size=5,      # Reduce pool size
max_overflow=10,  # Reduce overflow
```

---

**Happy Testing! 🎉**

For issues or questions, check the logs first, then review `REFACTORING_SUMMARY.md` for architecture details.
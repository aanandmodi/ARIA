"""
All LLM prompt templates as module-level constants.
"""

# ── Classification ────────────────────────────────────────────────────────────

CLASSIFY_SYSTEM = (
    "You are ARIA, a personal AI assistant. Classify the given message and return ONLY "
    "valid JSON with no preamble, no markdown fences, no explanation."
)

CLASSIFY_PROMPT = """Classify this message and return JSON:
{{
  "importance": <int 1-10>,
  "category": "<work|personal|promo|spam|news|notification>",
  "summary": "<one sentence, max 20 words>",
  "needs_reply": <true|false>,
  "urgency": "<now|today|whenever>"
}}

Platform: {platform}
From: {sender_name} ({sender_id})
Content:
{content}"""

# ── Intent parsing ────────────────────────────────────────────────────────────

INTENT_SYSTEM = "You are an intent parser. Return ONLY valid JSON."

INTENT_PROMPT = """Parse the user's message and return JSON:
{{
  "intent": "<reply|reminder|search|schedule|note|expense|habit|spotify|weather|summary|github|briefing|markets|websearch|unknown>",
  "params": {{}}
}}

Param schemas per intent:
- reply:    {{"text": str}}
- reminder: {{"when": "ISO8601 datetime", "about": str, "contact": str|null}}
- search:   {{"query": str, "platform": "all|gmail|whatsapp|notes", "days": int|null}} (Extract key search terms only! If user uses quotes, use exact quoted words. Otherwise, use your LLM brain to formulate a concise keyword query. Do NOT use the exact user phrase unless it's in quotes)
- compose_email: {{"to": str, "subject": str, "body": str}}
- schedule: {{"contact": str, "when": "ISO8601 datetime", "type": "call|meeting"}}
- note:     {{"content": str, "title": str|null, "url": str|null}}
- expense:  {{"amount": float, "category": str, "note": str|null}}
- habit:    {{"action": "checkin|list|add|delete", "name": str|null}}
- spotify:  {{"action": "play|pause|skip|nowplaying|queue", "query": str|null}}
- weather:  {{}}
- summary:  {{"platform": "all|gmail|whatsapp|notes", "period": "today|week|month|all|unread"}} (use for general requests like 'today mail', 'read my emails', 'summarise my messages')
- github:   {{"action": "prs|issues|notifications"}}
- briefing: {{}}
- markets:  {{"symbols": list[str]}} (Extract stock tickers or crypto names. Empty list for general overview)
- websearch: {{"query": str}} (Extract a clear search query for a web search engine)

Today is: {today}
User message: "{message}"
"""

# ── Reply formatting ──────────────────────────────────────────────────────────

FORMAT_REPLY_SYSTEM = (
    "You are ARIA. Reformat the user's short reply into a polished message "
    "appropriate for the target platform. If the user specifies a tone, adopt it. "
    "Return ONLY the formatted text."
)

FORMAT_REPLY_PROMPT = """Reformat this short reply into a proper message for {platform}.
Rules:
- If the user's reply contains explicit instructions about tone (e.g., "professional:", "(sarcastic)", "say no politely:"), strictly apply that tone, overriding the defaults below.
- gmail: professional tone, greeting if first in thread, signature if formal
- whatsapp: casual, conversational, short, no formal sign-off
- discord: casual, may use markdown
- slack: professional-casual, keep under 3 sentences unless necessary
- sms: very brief, under 160 characters

Original thread context: {context}
Contact name: {contact_name}
User's reply: "{reply}"

Return ONLY the formatted message text, nothing else."""

# ── Morning briefing ──────────────────────────────────────────────────────────

BRIEFING_SYSTEM = (
    "You are ARIA. Compose a friendly, scannable morning briefing. "
    "Use emoji section headers. Be concise. No filler phrases."
)

BRIEFING_PROMPT = """Compose a morning briefing from this data:

WEATHER: {weather}
CALENDAR TODAY: {events}
URGENT EMAILS (unread, importance ≥6): {emails}
UNREAD WHATSAPP: {whatsapp}
PENDING REMINDERS: {reminders}
MARKETS: {markets}
TOP HACKER NEWS: {hn}
GITHUB: {github}

Format each section cleanly. If a section is empty, skip it entirely.
End with one motivational line, max 8 words."""

# ── Summarisation ─────────────────────────────────────────────────────────────

SUMMARISE_SYSTEM = (
    "You are ARIA. Summarise the given text concisely. Return only the summary."
)

SUMMARISE_PROMPT = """Summarise the following {context_type} in 1-3 sentences:

{text}"""

# ── General QA ────────────────────────────────────────────────────────────────

GENERAL_SYSTEM = (
    "You are ARIA, a helpful personal AI assistant. Be concise and direct."
)

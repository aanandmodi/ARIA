"""
Search handler — universal cross-platform search.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.services import telegram_service
from api.services.search_service import universal_search
from api.llm.client import chat
from api.core.logging import log

SEARCH_SYSTEM_PROMPT = """You are ARIA, a helpful personal AI assistant. 
The user searched for something across their digital life. I am providing you with the search results from their database.
Your job is to read these results, understand them deeply using your LLM brain, and provide a conversational, helpful, and concise answer that directly addresses what the user is looking for.
If the search results contain the answer, summarize it beautifully.
If the results are empty or don't seem to contain the answer, politely tell the user.
Cite the platform/sender if relevant (e.g. "In an email from John, he mentioned...").
Do not output raw JSON or internal IDs. Keep it natural.
"""

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    """Handle search intent."""
    query = params.get("query", "")
    platform = params.get("platform", "all")
    days = params.get("days")
    user_message = update.message.text if update.message else query

    if not query and platform == "all" and not days:
        await telegram_service.send_message("🔍 What would you like to search for?")
        return

    # Acknowledge search
    search_desc = f"'{query}'" if query else f"messages"
    if platform != "all":
        search_desc += f" on {platform}"
    if days:
        search_desc += f" from the past {days} days"
    
    await telegram_service.send_message(f"🔍 Let me look through your {search_desc}...")

    results = await universal_search(db, query, platform=platform, days=days)
    
    # --- Fetch old emails directly from Gmail API ---
    if platform in ("all", "gmail") and query:
        from api.services import gmail_service
        try:
            gmail_mails = await gmail_service.search_emails(query, max_results=5)
            for m in gmail_mails:
                # Avoid duplicates if it's already in DB results
                if not any(r.get("external_id") == m.message_id for r in results):
                    results.append({
                        "platform": "gmail",
                        "sender_name": m.sender,
                        "content": m.snippet,
                        "summary": m.subject,
                        "date": m.date,
                        "external_id": m.message_id
                    })
        except Exception as e:
            log.error("gmail_api_search_failed", error=str(e))
            
    # --- Fetch old whatsapp messages from Baileys Store ---
    if platform in ("all", "whatsapp") and query:
        from api.services import whatsapp_service
        try:
            from datetime import datetime
            wa_msgs = await whatsapp_service.search_history(query, limit=5)
            for m in wa_msgs:
                if not any(r.get("external_id") == m.get("messageId") for r in results):
                    ts = m.get("timestamp")
                    date_str = datetime.fromtimestamp(ts).isoformat() if ts else datetime.utcnow().isoformat()
                    results.append({
                        "platform": "whatsapp",
                        "sender_name": m.get("pushName") or "WhatsApp User",
                        "content": m.get("text"),
                        "summary": None,
                        "date": date_str,
                        "external_id": m.get("messageId")
                    })
        except Exception as e:
            log.error("whatsapp_api_search_failed", error=str(e))
    # ------------------------------------------------
    
    if not results:
        prompt = f"User asked: '{user_message}'\n\nSearch query used: '{query}'\n\nResults: No results found in the database."
    else:
        context = []
        for r in results[:10]:
            content = r['content'] or r['summary']
            context.append(f"[{r['platform'].upper()}] From: {r['sender_name']} | Date: {r['date'][:10]}\nContent: {content}\n")
        
        results_text = "\n".join(context)
        prompt = f"User asked: '{user_message}'\n\nSearch query used: '{query}'\n\nDatabase Search Results:\n{results_text}\n\nRespond conversationally based on these results."

    try:
        response = await chat(prompt, system=SEARCH_SYSTEM_PROMPT, max_tokens=1024)
        await telegram_service.send_message(response)
    except Exception as exc:
        log.error("search_llm_failed", error=str(exc))
        # Fallback
        if not results:
            await telegram_service.send_message(f"🔍 No results found for '<i>{query}</i>'")
            return
        lines = [f"🔍 <b>Search results for '{query}'</b>\n"]
        for r in results[:10]:
            emoji = telegram_service.PLATFORM_EMOJI.get(r["platform"], "📨")
            lines.append(f"{emoji} <b>{r['sender_name']}</b> — {r['summary'] or r['content'][:50]}...\n   <i>{r['date'][:10]}</i>")
        await telegram_service.send_message("\n".join(lines))

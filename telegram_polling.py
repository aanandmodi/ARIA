"""
Telegram Polling Service for ARIA
This runs the bot in polling mode (no webhook needed) for local development.

Usage:
    python telegram_polling.py
"""
import asyncio
import os
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from telegram import Update
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters
from api.core.config import settings
from api.core.queue import get_arq_pool
from arq import create_pool
from arq.connections import RedisSettings


async def handle_message(update: Update, context):
    """Handle incoming messages by queuing them to ARQ worker."""
    if not update.message:
        return
    
    print(f"📨 Received message from {update.effective_user.id}: {update.message.text[:50] if update.message.text else '[media]'}")
    
    # Queue the update to ARQ worker (connect to localhost Redis)
    pool = await create_pool(RedisSettings(host='localhost', port=6379))
    job = await pool.enqueue_job(
        "process_telegram_update",
        update.to_dict()
    )
    print(f"✅ Queued job: {job.job_id}")
    await pool.close()


async def handle_callback(update: Update, context):
    """Handle callback queries."""
    if not update.callback_query:
        return
    
    print(f"🔘 Received callback from {update.effective_user.id}: {update.callback_query.data}")
    
    # Queue the update to ARQ worker (connect to localhost Redis)
    pool = await create_pool(RedisSettings(host='localhost', port=6379))
    job = await pool.enqueue_job(
        "process_telegram_update",
        update.to_dict()
    )
    print(f"✅ Queued job: {job.job_id}")
    await pool.close()


async def main():
    """Start the bot in polling mode."""
    print("=" * 60)
    print("🤖 ARIA Telegram Bot - Polling Mode")
    print("=" * 60)
    print()
    
    if not settings.telegram_bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        sys.exit(1)
    
    print(f"✅ Bot Token: {settings.telegram_bot_token[:20]}...")
    print(f"✅ User ID: {settings.telegram_user_id}")
    print(f"✅ Redis: {settings.redis_host}:{settings.redis_port}")
    print()
    
    # Delete any existing webhook
    print("🔄 Removing any existing webhook...")
    import httpx
    resp = httpx.post(
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/deleteWebhook",
        json={"drop_pending_updates": False},
        timeout=10
    )
    result = resp.json()
    if result.get("ok"):
        print("✅ Webhook removed")
    else:
        print(f"⚠️  Could not remove webhook: {result.get('description')}")
    
    print()
    print("🚀 Starting bot in polling mode...")
    print("   Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    # Create application
    app = Application.builder().token(settings.telegram_bot_token).build()
    
    # Add handlers
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # Start polling
    try:
        await app.initialize()
        await app.start()
        print("✅ Bot is now polling for updates...")
        print("   Send a message to your bot to test!")
        print()
        
        await app.updater.start_polling(
            allowed_updates=["message", "callback_query", "edited_message"],
            drop_pending_updates=False
        )
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping bot...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        print("✅ Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(0)

# Made with Bob

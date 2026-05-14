"""
Discord bot — listens for messages and pushes to inbound queue.
"""
from __future__ import annotations
import discord
from api.core.config import settings
from api.core.logging import log
from api.core.queue import enqueue

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    log.info("discord_bot_ready", user=str(client.user))


@client.event
async def on_message(message: discord.Message):
    # Skip bot messages
    if message.author.bot:
        return
    # Skip own messages
    if settings.discord_user_id and message.author.id == settings.discord_user_id:
        return

    try:
        attachments = [{"url": a.url, "filename": a.filename} for a in message.attachments]
        payload = {
            "platform": "discord",
            "message_id": str(message.id),
            "thread_id": str(message.channel.id),
            "sender_id": str(message.author.id),
            "sender_name": f"{message.author.display_name}",
            "content": message.content,
            "raw": {
                "id": str(message.id),
                "channel_id": str(message.channel.id),
                "channel_name": getattr(message.channel, "name", "DM"),
                "guild_name": message.guild.name if message.guild else "",
                "author": {
                    "id": str(message.author.id),
                    "name": message.author.name,
                    "display_name": message.author.display_name,
                },
                "attachments": attachments,
            },
            "received_at": message.created_at.isoformat(),
            "has_attachment": bool(attachments),
            "attachment_urls": [a["url"] for a in attachments],
        }
        await enqueue("process_inbound_message", payload)
    except Exception as exc:
        log.error("discord_on_message_error", error=str(exc))


async def start_bot():
    """Start the Discord bot. Called as an asyncio task."""
    if not settings.discord_bot_token:
        log.info("discord_bot_not_configured")
        return
    try:
        await client.start(settings.discord_bot_token)
    except Exception as exc:
        log.error("discord_bot_start_failed", error=str(exc))

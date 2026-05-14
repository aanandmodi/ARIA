"""
ARIA interactive setup wizard.
Generates a .env file with all required and optional configuration.

Usage:
    python aria_setup.py
"""
from __future__ import annotations
import os
import secrets
import sys

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def _ask(prompt: str, default: str = "", required: bool = False, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    suffix += " (REQUIRED)" if required else ""
    val = input(f"  {prompt}{suffix}: ").strip()
    if not val:
        val = default
    if required and not val:
        print(f"    ❌ This field is required!")
        return _ask(prompt, default, required, secret)
    return val


def main():
    print()
    print("=" * 60)
    print("  🚀 ARIA — Interactive Setup Wizard")
    print("=" * 60)
    print()
    print("This will generate your .env file.")
    print("Press Enter to accept defaults shown in [brackets].")
    print()

    if os.path.exists(ENV_PATH):
        overwrite = input(f"  ⚠️  .env already exists. Overwrite? (y/n) [n]: ").strip().lower()
        if overwrite != "y":
            print("  Aborted.")
            sys.exit(0)

    env = {}

    # ── Required ──
    print("\n─── REQUIRED (minimum to run) ───\n")
    env["TELEGRAM_BOT_TOKEN"] = _ask("Telegram Bot Token (from @BotFather)", required=True)
    env["TELEGRAM_USER_ID"] = _ask("Your Telegram User ID (send /myid to @userinfobot)", required=True)
    env["GROQ_API_KEY"] = _ask("Groq API Key (console.groq.com)", required=True)

    # ── Auto-generated ──
    env["TELEGRAM_WEBHOOK_SECRET"] = secrets.token_hex(16)

    # ── Groq model ──
    print("\n─── LLM Settings ───\n")
    env["GROQ_MODEL"] = _ask("Groq model", default="llama-3.3-70b-versatile")
    env["GROQ_WHISPER_MODEL"] = _ask("Groq Whisper model", default="whisper-large-v3")

    # ── Gmail ──
    print("\n─── Gmail / Google (optional, press Enter to skip) ───\n")
    env["GMAIL_CLIENT_ID"] = _ask("Google OAuth Client ID")
    env["GMAIL_CLIENT_SECRET"] = _ask("Google OAuth Client Secret")
    env["GMAIL_REFRESH_TOKEN"] = _ask("Gmail Refresh Token (run aria_gmail_auth.py later)")
    env["GMAIL_USER_EMAIL"] = _ask("Your Gmail address")
    env["GMAIL_PUBSUB_TOPIC"] = _ask("Gmail Pub/Sub topic", default="projects/YOUR_PROJECT/topics/gmail-push")

    # ── WhatsApp ──
    print("\n─── WhatsApp (auto-configured via Docker) ───\n")
    env["BAILEYS_HOST"] = _ask("Baileys host", default="baileys")
    env["BAILEYS_PORT"] = _ask("Baileys port", default="3001")

    # ── Discord ──
    print("\n─── Discord (optional) ───\n")
    env["DISCORD_BOT_TOKEN"] = _ask("Discord Bot Token")
    env["DISCORD_USER_ID"] = _ask("Your Discord User ID")

    # ── Slack ──
    print("\n─── Slack (optional) ───\n")
    env["SLACK_BOT_TOKEN"] = _ask("Slack Bot Token")
    env["SLACK_WEBHOOK_URL"] = _ask("Slack Webhook URL")
    env["SLACK_SIGNING_SECRET"] = _ask("Slack Signing Secret")

    # ── Notion ──
    print("\n─── Notion (optional) ───\n")
    env["NOTION_TOKEN"] = _ask("Notion Integration Token")
    env["NOTION_NOTES_DB_ID"] = _ask("Notion Notes Database ID")
    env["NOTION_TASKS_DB_ID"] = _ask("Notion Tasks Database ID")

    # ── GitHub ──
    print("\n─── GitHub (optional) ───\n")
    env["GITHUB_TOKEN"] = _ask("GitHub Personal Access Token")
    env["GITHUB_USERNAME"] = _ask("GitHub username")
    env["GITHUB_REPOS"] = _ask("Watched repos (comma-separated, e.g. user/repo1,user/repo2)")

    # ── Spotify ──
    print("\n─── Spotify (optional) ───\n")
    env["SPOTIFY_CLIENT_ID"] = _ask("Spotify Client ID")
    env["SPOTIFY_CLIENT_SECRET"] = _ask("Spotify Client Secret")
    env["SPOTIFY_REDIRECT_URI"] = _ask("Spotify Redirect URI", default="http://localhost:8888/callback")

    # ── SMS ──
    print("\n─── SMS Gateway (optional) ───\n")
    env["SMS_GATEWAY_URL"] = _ask("SMS Gateway URL")
    env["SMS_GATEWAY_TOKEN"] = _ask("SMS Gateway Token")

    # ── Monitoring ──
    print("\n─── Monitoring & Watchlists (optional) ───\n")
    env["STOCK_WATCHLIST"] = _ask("Stock tickers (comma-sep, e.g. AAPL,TSLA,MSFT)")
    env["CRYPTO_WATCHLIST"] = _ask("Crypto coins (comma-sep, e.g. bitcoin,ethereum)")
    env["RSS_FEEDS"] = _ask("RSS feed URLs (comma-sep)")
    env["KEYWORD_ALERTS"] = _ask("Keyword alerts (comma-sep)")

    # ── Database (defaults) ──
    print("\n─── Database (auto-configured for Docker) ───\n")
    db_pass = secrets.token_urlsafe(16)
    minio_pass = secrets.token_urlsafe(16)
    env["POSTGRES_DB"] = _ask("Postgres DB name", default="aria")
    env["POSTGRES_USER"] = _ask("Postgres user", default="aria")
    env["POSTGRES_PASSWORD"] = _ask("Postgres password", default=db_pass)
    env["POSTGRES_HOST"] = _ask("Postgres host", default="postgres")
    env["POSTGRES_PORT"] = _ask("Postgres port", default="5432")
    env["REDIS_HOST"] = _ask("Redis host", default="redis")
    env["REDIS_PORT"] = _ask("Redis port", default="6379")
    env["MINIO_ROOT_USER"] = _ask("MinIO user", default="aria")
    env["MINIO_ROOT_PASSWORD"] = _ask("MinIO password", default=minio_pass)
    env["MINIO_HOST"] = _ask("MinIO host", default="minio")
    env["MINIO_PORT"] = _ask("MinIO port", default="9000")
    env["MINIO_BUCKET"] = _ask("MinIO bucket", default="aria-storage")

    # ── Preferences ──
    print("\n─── Preferences ───\n")
    env["BRIEFING_TIME"] = _ask("Morning briefing time (HH:MM)", default="08:00")
    env["TIMEZONE"] = _ask("Timezone", default="Asia/Kolkata")
    env["IMPORTANCE_THRESHOLD"] = _ask("Importance threshold (1-10, lower = more notifications)", default="6")
    env["DRAFT_MODE"] = _ask("Draft mode (true/false — review replies before sending)", default="false")
    env["FOLLOW_UP_DAYS"] = _ask("Follow-up reminder days", default="3")
    env["LANGUAGE"] = _ask("Language", default="en")

    # ── Write .env ──
    print("\n" + "=" * 60)
    lines = []
    for key, value in env.items():
        lines.append(f"{key}={value}")

    with open(ENV_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n  ✅ .env written to: {ENV_PATH}")
    print(f"\n  Next steps:")
    print(f"    1. docker compose up -d")
    print(f"    2. python aria_register_webhook.py")
    print(f"    3. Send /start to your Telegram bot!")
    if not env.get("GMAIL_REFRESH_TOKEN"):
        print(f"    4. (Optional) python aria_gmail_auth.py — for Gmail integration")
    print()


if __name__ == "__main__":
    main()

"""
Register Telegram webhook for ARIA.

Usage:
    python aria_register_webhook.py
"""
from __future__ import annotations
import os
import sys

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

    if not token:
        token = input("Enter your Telegram Bot Token: ").strip()
    if not token:
        print("❌ Bot token is required.")
        sys.exit(1)

    domain = input("Enter your ARIA domain (e.g. aria.yourdomain.com): ").strip()
    if not domain:
        print("❌ Domain is required.")
        sys.exit(1)

    webhook_url = f"https://{domain}/webhook/telegram"
    print(f"\nRegistering webhook: {webhook_url}")

    payload = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": True,
    }
    if secret:
        payload["secret_token"] = secret

    resp = httpx.post(
        f"https://api.telegram.org/bot{token}/setWebhook",
        json=payload,
        timeout=10,
    )
    result = resp.json()
    print(f"\nResponse: {result}")

    if result.get("ok"):
        print("✅ Webhook registered successfully!")
    else:
        print(f"❌ Failed: {result.get('description', 'Unknown error')}")


if __name__ == "__main__":
    main()

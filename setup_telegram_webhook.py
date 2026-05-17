"""
Setup Telegram Webhook for ARIA
This script helps you register the Telegram webhook with your public URL.

Usage:
    python setup_telegram_webhook.py
"""
import os
import sys
import subprocess
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Using environment variables only.")


def check_ngrok():
    """Check if ngrok is running and get the public URL."""
    try:
        resp = httpx.get("http://localhost:4040/api/tunnels", timeout=5)
        data = resp.json()
        tunnels = data.get("tunnels", [])
        
        for tunnel in tunnels:
            if tunnel.get("proto") == "https":
                return tunnel.get("public_url")
        
        return None
    except Exception:
        return None


def get_webhook_info(token):
    """Get current webhook information."""
    try:
        resp = httpx.get(
            f"https://api.telegram.org/bot{token}/getWebhookInfo",
            timeout=10
        )
        return resp.json()
    except Exception as e:
        print(f"❌ Error getting webhook info: {e}")
        return None


def delete_webhook(token):
    """Delete existing webhook."""
    try:
        resp = httpx.post(
            f"https://api.telegram.org/bot{token}/deleteWebhook",
            json={"drop_pending_updates": True},
            timeout=10
        )
        result = resp.json()
        if result.get("ok"):
            print("✅ Existing webhook deleted")
        return result.get("ok", False)
    except Exception as e:
        print(f"❌ Error deleting webhook: {e}")
        return False


def set_webhook(token, url, secret=None):
    """Set new webhook."""
    payload = {
        "url": url,
        "allowed_updates": ["message", "callback_query", "edited_message"],
        "drop_pending_updates": True,
        "max_connections": 100,
    }
    
    if secret:
        payload["secret_token"] = secret
    
    try:
        resp = httpx.post(
            f"https://api.telegram.org/bot{token}/setWebhook",
            json=payload,
            timeout=10
        )
        return resp.json()
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        return {"ok": False, "description": str(e)}


def main():
    print("=" * 60)
    print("🤖 ARIA Telegram Webhook Setup")
    print("=" * 60)
    print()
    
    # Get bot token
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        token = input("Enter your Telegram Bot Token: ").strip()
    
    if not token:
        print("❌ Bot token is required!")
        sys.exit(1)
    
    # Get webhook secret
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    
    # Check current webhook status
    print("📊 Checking current webhook status...")
    webhook_info = get_webhook_info(token)
    
    if webhook_info and webhook_info.get("ok"):
        result = webhook_info.get("result", {})
        current_url = result.get("url", "")
        
        if current_url:
            print(f"⚠️  Webhook already set to: {current_url}")
            print(f"   Pending updates: {result.get('pending_update_count', 0)}")
            
            choice = input("\nDelete existing webhook? (y/n): ").strip().lower()
            if choice == 'y':
                delete_webhook(token)
            else:
                print("❌ Cancelled. Existing webhook remains.")
                sys.exit(0)
    
    print()
    print("🌐 Choose webhook setup method:")
    print("   1. Use ngrok (automatic detection)")
    print("   2. Enter custom domain/URL")
    print("   3. Use localhost (for testing only - won't work with Telegram)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    webhook_url = None
    
    if choice == "1":
        print("\n🔍 Checking for ngrok tunnel...")
        ngrok_url = check_ngrok()
        
        if ngrok_url:
            webhook_url = f"{ngrok_url}/webhook/telegram"
            print(f"✅ Found ngrok tunnel: {ngrok_url}")
        else:
            print("❌ No ngrok tunnel found!")
            print("\n💡 To start ngrok:")
            print("   ngrok http 8000")
            print("\nThen run this script again.")
            sys.exit(1)
    
    elif choice == "2":
        domain = input("\nEnter your public domain (e.g., aria.yourdomain.com): ").strip()
        if not domain:
            print("❌ Domain is required!")
            sys.exit(1)
        
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        
        webhook_url = f"{domain}/webhook/telegram"
    
    elif choice == "3":
        print("\n⚠️  WARNING: Localhost webhooks won't work with Telegram!")
        print("   This is only for testing the registration process.")
        webhook_url = "http://localhost:8000/webhook/telegram"
    
    else:
        print("❌ Invalid choice!")
        sys.exit(1)
    
    # Register webhook
    print(f"\n📝 Registering webhook: {webhook_url}")
    print("   Please wait...")
    
    result = set_webhook(token, webhook_url, secret)
    
    print()
    print("=" * 60)
    
    if result.get("ok"):
        print("✅ Webhook registered successfully!")
        print()
        print("📊 Webhook Details:")
        print(f"   URL: {webhook_url}")
        print(f"   Secret: {'Set' if secret else 'Not set'}")
        print()
        print("🎉 Your bot is now ready to receive messages!")
        print()
        print("📝 Next steps:")
        print("   1. Send a message to your bot on Telegram")
        print("   2. Check logs: docker-compose logs -f api")
        print("   3. Check worker logs: docker-compose logs -f worker")
    else:
        print("❌ Failed to register webhook!")
        print(f"   Error: {result.get('description', 'Unknown error')}")
        print()
        print("💡 Common issues:")
        print("   - Make sure your URL is publicly accessible")
        print("   - URL must use HTTPS (except localhost for testing)")
        print("   - Check if port 8000 is accessible from the internet")
    
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

# Made with Bob

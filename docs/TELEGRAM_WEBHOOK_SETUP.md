# Telegram Webhook Setup Guide

## Problem
Your Telegram bot is not receiving messages because the webhook is not properly configured. Telegram needs a **public HTTPS URL** to send updates to your bot.

## Solution Options

### Option 1: Using ngrok (Recommended for Development)

1. **Install ngrok**:
   - Download from: https://ngrok.com/download
   - Or use: `choco install ngrok` (Windows with Chocolatey)

2. **Start ngrok**:
   ```bash
   ngrok http 8000
   ```

3. **Run the webhook setup script**:
   ```bash
   python setup_telegram_webhook.py
   ```
   - Choose option `1` (Use ngrok)
   - The script will automatically detect your ngrok URL

4. **Keep ngrok running**:
   - Your bot will only work while ngrok is running
   - Each time you restart ngrok, you'll get a new URL and need to re-register the webhook

### Option 2: Using a Custom Domain (Production)

If you have a server with a public domain:

1. **Configure your domain**:
   - Point your domain (e.g., `aria.yourdomain.com`) to your server's IP
   - Ensure port 8000 is accessible from the internet
   - Set up SSL/TLS certificate (required by Telegram)

2. **Run the webhook setup script**:
   ```bash
   python setup_telegram_webhook.py
   ```
   - Choose option `2` (Enter custom domain)
   - Enter your domain: `aria.yourdomain.com`

### Option 3: Quick Test with Manual Registration

If you just want to test quickly:

```python
import httpx

TOKEN = "your_bot_token_here"
WEBHOOK_URL = "https://your-ngrok-url.ngrok.io/webhook/telegram"

response = httpx.post(
    f"https://api.telegram.org/bot{TOKEN}/setWebhook",
    json={
        "url": WEBHOOK_URL,
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": True
    }
)
print(response.json())
```

## Verifying Webhook Status

Check if your webhook is registered:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

Or use the Python script:
```python
import httpx
TOKEN = "your_bot_token"
resp = httpx.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo")
print(resp.json())
```

## Testing Your Bot

Once the webhook is set up:

1. **Send a message to your bot** on Telegram

2. **Check the logs**:
   ```bash
   # API logs (webhook receives the message)
   docker-compose logs -f api
   
   # Worker logs (processes the message)
   docker-compose logs -f worker
   ```

3. **You should see**:
   - API log: `telegram_webhook_received`
   - Worker log: `process_telegram_update` executing

## Troubleshooting

### Bot not responding to messages

1. **Check webhook status**:
   ```bash
   python setup_telegram_webhook.py
   ```
   Look for "Webhook already set to: ..."

2. **Check if webhook URL is accessible**:
   ```bash
   curl https://your-webhook-url/webhook/telegram
   ```
   Should return: `{"detail":"Method Not Allowed"}`

3. **Check Docker logs**:
   ```bash
   docker-compose logs --tail=50 api
   docker-compose logs --tail=50 worker
   ```

4. **Restart services**:
   ```bash
   docker-compose restart api worker
   ```

### Common Issues

**Issue**: "Webhook already set"
- **Solution**: Delete the existing webhook first (the script will prompt you)

**Issue**: "URL is not valid"
- **Solution**: Ensure your URL uses HTTPS (not HTTP)
- **Solution**: Make sure the URL is publicly accessible

**Issue**: "Connection refused"
- **Solution**: Check if your server/ngrok is running
- **Solution**: Verify port 8000 is accessible

**Issue**: Bot receives messages but doesn't respond
- **Solution**: Check worker logs for errors
- **Solution**: Verify GROQ_API_KEY is set in .env
- **Solution**: Check Redis connection

## Current Setup

Your bot token: `8689811105:AAGqKOjskEFN-5n1JtIIZ62LemMqhepC6js`
Your user ID: `5440418275`

## Next Steps

1. Choose your webhook method (ngrok recommended for testing)
2. Run `python setup_telegram_webhook.py`
3. Follow the prompts
4. Test by sending a message to your bot
5. Check logs to verify it's working

## Important Notes

- **ngrok free tier**: URL changes every time you restart ngrok
- **Production**: Use a permanent domain with SSL certificate
- **Security**: Keep your bot token secret
- **Rate limits**: Telegram has rate limits for API calls
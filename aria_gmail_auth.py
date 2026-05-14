"""
Gmail OAuth2 authorization helper script.
Run this once to obtain a refresh token for Gmail API access.

Usage:
    python aria_gmail_auth.py
"""
from __future__ import annotations
import json
import os
import sys

# Fix Windows terminal encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]


def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Install google-auth-oauthlib: pip install google-auth-oauthlib")
        sys.exit(1)

    print("\n=== ARIA Gmail OAuth2 Setup ===\n")

    client_id = os.getenv("GMAIL_CLIENT_ID", "")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET", "")

    if not client_id:
        client_id = input("Enter your Google OAuth2 Client ID: ").strip()
    if not client_secret:
        client_secret = input("Enter your Google OAuth2 Client Secret: ").strip()

    if not client_id or not client_secret:
        print("[ERROR] Client ID and Secret are required.")
        sys.exit(1)

    # Use "installed" app type for local server flow.
    # Even if created as "Web application" in GCP Console, InstalledAppFlow
    # handles the redirect to localhost automatically.
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    print("\nA browser window will open for authorization.")
    print("If it doesn't open, copy the URL below:\n")

    try:
        creds = flow.run_local_server(port=8080, open_browser=True)
    except Exception:
        # Fallback to console flow
        auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
        print(f"Open this URL in your browser:\n\n{auth_url}\n")
        code = input("Enter the authorization code: ").strip()
        flow.fetch_token(code=code)
        creds = flow.credentials

    refresh_token = creds.refresh_token
    if not refresh_token:
        print("[WARNING] No refresh token received. Try revoking access and re-running.")
        sys.exit(1)

    print(f"\n[SUCCESS] Your refresh token:\n")
    print(f"   GMAIL_REFRESH_TOKEN={refresh_token}\n")

    # Offer to write to .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        write = input("Write to .env? (y/n): ").strip().lower()
        if write == "y":
            with open(env_path, "r") as f:
                content = f.read()
            if "GMAIL_REFRESH_TOKEN=" in content:
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("GMAIL_REFRESH_TOKEN="):
                        lines[i] = f"GMAIL_REFRESH_TOKEN={refresh_token}"
                content = "\n".join(lines)
            else:
                content += f"\nGMAIL_REFRESH_TOKEN={refresh_token}\n"
            with open(env_path, "w") as f:
                f.write(content)
            print("[OK] Written to .env")
    else:
        print("   Add this to your .env file manually.")

    print("\nDone! Gmail integration is ready.")


if __name__ == "__main__":
    main()

"""
Gmail service — fetch, send, search, draft via Google API.
"""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
from email.mime.text import MIMEText
from functools import partial

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from api.core.config import settings
from api.core.logging import log

_gmail_service = None


@dataclass
class EmailMessage:
    message_id: str
    thread_id: str
    sender: str
    sender_name: str
    subject: str
    body: str
    snippet: str
    date: str


@dataclass
class EmailSummary:
    sender: str
    subject: str
    snippet: str
    date: str
    message_id: str


def _get_credentials() -> Credentials | None:
    """Build Google credentials from stored refresh token."""
    if not settings.gmail_refresh_token:
        return None
    try:
        creds = Credentials(
            token=None,
            refresh_token=settings.gmail_refresh_token,
            client_id=settings.gmail_client_id,
            client_secret=settings.gmail_client_secret,
            token_uri="https://oauth2.googleapis.com/token",
        )
        creds.refresh(GoogleRequest())
        return creds
    except Exception as exc:
        log.error("gmail_creds_failed", error=str(exc))
        return None


def _get_service():
    """Build or return cached Gmail API service."""
    global _gmail_service
    if _gmail_service is not None:
        return _gmail_service
    creds = _get_credentials()
    if creds is None:
        return None
    _gmail_service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    return _gmail_service


def _is_configured() -> bool:
    return bool(settings.gmail_refresh_token and settings.gmail_client_id)


async def setup_pubsub_watch() -> None:
    """Call gmail.users.watch() to start Pub/Sub push notifications."""
    if not _is_configured():
        log.info("gmail_not_configured_skipping_watch")
        return
    try:
        svc = _get_service()
        if svc is None:
            return
        loop = asyncio.get_event_loop()
        body = {
            "topicName": settings.gmail_pubsub_topic,
            "labelIds": ["INBOX"],
        }
        result = await loop.run_in_executor(
            None,
            partial(svc.users().watch(userId="me", body=body).execute),
        )
        log.info("gmail_watch_registered", result=result)
    except Exception as exc:
        log.error("gmail_watch_failed", error=str(exc))


async def fetch_full_message(message_id: str) -> EmailMessage | None:
    """Fetch full email body, decode base64 MIME parts, return plain text."""
    if not _is_configured():
        return None
    try:
        svc = _get_service()
        if svc is None:
            return None
        loop = asyncio.get_event_loop()
        msg = await loop.run_in_executor(
            None,
            partial(
                svc.users().messages().get(
                    userId="me", id=message_id, format="full"
                ).execute
            ),
        )

        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        subject = headers.get("subject", "(no subject)")
        sender_full = headers.get("from", "unknown")
        date_str = headers.get("date", "")

        # Parse sender name from "Name <email>" format
        sender_name = sender_full
        sender_email = sender_full
        if "<" in sender_full:
            parts = sender_full.split("<")
            sender_name = parts[0].strip().strip('"')
            sender_email = parts[1].rstrip(">").strip()

        # Extract body
        body = _extract_body(msg.get("payload", {}))
        snippet = msg.get("snippet", "")
        thread_id = msg.get("threadId", "")

        return EmailMessage(
            message_id=message_id,
            thread_id=thread_id,
            sender=sender_email,
            sender_name=sender_name,
            subject=subject,
            body=body,
            snippet=snippet,
            date=date_str,
        )
    except Exception as exc:
        log.error("gmail_fetch_failed", error=str(exc), msg_id=message_id)
        return None


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text or HTML body from Gmail payload."""
    mime_type = payload.get("mimeType", "")
    
    if mime_type == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        
    if mime_type == "text/html" and payload.get("body", {}).get("data"):
        html = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        import re
        text = re.sub(r'<[^>]+>', ' ', html)
        return text.strip()

    html_fallback = ""
    for part in payload.get("parts", []):
        res = _extract_body(part)
        if res:
            if part.get("mimeType") == "text/html":
                html_fallback = res
            else:
                return res

    if html_fallback:
        return html_fallback

    # Fallback to snippet
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    return ""


async def send_email(
    to: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
) -> str:
    """Send email. If thread_id given, reply to that thread. Returns message ID."""
    if not _is_configured():
        log.warning("gmail_not_configured_cannot_send")
        return ""
    try:
        svc = _get_service()
        if svc is None:
            return ""

        message = MIMEText(body)
        message["to"] = to
        message["from"] = settings.gmail_user_email
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_body: dict = {"raw": raw}
        if thread_id:
            send_body["threadId"] = thread_id

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                svc.users().messages().send(userId="me", body=send_body).execute
            ),
        )
        msg_id = result.get("id", "")
        log.info("gmail_sent", to=to, subject=subject, msg_id=msg_id)
        return msg_id
    except Exception as exc:
        log.error("gmail_send_failed", error=str(exc), to=to)
        return ""


async def search_emails(query: str, max_results: int = 10) -> list[EmailSummary]:
    """Gmail search query. Return list of summaries."""
    if not _is_configured():
        return []
    try:
        svc = _get_service()
        if svc is None:
            return []
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                svc.users().messages().list(
                    userId="me", q=query, maxResults=max_results
                ).execute
            ),
        )
        messages = result.get("messages", [])
        summaries = []
        for m in messages[:max_results]:
            full = await fetch_full_message(m["id"])
            if full:
                summaries.append(EmailSummary(
                    sender=full.sender,
                    subject=full.subject,
                    snippet=full.snippet,
                    date=full.date,
                    message_id=full.message_id,
                ))
        return summaries
    except Exception as exc:
        log.error("gmail_search_failed", error=str(exc), query=query)
        return []


async def get_latest_message_id() -> str | None:
    """Get the ID of the most recently received email."""
    if not _is_configured():
        return None
    try:
        svc = _get_service()
        if svc is None:
            return None
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                svc.users().messages().list(
                    userId="me", maxResults=1
                ).execute
            ),
        )
        messages = result.get("messages", [])
        if messages:
            return messages[0]["id"]
        return None
    except Exception as exc:
        log.error("gmail_get_latest_failed", error=str(exc))
        return None


async def create_draft(to: str, subject: str, body: str) -> str:
    """Create Gmail draft. Return draft ID."""
    if not _is_configured():
        return ""
    try:
        svc = _get_service()
        if svc is None:
            return ""

        message = MIMEText(body)
        message["to"] = to
        message["from"] = settings.gmail_user_email
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft_body = {"message": {"raw": raw}}

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                svc.users().drafts().create(userId="me", body=draft_body).execute
            ),
        )
        draft_id = result.get("id", "")
        log.info("gmail_draft_created", draft_id=draft_id, to=to)
        return draft_id
    except Exception as exc:
        log.error("gmail_draft_failed", error=str(exc))
        return ""


async def send_email(to: str, subject: str, body: str) -> bool:
    """Send a new email."""
    try:
        svc = _get_service()
        if svc is None:
            return False
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(
                svc.users().messages().send(
                    userId='me',
                    body={'raw': raw}
                ).execute
            )
        )
        
        log.info("gmail_sent", to=to, subject=subject)
        return True
    except Exception as exc:
        log.error("gmail_send_failed", error=str(exc), to=to)
        return False


async def send_reply(message_id: str, reply_text: str) -> bool:
    """Send a reply to an email thread."""
    try:
        svc = _get_service()
        if svc is None:
            return False
        
        # Get original message
        loop = asyncio.get_event_loop()
        original = await loop.run_in_executor(
            None,
            partial(
                svc.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute
            )
        )
        
        # Extract headers
        headers = {h['name']: h['value'] for h in original['payload']['headers']}
        to = headers.get('From', '')
        subject = headers.get('Subject', '')
        thread_id = original.get('threadId')
        
        # Create reply
        message = MIMEText(reply_text)
        message['to'] = to
        message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
        message['In-Reply-To'] = headers.get('Message-ID', '')
        message['References'] = headers.get('References', '') + ' ' + headers.get('Message-ID', '')
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        await loop.run_in_executor(
            None,
            partial(
                svc.users().messages().send(
                    userId='me',
                    body={'raw': raw, 'threadId': thread_id}
                ).execute
            )
        )
        
        log.info("gmail_reply_sent", message_id=message_id, to=to)
        return True
    except Exception as exc:
        log.error("gmail_reply_failed", error=str(exc), message_id=message_id)
        return False


async def get_contacts(limit: int = 100) -> list[dict]:
    """Get Gmail contacts from People API."""
    from api.core.cache import cached
    
    @cached("contacts_gmail", ttl=3600)
    async def _fetch_contacts():
        try:
            creds = _get_credentials()
            if creds is None:
                return []
            
            from googleapiclient.discovery import build as build_service
            people_service = build_service('people', 'v1', credentials=creds, cache_discovery=False)
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                partial(
                    people_service.people().connections().list(
                        resourceName='people/me',
                        pageSize=limit,
                        personFields='names,emailAddresses'
                    ).execute
                )
            )
            
            connections = results.get('connections', [])
            
            contacts = []
            for c in connections:
                names = c.get('names', [])
                emails = c.get('emailAddresses', [])
                
                if names and emails:
                    contacts.append({
                        "name": names[0].get('displayName', ''),
                        "email": emails[0].get('value', ''),
                        "platform": "gmail"
                    })
            
            log.info("gmail_contacts_fetched", count=len(contacts))
            return contacts
        except Exception as exc:
            log.error("gmail_contacts_failed", error=str(exc))
            return []
    
    return await _fetch_contacts()


async def search_messages(query: str, limit: int = 10) -> list[dict]:
    """Search Gmail messages."""
    try:
        svc = _get_service()
        if svc is None:
            return []
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            partial(
                svc.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=limit
                ).execute
            )
        )
        
        messages = results.get('messages', [])
        
        search_results = []
        for msg in messages:
            # Get message details
            details = await loop.run_in_executor(
                None,
                partial(
                    svc.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject']
                    ).execute
                )
            )
            
            headers = {h['name']: h['value'] for h in details['payload']['headers']}
            
            search_results.append({
                "id": msg['id'],
                "from": headers.get('From', ''),
                "subject": headers.get('Subject', ''),
                "snippet": details.get('snippet', '')
            })
        
        log.info("gmail_search_complete", query=query, results=len(search_results))
        return search_results
    except Exception as exc:
        log.error("gmail_search_failed", error=str(exc), query=query)
        return []

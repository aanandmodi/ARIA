"""
Google Calendar service — events, creation, free slot finding.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from api.core.config import settings
from api.core.logging import log

_calendar_service = None


@dataclass
class CalendarEvent:
    summary: str
    start: str
    end: str
    location: str
    description: str


def _get_credentials() -> Credentials | None:
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
        log.error("calendar_creds_failed", error=str(exc))
        return None


def _get_service():
    global _calendar_service
    if _calendar_service is not None:
        return _calendar_service
    creds = _get_credentials()
    if creds is None:
        return None
    _calendar_service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return _calendar_service


async def get_today_events() -> list[CalendarEvent]:
    """Get all events for today."""
    svc = _get_service()
    if svc is None:
        return []
    try:
        tz = ZoneInfo(settings.timezone)
        now = datetime.now(tz)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                svc.events().list(
                    calendarId="primary",
                    timeMin=start_of_day.isoformat(),
                    timeMax=end_of_day.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                ).execute
            ),
        )

        events = []
        for item in result.get("items", []):
            start = item.get("start", {}).get("dateTime", item.get("start", {}).get("date", ""))
            end = item.get("end", {}).get("dateTime", item.get("end", {}).get("date", ""))
            events.append(CalendarEvent(
                summary=item.get("summary", "Untitled"),
                start=start,
                end=end,
                location=item.get("location", ""),
                description=item.get("description", ""),
            ))
        return events
    except Exception as exc:
        log.error("calendar_today_failed", error=str(exc))
        return []


async def create_event(
    summary: str,
    start_time: str,
    end_time: str | None = None,
    description: str = "",
    attendees: list[str] | None = None,
) -> str:
    """Create a calendar event. Returns event ID."""
    svc = _get_service()
    if svc is None:
        return ""
    try:
        tz_str = settings.timezone
        if not end_time:
            # Default 1 hour duration
            start_dt = datetime.fromisoformat(start_time)
            end_dt = start_dt + timedelta(hours=1)
            end_time = end_dt.isoformat()

        body: dict = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": tz_str},
            "end": {"dateTime": end_time, "timeZone": tz_str},
            "description": description,
        }
        if attendees:
            body["attendees"] = [{"email": e} for e in attendees]

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                svc.events().insert(calendarId="primary", body=body).execute
            ),
        )
        event_id = result.get("id", "")
        log.info("calendar_event_created", event_id=event_id, summary=summary)
        return event_id
    except Exception as exc:
        log.error("calendar_create_failed", error=str(exc))
        return ""


async def find_free_slot(date_str: str, duration_minutes: int = 60) -> str | None:
    """Find the first free slot on a given date. Returns ISO start time or None."""
    svc = _get_service()
    if svc is None:
        return None
    try:
        tz = ZoneInfo(settings.timezone)
        target_date = datetime.fromisoformat(date_str).replace(tzinfo=tz)
        start_of_day = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=18, minute=0, second=0, microsecond=0)

        loop = asyncio.get_event_loop()
        body = {
            "timeMin": start_of_day.isoformat(),
            "timeMax": end_of_day.isoformat(),
            "timeZone": settings.timezone,
            "items": [{"id": "primary"}],
        }
        result = await loop.run_in_executor(
            None,
            partial(svc.freebusy().query(body=body).execute),
        )

        busy_periods = result.get("calendars", {}).get("primary", {}).get("busy", [])

        # Find first gap
        current = start_of_day
        for period in busy_periods:
            busy_start = datetime.fromisoformat(period["start"].replace("Z", "+00:00")).astimezone(tz)
            if (busy_start - current).total_seconds() >= duration_minutes * 60:
                return current.isoformat()
            busy_end = datetime.fromisoformat(period["end"].replace("Z", "+00:00")).astimezone(tz)
            current = max(current, busy_end)

        if (end_of_day - current).total_seconds() >= duration_minutes * 60:
            return current.isoformat()

        return None
    except Exception as exc:
        log.error("calendar_freeslot_failed", error=str(exc))
        return None

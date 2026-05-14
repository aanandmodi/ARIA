"""
Spotify service — play, now playing, queue, search via spotipy.
"""

from __future__ import annotations

import asyncio
from functools import partial

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from api.core.config import settings
from api.core.logging import log

_sp: spotipy.Spotify | None = None


def _get_spotify() -> spotipy.Spotify | None:
    global _sp
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        return None
    if _sp is None:
        auth = SpotifyOAuth(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret,
            redirect_uri=settings.spotify_redirect_uri,
            scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing",
        )
        _sp = spotipy.Spotify(auth_manager=auth)
    return _sp


async def now_playing() -> str:
    """Get currently playing track info."""
    sp = _get_spotify()
    if sp is None:
        return "Spotify not configured."
    try:
        loop = asyncio.get_event_loop()
        current = await loop.run_in_executor(None, sp.current_playback)
        if not current or not current.get("item"):
            return "Nothing is currently playing."
        item = current["item"]
        artists = ", ".join(a["name"] for a in item.get("artists", []))
        name = item.get("name", "Unknown")
        album = item.get("album", {}).get("name", "")
        progress_ms = current.get("progress_ms", 0)
        duration_ms = item.get("duration_ms", 1)
        progress_pct = round(progress_ms / duration_ms * 100)
        return f"🎵 {name} — {artists}\n💿 {album}\n⏱ {progress_pct}% played"
    except Exception as exc:
        log.error("spotify_now_playing_failed", error=str(exc))
        return "Could not get current playback."


async def play(query: str | None = None) -> str:
    """Resume playback, or search and play a track."""
    sp = _get_spotify()
    if sp is None:
        return "Spotify not configured."
    try:
        loop = asyncio.get_event_loop()
        if query:
            results = await loop.run_in_executor(
                None, partial(sp.search, q=query, type="track", limit=1)
            )
            tracks = results.get("tracks", {}).get("items", [])
            if not tracks:
                return f"No tracks found for '{query}'."
            track_uri = tracks[0]["uri"]
            track_name = tracks[0]["name"]
            artists = ", ".join(a["name"] for a in tracks[0].get("artists", []))
            await loop.run_in_executor(
                None, partial(sp.start_playback, uris=[track_uri])
            )
            return f"▶️ Playing: {track_name} — {artists}"
        else:
            await loop.run_in_executor(None, sp.start_playback)
            return "▶️ Playback resumed."
    except Exception as exc:
        log.error("spotify_play_failed", error=str(exc))
        return "Could not start playback."


async def pause() -> str:
    """Pause playback."""
    sp = _get_spotify()
    if sp is None:
        return "Spotify not configured."
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, sp.pause_playback)
        return "⏸ Playback paused."
    except Exception as exc:
        log.error("spotify_pause_failed", error=str(exc))
        return "Could not pause playback."


async def skip() -> str:
    """Skip to next track."""
    sp = _get_spotify()
    if sp is None:
        return "Spotify not configured."
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, sp.next_track)
        await asyncio.sleep(1)
        return await now_playing()
    except Exception as exc:
        log.error("spotify_skip_failed", error=str(exc))
        return "Could not skip track."


async def queue_track(query: str) -> str:
    """Search and add a track to the queue."""
    sp = _get_spotify()
    if sp is None:
        return "Spotify not configured."
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, partial(sp.search, q=query, type="track", limit=1)
        )
        tracks = results.get("tracks", {}).get("items", [])
        if not tracks:
            return f"No tracks found for '{query}'."
        track_uri = tracks[0]["uri"]
        track_name = tracks[0]["name"]
        await loop.run_in_executor(
            None, partial(sp.add_to_queue, track_uri)
        )
        return f"📋 Queued: {track_name}"
    except Exception as exc:
        log.error("spotify_queue_failed", error=str(exc))
        return "Could not queue track."

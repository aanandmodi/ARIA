"""
Voice note transcription via Groq Whisper.
"""

from __future__ import annotations

import io

from api.core.config import settings
from api.core.logging import log
from api.llm.client import get_groq_client


async def transcribe(audio_bytes: bytes, filename: str = "voice.ogg") -> str:
    """
    Transcribe audio bytes using Groq's Whisper endpoint.
    Returns the transcript text, or a fallback message on error.
    """
    try:
        client = get_groq_client()
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        response = await client.audio.transcriptions.create(
            model=settings.groq_whisper_model,
            file=audio_file,
            language=settings.language if settings.language != "en" else "en",
        )

        transcript = response.text.strip()
        log.info(
            "transcription_complete",
            length=len(transcript),
            model=settings.groq_whisper_model,
        )
        return transcript

    except Exception as exc:
        log.error("transcription_failed", error=str(exc))
        return "[Transcription failed — audio could not be processed]"

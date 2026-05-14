"""
MinIO file storage service.
"""
from __future__ import annotations
import asyncio, io
from functools import partial
from api.core.config import settings
from api.core.logging import log
from api.core.storage import get_s3_client

async def upload(file_bytes: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    """Upload bytes to MinIO. Returns the object key."""
    try:
        client = get_s3_client()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, partial(client.put_object, Bucket=settings.minio_bucket, Key=key, Body=io.BytesIO(file_bytes), ContentLength=len(file_bytes), ContentType=content_type))
        log.info("minio_uploaded", key=key, size=len(file_bytes))
        return key
    except Exception as exc:
        log.error("minio_upload_failed", error=str(exc), key=key)
        return ""

async def download(key: str) -> bytes:
    """Download object from MinIO. Returns bytes."""
    try:
        client = get_s3_client()
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, partial(client.get_object, Bucket=settings.minio_bucket, Key=key))
        data = resp["Body"].read()
        log.info("minio_downloaded", key=key, size=len(data))
        return data
    except Exception as exc:
        log.error("minio_download_failed", error=str(exc), key=key)
        return b""

async def get_url(key: str, expires: int = 3600) -> str:
    """Generate a presigned URL for an object."""
    try:
        client = get_s3_client()
        loop = asyncio.get_event_loop()
        url = await loop.run_in_executor(None, partial(client.generate_presigned_url, "get_object", Params={"Bucket": settings.minio_bucket, "Key": key}, ExpiresIn=expires))
        return url
    except Exception as exc:
        log.error("minio_url_failed", error=str(exc), key=key)
        return ""

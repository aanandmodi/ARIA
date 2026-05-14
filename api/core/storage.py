"""
MinIO (S3-compatible) client singleton.
"""

from __future__ import annotations

import asyncio
from functools import partial
from typing import Any

import boto3
from botocore.config import Config as BotoConfig

from api.core.config import settings
from api.core.logging import log

_s3_client: Any = None


def _build_client() -> Any:
    """Build a synchronous boto3 S3 client pointing at MinIO."""
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_host}:{settings.minio_port}",
        aws_access_key_id=settings.minio_root_user,
        aws_secret_access_key=settings.minio_root_password,
        config=BotoConfig(signature_version="s3v4"),
        region_name="us-east-1",
    )


def get_s3_client() -> Any:
    """Return (and lazily create) the MinIO/S3 client."""
    global _s3_client
    if _s3_client is None:
        _s3_client = _build_client()
    return _s3_client


async def ensure_bucket() -> None:
    """Create the default bucket if it does not already exist."""
    loop = asyncio.get_event_loop()
    client = get_s3_client()
    try:
        buckets = await loop.run_in_executor(None, client.list_buckets)
        existing = {b["Name"] for b in buckets.get("Buckets", [])}
        if settings.minio_bucket not in existing:
            await loop.run_in_executor(
                None,
                partial(client.create_bucket, Bucket=settings.minio_bucket),
            )
            log.info("minio_bucket_created", bucket=settings.minio_bucket)
        else:
            log.info("minio_bucket_exists", bucket=settings.minio_bucket)
    except Exception as exc:
        log.error("minio_bucket_check_failed", error=str(exc))

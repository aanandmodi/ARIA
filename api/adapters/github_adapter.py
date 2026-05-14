"""
GitHub adapter — parses GitHub webhook/notification payloads into InboundMessage.
"""

from __future__ import annotations

from datetime import datetime

from api.adapters.base import InboundMessage
from api.core.logging import log


def parse(raw_payload: dict) -> InboundMessage | None:
    """
    Parse a GitHub webhook event or notification digest item into InboundMessage.
    """
    try:
        action = raw_payload.get("action", "")
        repo = raw_payload.get("repository", {})
        repo_name = repo.get("full_name", "unknown/repo")
        sender = raw_payload.get("sender", {})
        sender_login = sender.get("login", "github")

        # Determine event type and build content
        content = ""
        subject = ""

        if "pull_request" in raw_payload:
            pr = raw_payload["pull_request"]
            subject = f"PR #{pr.get('number', '')}: {pr.get('title', '')}"
            content = (
                f"[{action}] {subject}\n"
                f"by {pr.get('user', {}).get('login', 'unknown')}\n"
                f"Repo: {repo_name}\n"
                f"URL: {pr.get('html_url', '')}"
            )
        elif "issue" in raw_payload:
            issue = raw_payload["issue"]
            subject = f"Issue #{issue.get('number', '')}: {issue.get('title', '')}"
            content = (
                f"[{action}] {subject}\n"
                f"by {issue.get('user', {}).get('login', 'unknown')}\n"
                f"Repo: {repo_name}\n"
                f"URL: {issue.get('html_url', '')}"
            )
        elif "comment" in raw_payload:
            comment = raw_payload["comment"]
            subject = f"Comment on {repo_name}"
            content = (
                f"[{action}] New comment by {comment.get('user', {}).get('login', '')}\n"
                f"Body: {comment.get('body', '')[:500]}\n"
                f"URL: {comment.get('html_url', '')}"
            )
        else:
            # Generic event
            subject = f"GitHub event: {action} on {repo_name}"
            content = f"Action: {action}\nRepo: {repo_name}\nSender: {sender_login}"

        message_id = (
            raw_payload.get("delivery", "")
            or str(raw_payload.get("id", ""))
            or f"gh_{datetime.utcnow().timestamp()}"
        )

        return InboundMessage(
            platform="github",
            message_id=message_id,
            thread_id=repo_name,
            sender_id=sender_login,
            sender_name=sender_login,
            content=content,
            raw=raw_payload,
            received_at=datetime.utcnow(),
            subject=subject,
        )
    except Exception as exc:
        log.error("github_adapter_parse_error", error=str(exc))
        return None

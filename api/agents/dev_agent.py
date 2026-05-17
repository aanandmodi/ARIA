"""
Dev Agent - Handles GitHub and development operations.
"""
from __future__ import annotations

from api.agents.base_agent import BaseAgent, AgentState
from api.core.logging import log
from api.services import github_service


class DevAgent(BaseAgent):
    """
    Specialized agent for development operations:
    - GitHub PRs, issues, commits
    - Code search
    - Repository management
    """
    
    def __init__(self):
        super().__init__(
            name="dev",
            description="Handles GitHub and development operations"
        )
        self.supported_intents = {"github_action"}
    
    def can_handle(self, intent: str, context: dict) -> bool:
        """Check if this agent can handle the intent."""
        return intent in self.supported_intents
    
    async def process(self, state: AgentState) -> AgentState:
        """Process GitHub-related requests."""
        self.log_action("processing", intent=state.intent)
        
        try:
            action = state.context.get("action", "notifications")
            
            if action == "notifications":
                result = await self._handle_notifications()
            elif action == "prs":
                result = await self._handle_prs()
            elif action == "issues":
                result = await self._handle_issues()
            elif action == "merge":
                result = await self._handle_merge(state.context)
            elif action == "close":
                result = await self._handle_close(state.context)
            elif action == "comment":
                result = await self._handle_comment(state.context)
            elif action == "create_issue":
                result = await self._handle_create_issue(state.context)
            elif action == "commit":
                result = await self._handle_commit(state.context)
            elif action == "create_pr":
                result = await self._handle_create_pr(state.context)
            else:
                result = await self._handle_digest()
            
            state.result = result
            state.tools_used.append(f"github_{action}")
            
        except Exception as exc:
            log.error("dev_agent_error", error=str(exc), action=action)
            state.result = "⚠️ An error occurred while accessing GitHub."
        
        return state
    
    async def _handle_notifications(self) -> str:
        """Get GitHub notifications."""
        notifs = await github_service.get_notifications()
        
        if not notifs:
            return "🐙 No unread GitHub notifications."
        
        lines = ["🐙 <b>GitHub Notifications</b>\n"]
        for n in notifs[:10]:
            lines.append(f"• <b>{n['type']}</b>: {n['title']} ({n['repo']})")
        
        return "\n".join(lines)
    
    async def _handle_prs(self) -> str:
        """Get open PRs."""
        digest = await github_service.get_digest()
        return f"🐙 <b>GitHub PRs/Issues</b>\n\n{digest}"
    
    async def _handle_issues(self) -> str:
        """Get open issues."""
        digest = await github_service.get_digest()
        return f"🐙 <b>GitHub Issues</b>\n\n{digest}"
    
    async def _handle_merge(self, context: dict) -> str:
        """Merge a PR."""
        repo = context.get("repo")
        number = context.get("number")
        
        if not repo or not number:
            return "⚠️ Please specify repository and PR number."
        
        success = await github_service.merge_pr(repo, int(number))
        return "✅ PR merged successfully!" if success else "❌ Failed to merge PR."
    
    async def _handle_close(self, context: dict) -> str:
        """Close an issue or PR."""
        repo = context.get("repo")
        number = context.get("number")
        
        if not repo or not number:
            return "⚠️ Please specify repository and issue/PR number."
        
        success = await github_service.close_issue(repo, int(number))
        return "✅ Issue/PR closed!" if success else "❌ Failed to close."
    
    async def _handle_comment(self, context: dict) -> str:
        """Comment on an issue or PR."""
        repo = context.get("repo")
        number = context.get("number")
        text = context.get("text")
        
        if not repo or not number or not text:
            return "⚠️ Please specify repository, issue number, and comment text."
        
        success = await github_service.comment_issue(repo, int(number), text)
        return "✅ Comment added!" if success else "❌ Failed to add comment."
    
    async def _handle_create_issue(self, context: dict) -> str:
        """Create a new issue."""
        repo = context.get("repo")
        title = context.get("text") or context.get("title")
        body = context.get("body", "")
        
        if not repo or not title:
            return "⚠️ Please specify repository and issue title."
        
        url = await github_service.create_issue(repo, title, body)
        return f"✅ Issue created: {url}" if url else "❌ Failed to create issue."
    
    async def _handle_commit(self, context: dict) -> str:
        """Create a commit."""
        repo = context.get("repo")
        branch = context.get("branch", "main")
        message = context.get("message")
        files = context.get("files", {})
        
        if not repo or not message:
            return "⚠️ Please specify repository and commit message."
        
        # This would require implementing commit functionality in github_service
        return "⚠️ Commit functionality coming soon. Use GitHub CLI or web interface for now."
    
    async def _handle_create_pr(self, context: dict) -> str:
        """Create a pull request."""
        repo = context.get("repo")
        title = context.get("title")
        head = context.get("head")
        base = context.get("base", "main")
        body = context.get("body", "")
        
        if not repo or not title or not head:
            return "⚠️ Please specify repository, PR title, and head branch."
        
        # This would require implementing PR creation in github_service
        return "⚠️ PR creation functionality coming soon. Use GitHub CLI or web interface for now."
    
    async def _handle_digest(self) -> str:
        """Get GitHub digest."""
        digest = await github_service.get_digest()
        return f"🐙 <b>GitHub Digest</b>\n\n{digest}"

# Made with Bob

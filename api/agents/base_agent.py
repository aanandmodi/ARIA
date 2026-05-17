"""
Base agent class for LangGraph multi-agent system.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq

from api.core.config import settings
from api.core.logging import log


@dataclass
class AgentState:
    """Shared state passed between agents."""
    messages: list[BaseMessage] = field(default_factory=list)
    user_query: str = ""
    intent: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    result: str = ""
    next_agent: str | None = None
    tools_used: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all specialized agents."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model="llama-3.1-8b-instant",  # Fast model for agents
            temperature=0.3,
        )
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """Process the current state and return updated state."""
        pass
    
    @abstractmethod
    def can_handle(self, intent: str, context: dict) -> bool:
        """Determine if this agent can handle the given intent."""
        pass
    
    async def _call_llm(self, prompt: str, system: str | None = None) -> str:
        """Helper to call LLM with error handling."""
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as exc:
            log.error(f"{self.name}_llm_error", error=str(exc))
            return ""
    
    def log_action(self, action: str, **kwargs):
        """Log agent actions."""
        log.info(f"{self.name}_action", action=action, **kwargs)

# Made with Bob

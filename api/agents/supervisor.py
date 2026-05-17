"""
Supervisor Agent - Routes requests to specialized agents.
"""
from __future__ import annotations

from api.agents.base_agent import BaseAgent, AgentState
from api.core.logging import log


class SupervisorAgent(BaseAgent):
    """
    Supervisor agent that analyzes requests and routes to specialized agents.
    Acts as the orchestrator in the multi-agent system.
    """
    
    def __init__(self):
        super().__init__(
            name="supervisor",
            description="Routes user requests to specialized agents"
        )
        self.agent_registry = {}
    
    def register_agent(self, agent: BaseAgent):
        """Register a specialized agent."""
        self.agent_registry[agent.name] = agent
        log.info("agent_registered", name=agent.name)
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze the request and determine which agent should handle it.
        """
        self.log_action("routing_request", intent=state.intent)
        
        # Find the best agent for this intent
        best_agent = None
        for agent in self.agent_registry.values():
            if agent.can_handle(state.intent, state.context):
                best_agent = agent
                break
        
        if best_agent:
            state.next_agent = best_agent.name
            self.log_action("agent_selected", agent=best_agent.name)
        else:
            # No specialized agent found, handle as general conversation
            state.next_agent = "conversation"
            self.log_action("fallback_to_conversation")
        
        return state
    
    def can_handle(self, intent: str, context: dict) -> bool:
        """Supervisor always handles routing."""
        return True
    
    async def route_to_agent(self, state: AgentState) -> AgentState:
        """Execute the selected agent."""
        if state.next_agent and state.next_agent in self.agent_registry:
            agent = self.agent_registry[state.next_agent]
            return await agent.process(state)
        return state

# Made with Bob

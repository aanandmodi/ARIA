"""
Inbox Agent - Handles email, WhatsApp, SMS operations.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from api.agents.base_agent import BaseAgent, AgentState
from api.core.logging import log
from api.services import gmail_service, whatsapp_service, sms_service


class InboxAgent(BaseAgent):
    """
    Specialized agent for inbox operations:
    - Reply to messages
    - Compose emails
    - Send WhatsApp/SMS
    - List contacts
    - Search messages
    """
    
    def __init__(self):
        super().__init__(
            name="inbox",
            description="Handles email, WhatsApp, and SMS operations"
        )
        self.supported_intents = {
            "reply", "compose_email", "send_whatsapp", 
            "send_sms", "list_contacts", "search"
        }
    
    def can_handle(self, intent: str, context: dict) -> bool:
        """Check if this agent can handle the intent."""
        return intent in self.supported_intents
    
    async def process(self, state: AgentState) -> AgentState:
        """Process inbox-related requests."""
        self.log_action("processing", intent=state.intent)
        
        try:
            if state.intent == "reply":
                result = await self._handle_reply(state)
            elif state.intent == "compose_email":
                result = await self._handle_compose_email(state)
            elif state.intent == "send_whatsapp":
                result = await self._handle_send_whatsapp(state)
            elif state.intent == "send_sms":
                result = await self._handle_send_sms(state)
            elif state.intent == "list_contacts":
                result = await self._handle_list_contacts(state)
            elif state.intent == "search":
                result = await self._handle_search(state)
            else:
                result = "I'm not sure how to help with that inbox operation."
            
            state.result = result
            state.tools_used.append(f"inbox_{state.intent}")
            
        except Exception as exc:
            log.error("inbox_agent_error", error=str(exc), intent=state.intent)
            state.result = "⚠️ An error occurred while processing your inbox request."
        
        return state
    
    async def _handle_reply(self, state: AgentState) -> str:
        """Handle replying to messages."""
        # Extract message context
        message_id = state.context.get("message_id")
        reply_text = state.context.get("reply_text") or state.user_query
        
        if not message_id:
            return "⚠️ I need to know which message to reply to. Please select a message first."
        
        # Determine platform and send reply
        platform = state.context.get("platform", "email")
        
        if platform == "email":
            # Use Gmail service
            success = await gmail_service.send_reply(message_id, reply_text)
            return "✅ Email reply sent!" if success else "❌ Failed to send email reply."
        
        elif platform == "whatsapp":
            # Use WhatsApp service
            contact = state.context.get("contact")
            if contact:
                success = await whatsapp_service.send_message(contact, reply_text)
                return "✅ WhatsApp message sent!" if success else "❌ Failed to send WhatsApp message."
        
        return "⚠️ Unsupported platform for replies."
    
    async def _handle_compose_email(self, state: AgentState) -> str:
        """Handle composing new emails."""
        to = state.context.get("to")
        subject = state.context.get("subject", "")
        body = state.context.get("body", state.user_query)
        
        if not to:
            return "⚠️ Please specify the recipient email address."
        
        success = await gmail_service.send_email(to, subject, body)
        return f"✅ Email sent to {to}!" if success else "❌ Failed to send email."
    
    async def _handle_send_whatsapp(self, state: AgentState) -> str:
        """Handle sending WhatsApp messages."""
        contact = state.context.get("contact_name") or state.context.get("phone")
        message = state.context.get("message", "")
        
        if not contact:
            return "⚠️ Please specify the contact name or phone number."
        
        if not message:
            return "⚠️ Please specify the message to send."
        
        # Resolve contact name to phone number if needed
        if "@" not in contact and "+" not in contact:
            # Look up contact by name
            phone = await self._resolve_contact_name(contact)
            if not phone:
                return f"⚠️ Could not find contact: {contact}"
            contact = phone
        
        success = await whatsapp_service.send_message(contact, message)
        return f"✅ WhatsApp message sent to {contact}!" if success else "❌ Failed to send WhatsApp message."
    
    async def _handle_send_sms(self, state: AgentState) -> str:
        """Handle sending SMS messages."""
        to = state.context.get("to")
        message = state.context.get("message", "")
        
        if not to or not message:
            return "⚠️ Please specify both recipient and message."
        
        success = await sms_service.send_sms(to, message)
        return f"✅ SMS sent to {to}!" if success else "❌ Failed to send SMS."
    
    async def _handle_list_contacts(self, state: AgentState) -> str:
        """Handle listing contacts."""
        platform = state.context.get("platform", "all")
        
        contacts = []
        
        if platform in ("whatsapp", "all"):
            wa_contacts = await whatsapp_service.get_contacts()
            contacts.extend([f"📱 {c['name']} ({c['phone']})" for c in wa_contacts[:10]])
        
        if platform in ("gmail", "all"):
            gmail_contacts = await gmail_service.get_contacts()
            contacts.extend([f"📧 {c['name']} ({c['email']})" for c in gmail_contacts[:10]])
        
        if not contacts:
            return "No contacts found."
        
        return "<b>Your Contacts:</b>\n\n" + "\n".join(contacts)
    
    async def _handle_search(self, state: AgentState) -> str:
        """Handle searching messages."""
        query = state.context.get("query", state.user_query)
        platform = state.context.get("platform", "all")
        
        results = []
        
        if platform in ("email", "all"):
            email_results = await gmail_service.search_messages(query, limit=5)
            results.extend([f"📧 {r['subject']} - {r['from']}" for r in email_results])
        
        if platform in ("whatsapp", "all"):
            wa_results = await whatsapp_service.search_messages(query, limit=5)
            results.extend([f"💬 {r['contact']} - {r['preview']}" for r in wa_results])
        
        if not results:
            return f"No messages found matching '{query}'."
        
        return f"<b>Search Results for '{query}':</b>\n\n" + "\n".join(results)
    
    async def _resolve_contact_name(self, name: str) -> str | None:
        """Resolve contact name to phone number or email."""
        # Try WhatsApp first
        wa_contacts = await whatsapp_service.get_contacts()
        for contact in wa_contacts:
            if name.lower() in contact.get("name", "").lower():
                return contact.get("phone")
        
        # Try Gmail
        gmail_contacts = await gmail_service.get_contacts()
        for contact in gmail_contacts:
            if name.lower() in contact.get("name", "").lower():
                return contact.get("email")
        
        return None

# Made with Bob

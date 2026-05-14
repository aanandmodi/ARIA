"""
SMS outbound adapter.
"""
import os
from api.adapters.base import BaseAdapter
from api.core.logging import log

class SmsAdapter(BaseAdapter):
    async def send_message(self, to_id: str, text: str, **kwargs) -> bool:
        """
        Send an SMS. Usually via Twilio.
        """
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException
        
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_PHONE_NUMBER")
        
        if not all([account_sid, auth_token, from_number]):
            log.warning("twilio_credentials_missing", to=to_id)
            return False
            
        try:
            client = Client(account_sid, auth_token)
            # Twilio's python library is sync by default, but we can wrap it or just call it since it's fast
            # For strict async, we might want run_in_executor
            message = client.messages.create(
                body=text,
                from_=from_number,
                to=to_id
            )
            log.info("sms_sent", to=to_id, sid=message.sid)
            return True
        except TwilioRestException as exc:
            log.error("sms_send_failed", error=str(exc))
            return False
        except Exception as exc:
            log.error("sms_send_error", error=str(exc))
            return False

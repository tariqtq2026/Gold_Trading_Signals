
import os
import datetime
from twilio.rest import Client

ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP = os.environ.get("TWILIO_WHATSAPP_NUMBER")
TO_WHATSAPP = os.environ.get("MY_WHATSAPP_NUMBER")

def send_whatsapp_alert():
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    
    message_body = (
        f"🚨 *LONDON/NY SESSION ALERT (XAUUSD)* 🚨\n\n"
        f"⏰ *Time:* {current_time} PKT\n"
        f"📌 Market Open! Check charts for trade setups:\n\n"
        f"1. *Resistance Sweep:* Look for rejection at high levels.\n"
        f"2. *Breakdown:* Check 15m candle close below Support.\n"
        f"3. *VSA Filter:* Ensure high volume spike on M15 close."
    )
    
    message = client.messages.create(
        body=message_body,
        from_=FROM_WHATSAPP,
        to=TO_WHATSAPP
    )
    
    print(f"Message sent successfully! SID: {message.sid}")

if __name__ == "__main__":
    send_whatsapp_alert()

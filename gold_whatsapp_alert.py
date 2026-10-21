import os
import requests
import datetime

ID_INSTANCE = os.environ.get("GREEN_ID_INSTANCE")
API_TOKEN = os.environ.get("GREEN_API_TOKEN")
PHONE_NUMBER = os.environ.get("MY_WHATSAPP_NUMBER")  # Example: 923001234567

def send_whatsapp_alert():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    
    message = (
        f"🚨 *LONDON/NY SESSION ALERT (XAUUSD)* 🚨\n\n"
        f"⏰ *Time:* {current_time} PKT\n"
        f"📌 Market Open! Check charts for trade setups:\n\n"
        f"1. *Resistance Sweep:* Look for rejection at high levels.\n"
        f"2. *Breakdown:* Check 15m candle close below Support.\n"
        f"3. *VSA Filter:* Ensure high volume spike on M15 close."
    )
    
    url = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
    
    payload = {
        "chatId": f"{PHONE_NUMBER}@c.us",
        "message": message
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Message sent successfully via Green API!")
    else:
        print(f"Failed to send message: {response.text}")

if __name__ == "__main__":
    send_whatsapp_alert()

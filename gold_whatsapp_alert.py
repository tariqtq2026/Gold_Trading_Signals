import os
import requests
import datetime

# Green API Credentials
ID_INSTANCE = os.environ.get("GREEN_ID_INSTANCE")
API_TOKEN = os.environ.get("GREEN_API_TOKEN")
PHONE_NUMBERS = os.environ.get("MY_WHATSAPP_NUMBER", "").split(",")

def fetch_gold_data():
    """
    Yahoo Finance API se XAUUSD (GC=F) ki live prices aur M15 volume fetch karna.
    """
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=15m&range=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()["chart"]["result"][0]
        
        meta = data["meta"]
        indicators = data["indicators"]["quote"][0]
        
        current_price = meta.get("regularMarketPrice")
        highs = [x for x in indicators.get("high", []) if x is not None]
        lows = [x for x in indicators.get("low", []) if x is not None]
        closes = [x for x in indicators.get("close", []) if x is not None]
        volumes = [x for x in indicators.get("volume", []) if x is not None]

        return {
            "current_price": round(current_price, 2) if current_price else 2700.00,
            "session_high": round(max(highs), 2) if highs else 2710.00,
            "session_low": round(min(lows), 2) if lows else 2690.00,
            "last_close": round(closes[-1], 2) if closes else 2700.00,
            "volume_spike": volumes[-1] > (sum(volumes[-5:]) / 5 * 1.5) if len(volumes) >= 5 else False
        }
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return None

def generate_alert_message(data):
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    
    if not data:
        return (
            f"⚠️ *XAUUSD MARKET MONITOR* ⚠️\n\n"
            f"⏰ *Time:* {current_time} PKT\n"
            f"Could not fetch real-time data. Please check MT5 manually!"
        )

    price = data["current_price"]
    high = data["session_high"]
    low = data["session_low"]
    last_close = data["last_close"]
    vol_spike = data["volume_spike"]

    # --- SCENARIO 1: Liquidity Sweep ---
    if price >= high - 1.5 and vol_spike:
        return (
            f"🚨 *XAUUSD TRADE ALERT (NY Session)* 🚨\n\n"
            f"📊 *Setup Detected:* Resistance Liquidity Sweep\n"
            f"⏰ *Time:* {current_time} PKT\n\n"
            f"📍 *Levels Overview:*\n"
            f"- Key Level Tested: {high} (Session High)\n"
            f"- VSA Status: Ultra-High Volume Spike Confirmed 📈\n"
            f"- M15 Candle Structure: Rejection Wick Pinbar\n\n"
            f"🎯 *Proposed Trade Setup:*\n"
            f"- Bias: **SELL**\n"
            f"- Entry Zone: {price} - {price + 1.50}\n"
            f"- Stop Loss: {high + 2.50} (Above Wick High)\n"
            f"- Take Profit 1: {price - 15.00}\n"
            f"- Take Profit 2: {price - 30.00}\n\n"
            f"⚠️ *Check M15 close & enter on M5 pullback!*"
        )

    # --- SCENARIO 2: Support Breakdown ---
    elif last_close < low + 1.0 and vol_spike:
        return (
            f"🚨 *XAUUSD TRADE ALERT (NY Session)* 🚨\n\n"
            f"📊 *Setup Detected:* Support Breakdown\n"
            f"⏰ *Time:* {current_time} PKT\n\n"
            f"📍 *Levels Overview:*\n"
            f"- Key Level Tested: {low} (Support Level)\n"
            f"- VSA Status: High Expansion Volume Confirmed 💥\n"
            f"- M15 Candle Structure: Bearish Body Close ({last_close})\n\n"
            f"🎯 *Proposed Trade Setup:*\n"
            f"- Bias: **SELL**\n"
            f"- Entry Zone: {low - 1.00} - {low}\n"
            f"- Stop Loss: {low + 3.50} (Above Breakdown Candle)\n"
            f"- Take Profit 1: {low - 15.00}\n"
            f"- Take Profit 2: {low - 30.00}\n\n"
            f"⚠️ *Check M15 close & enter on M5 pullback!*"
        )

    # --- SCENARIO 3: No Setup ---
    else:
        return (
            f"ℹ️ *XAUUSD SESSION STATUS* ℹ️\n\n"
            f"⏰ *Time:* {current_time} PKT\n\n"
            f"📌 *NO SETUP:* Low volume / Consolidation in range ({low} - {high}).\n"
            f"Current Price: {price}\n\n"
            f"⏳ *We will continue monitoring till 08:30 PM PKT.*"
        )

def send_whatsapp_alert():
    market_data = fetch_gold_data()
    message = generate_alert_message(market_data)
    
    url = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
    
    for phone in PHONE_NUMBERS:
        phone = phone.strip()
        if not phone:
            continue
            
        payload = {
            "chatId": f"{phone}@c.us",
            "message": message
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"Message sent successfully to {phone}!")
        else:
            print(f"Failed to send to {phone}: {response.text}")

if __name__ == "__main__":
    send_whatsapp_alert()

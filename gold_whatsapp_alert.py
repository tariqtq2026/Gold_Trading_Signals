import os
import requests
import datetime

# Green API Credentials
ID_INSTANCE = os.environ.get("GREEN_ID_INSTANCE")
API_TOKEN = os.environ.get("GREEN_API_TOKEN")
PHONE_NUMBERS = os.environ.get("MY_WHATSAPP_NUMBER", "").split(",")

# Monitor kiye jane wale assets aur unke Yahoo Finance Tickers
ASSETS = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "BTCUSD": "BTC-USD"
}

def fetch_market_data(ticker):
    """
    Yahoo Finance API se kisi bhi asset ki live prices aur volume fetch karna.
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=15m&range=1d"
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
            "current_price": round(current_price, 4) if current_price else 0.0,
            "session_high": round(max(highs), 4) if highs else 0.0,
            "session_low": round(min(lows), 4) if lows else 0.0,
            "last_close": round(closes[-1], 4) if closes else 0.0,
            "volume_spike": volumes[-1] > (sum(volumes[-5:]) / 5 * 1.5) if len(volumes) >= 5 else False
        }
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def generate_alert_message(name, data):
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    
    if not data:
        return f"⚠️ *{name} MARKET MONITOR* ⚠️\nCould not fetch real-time data."

    price = data["current_price"]
    high = data["session_high"]
    low = data["session_low"]
    last_close = data["last_close"]
    vol_spike = data["volume_spike"]

    # --- SCENARIO 1: Resistance Sweep ---
    if price >= high - (high * 0.0005) and vol_spike:
        return (
            f"🚨 *{name} TRADE ALERT* 🚨\n\n"
            f"📊 *Setup Detected:* Resistance Liquidity Sweep\n"
            f"⏰ *Time:* {current_time} PKT\n\n"
            f"📍 *Levels Overview:*\n"
            f"- Key Level Tested: {high} (Session High)\n"
            f"- VSA Status: Ultra-High Volume Spike Confirmed 📈\n\n"
            f"🎯 *Proposed Setup:*\n"
            f"- Bias: **SELL**\n"
            f"- Current Price: {price}\n"
            f"- Stop Loss: {round(high * 1.001, 4)}\n"
            f"- Take Profit: {round(price - (high - low) * 0.5, 4)}"
        )

    # --- SCENARIO 2: Support Breakdown ---
    elif last_close < low + (low * 0.0005) and vol_spike:
        return (
            f"🚨 *{name} BREAKDOWN ALERT* 🚨\n\n"
            f"📊 *Setup Detected:* Support Breakdown\n"
            f"⏰ *Time:* {current_time} PKT\n\n"
            f"📍 *Levels Overview:*\n"
            f"- Key Level Tested: {low} (Support Level)\n"
            f"- VSA Status: High Expansion Volume Confirmed 💥\n\n"
            f"🎯 *Proposed Setup:*\n"
            f"- Bias: **SELL**\n"
            f"- Current Price: {price}\n"
            f"- Stop Loss: {round(low * 1.002, 4)}\n"
            f"- Take Profit: {round(price - ((high - low) if high > low else 10), 4)}"
        )

    # --- SCENARIO 3: No Setup ---
    else:
        return (
            f"ℹ️ *{name} SESSION STATUS* ℹ️\n\n"
            f"⏰ *Time:* {current_time} PKT\n"
            f"📌 *NO SETUP:* Low volume / Consolidation in range ({low} - {high}).\n"
            f"Current Price: {price}"
        )

def run_bot():
    url = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
    
    for name, ticker in ASSETS.items():
        market_data = fetch_market_data(ticker)
        message = generate_alert_message(name, market_data)
        
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
                print(f"{name} alert sent to {phone} successfully!")
            else:
                print(f"Failed to send {name} to {phone}: {response.text}")

if __name__ == "__main__":
    run_bot()

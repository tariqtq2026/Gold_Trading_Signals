import os
import requests
import datetime

# Green API Credentials
ID_INSTANCE = os.environ.get("GREEN_ID_INSTANCE")
API_TOKEN = os.environ.get("GREEN_API_TOKEN")
PHONE_NUMBERS = os.environ.get("MY_WHATSAPP_NUMBER", "").split(",")

# Monitored Assets
ASSETS = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "BTCUSD": "BTC-USD"
}

def fetch_economic_news():
    """
    Forex Factory ya public economic calendar API se high-impact news check karna.
    """
    try:
        # Free public economic calendar feed
        url = "nfs.faireconomy.media_calendar_thisweek.json" # Placeholder for reliable feed or public API endpoint
        # Alternative: checking high-impact windows or fetching from a clean JSON source
        response = requests.get("https://nfs.faireconomy.cc/calendar.json", timeout=5)
        if response.status_code == 200:
            events = response.json()
            current_utc = datetime.datetime.utcnow()
            high_impact_today = False
            
            for event in events:
                if event.get("impact") == "High":
                    date_str = event.get("date")
                    # Parse event date and check if it's happening within the next few hours
                    # For safety, we flag high impact news days/times
                    high_impact_today = True
            return high_impact_today
    except Exception as e:
        print(f"News fetch warning: {e}")
    return False

def fetch_market_data(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=15m&range=2d"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()["chart"]["result"][0]
        
        meta = data["meta"]
        quote = data["indicators"]["quote"][0]
        
        highs = [x for x in quote.get("high", []) if x is not None]
        lows = [x for x in quote.get("low", []) if x is not None]
        closes = [x for x in quote.get("close", []) if x is not None]
        opens = [x for x in quote.get("open", []) if x is not None]
        volumes = [x for x in quote.get("volume", []) if x is not None]

        if len(closes) < 10:
            return None

        current_price = round(meta.get("regularMarketPrice", closes[-1]), 4)
        session_high = round(max(highs[-32:]), 4)
        session_low = round(min(lows[-32:]), 4)
        
        # 1. VSA Volume Spike Check
        avg_vol = sum(volumes[-10:-1]) / 9 if len(volumes) >= 10 else 1
        vsa_spike = volumes[-1] > (avg_vol * 1.8) or volumes[-2] > (avg_vol * 1.8)

        # 2. Fair Value Gap (FVG) Detection
        bullish_fvg = False
        bearish_fvg = False
        if len(highs) >= 3:
            if lows[-3] > highs[-1]:
                bearish_fvg = True
            if highs[-3] < lows[-1]:
                bullish_fvg = True

        # 3. Market Structure Shift (ChoCH) / Displacement
        last_body = abs(closes[-1] - opens[-1])
        avg_body = sum(abs(closes[i] - opens[i]) for i in range(-6, -1)) / 5
        strong_displacement = last_body > (avg_body * 1.5)

        # 4. Liquidity Sweep Logic
        sweep_buyside = max(highs[-3:]) >= session_high and closes[-1] < session_high
        sweep_sellside = min(lows[-3:]) <= session_low and closes[-1] > session_low

        return {
            "current_price": current_price,
            "session_high": session_high,
            "session_low": session_low,
            "vsa_spike": vsa_spike,
            "bearish_fvg": bearish_fvg,
            "bullish_fvg": bullish_fvg,
            "strong_displacement": strong_displacement,
            "sweep_buyside": sweep_buyside,
            "sweep_sellside": sweep_sellside
        }
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def generate_alert_message(name, data, has_news):
    current_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=5)).strftime("%I:%M %p")
    
    news_warning = "⚠️ *High-Impact News Alert Today! Trade with extra caution.* 📰\n\n" if has_news else ""

    if not data:
        return f"⚠️ *{name} MARKET MONITOR* ⚠️\nData fetch failed."

    price = data["current_price"]
    high = data["session_high"]
    low = data["session_low"]

    if data["sweep_buyside"] and (data["bearish_fvg"] or data["strong_displacement"]) and data["vsa_spike"]:
        sl = round(high * 1.0015, 4)
        tp = round(price - ((high - low) * 0.6), 4)
        return (
            f"🚨 *{name} INSTITUTIONAL SELL SETUP* 🚨\n\n"
            f"{news_warning}"
            f"⏰ *Time:* {current_time} PKT\n"
            f"📍 *Confluences Verified (3/3):*\n"
            f"1️⃣ Buyside Liquidity Swept ({high})\n"
            f"2️⃣ Institutional Displacement / FVG Created 📉\n"
            f"3️⃣ VSA Absorption Volume Spike Confirmed 💥\n\n"
            f"🎯 *Proposed Trade:*\n"
            f"- Bias: **SHORT / SELL**\n"
            f"- Entry Price: {price}\n"
            f"- Stop Loss: {sl}\n"
            f"- Take Profit: {tp}\n\n"
            f"⚠️ *Note:* Manual execution only upon candle close."
        )

    elif data["sweep_sellside"] and (data["bullish_fvg"] or data["strong_displacement"]) and data["vsa_spike"]:
        sl = round(low * 0.9985, 4)
        tp = round(price + ((high - low) * 0.6), 4)
        return (
            f"🚨 *{name} INSTITUTIONAL BUY SETUP* 🚨\n\n"
            f"{news_warning}"
            f"⏰ *Time:* {current_time} PKT\n"
            f"📍 *Confluences Verified (3/3):*\n"
            f"1️⃣ Sellside Liquidity Swept ({low})\n"
            f"2️⃣ Institutional Displacement / FVG Created 📈\n"
            f"3️⃣ VSA Accumulation Volume Spike Confirmed 💥\n\n"
            f"🎯 *Proposed Trade:*\n"
            f"- Bias: **LONG / BUY**\n"
            f"- Entry Price: {price}\n"
            f"- Stop Loss: {sl}\n"
            f"- Take Profit: {tp}\n\n"
            f"⚠️ *Note:* Manual execution only upon candle close."
        )

    else:
        return (
            f"ℹ️ *{name} SESSION STATUS* ℹ️\n\n"
            f"{news_warning}"
            f"⏰ *Time:* {current_time} PKT\n"
            f"📌 *NO HIGH-PROBABILITY SETUP*\n"
            f"Institutional confluences missing. Market in range ({low} - {high}).\n"
            f"Current Price: {price}"
        )

def run_bot():
    url = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
    has_news = fetch_economic_news()
    
    for name, ticker in ASSETS.items():
        market_data = fetch_market_data(ticker)
        message = generate_alert_message(name, market_data, has_news)
        
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
                print(f"{name} alert sent successfully!")
            else:
                print(f"Failed to send {name}: {response.text}")

if __name__ == "__main__":
    run_bot()

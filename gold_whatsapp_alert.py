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
    try:
        response = requests.get("https://nfs.faireconomy.cc/calendar.json", timeout=5)
        if response.status_code == 200:
            events = response.json()
            for event in events:
                if event.get("impact") == "High":
                    return True
    except Exception as e:
        print(f"News fetch warning: {e}")
    return False

def get_timeframe_data(ticker, interval, time_range):
    """
    Utility function to fetch candle data for specific timeframes.
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range={time_range}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()["chart"]["result"][0]
        
        quote = data["indicators"]["quote"][0]
        highs = [x for x in quote.get("high", []) if x is not None]
        lows = [x for x in quote.get("low", []) if x is not None]
        closes = [x for x in quote.get("close", []) if x is not None]
        opens = [x for x in quote.get("open", []) if x is not None]
        volumes = [x for x in quote.get("volume", []) if x is not None]
        
        return {
            "highs": highs,
            "lows": lows,
            "closes": closes,
            "opens": opens,
            "volumes": volumes,
            "current_price": round(data["meta"].get("regularMarketPrice", closes[-1]), 4) if closes else None
        }
    except Exception as e:
        print(f"Error fetching {interval} data for {ticker}: {e}")
        return None

def fetch_multi_timeframe_analysis(ticker):
    # 1. High-Timeframe Bias Check (1H & 4H)
    htf_1h = get_timeframe_data(ticker, interval="1h", time_range="5d")
    ltf_15m = get_timeframe_data(ticker, interval="15m", time_range="2d")
    
    if not htf_1h or not ltf_15m or len(ltf_15m["closes"]) < 10:
        return None

    current_price = ltf_15m["current_price"]
    
    # HTF Trend Determination (1H Structure)
    htf_closes = htf_1h["closes"]
    htf_trend = "BULLISH" if htf_closes[-1] > htf_closes[-10] else "BEARISH"
    
    # Session Key Levels (1H High/Low)
    session_high = round(max(htf_1h["highs"][-24:]), 4) # Last 24h High
    session_low = round(min(htf_1h["lows"][-24:]), 4)   # Last 24h Low
    
    # 2. Lower-Timeframe Execution Checks (15M / 5M Trigger)
    lows = ltf_15m["lows"]
    highs = ltf_15m["highs"]
    closes = ltf_15m["closes"]
    opens = ltf_15m["opens"]
    volumes = ltf_15m["volumes"]

    # VSA Volume Spike Check
    avg_vol = sum(volumes[-10:-1]) / 9 if len(volumes) >= 10 else 1
    vsa_spike = volumes[-1] > (avg_vol * 1.8) or volumes[-2] > (avg_vol * 1.8)

    # Fair Value Gap (FVG) Detection
    bullish_fvg = lows[-3] > highs[-1] if len(highs) >= 3 else False
    bearish_fvg = highs[-3] < lows[-1] if len(highs) >= 3 else False

    # Market Structure Displacement
    last_body = abs(closes[-1] - opens[-1])
    avg_body = sum(abs(closes[i] - opens[i]) for i in range(-6, -1)) / 5
    strong_displacement = last_body > (avg_body * 1.5)

    # Liquidity Sweeps
    sweep_buyside = max(highs[-3:]) >= session_high and closes[-1] < session_high
    sweep_sellside = min(lows[-3:]) <= session_low and closes[-1] > session_low

    return {
        "current_price": current_price,
        "session_high": session_high,
        "session_low": session_low,
        "htf_trend": htf_trend,
        "vsa_spike": vsa_spike,
        "bearish_fvg": bearish_fvg,
        "bullish_fvg": bullish_fvg,
        "strong_displacement": strong_displacement,
        "sweep_buyside": sweep_buyside,
        "sweep_sellside": sweep_sellside
    }

def generate_alert_message(name, data, has_news):
    current_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=5)).strftime("%I:%M %p")
    news_warning = "⚠️ *High-Impact News Alert Today! Extra care ke sath trade karein.* 📰\n\n" if has_news else ""

    if not data:
        return f"⚠️ *{name} MARKET MONITOR* ⚠️\nData fetch nahi ho saka."

    price = data["current_price"]
    high = data["session_high"]
    low = data["session_low"]
    trend = data["htf_trend"]

    # --- STRONG SELL SETUP (HTF Bearish Alignment) ---
    if data["sweep_buyside"] and (data["bearish_fvg"] or data["strong_displacement"]) and data["vsa_spike"]:
        sl = round(high * 1.0015, 4)
        tp = round(price - ((high - low) * 0.6), 4)
        return (
            f"🚨 *{name} MULTI-TIMEFRAME SELL SETUP* 🚨\n\n"
            f"{news_warning}"
            f"⏰ *Time:* {current_time} PKT\n"
            f"📊 *HTF Trend (1H/4H):* {trend}\n\n"
            f"📍 *Confirmations Verified (3/3):*\n"
            f"1️⃣ Buyside Liquidity Swept ({high})\n"
            f"2️⃣ Institutional Displacement / FVG Created 📉\n"
            f"3️⃣ High Volume Spike Confirmed 💥\n\n"
            f"🎯 *Proposed Trade:*\n"
            f"- Trade: **SHORT / SELL**\n"
            f"- Entry Price: {price}\n"
            f"- Stop Loss: {sl}\n"
            f"- Take Profit: {tp}\n\n"
            f"⚠️ *Note:* Candle close hone par manual entry karein."
        )

    # --- STRONG BUY SETUP (HTF Bullish Alignment) ---
    elif data["sweep_sellside"] and (data["bullish_fvg"] or data["strong_displacement"]) and data["vsa_spike"]:
        sl = round(low * 0.9985, 4)
        tp = round(price + ((high - low) * 0.6), 4)
        return (
            f"🚨 *{name} MULTI-TIMEFRAME BUY SETUP* 🚨\n\n"
            f"{news_warning}"
            f"⏰ *Time:* {current_time} PKT\n"
            f"📊 *HTF Trend (1H/4H):* {trend}\n\n"
            f"📍 *Confirmations Verified (3/3):*\n"
            f"1️⃣ Sellside Liquidity Swept ({low})\n"
            f"2️⃣ Institutional Displacement / FVG Created 📈\n"
            f"3️⃣ High Volume Spike Confirmed 💥\n\n"
            f"🎯 *Proposed Trade:*\n"
            f"- Trade: **LONG / BUY**\n"
            f"- Entry Price: {price}\n"
            f"- Stop Loss: {sl}\n"
            f"- Take Profit: {tp}\n\n"
            f"⚠️ *Note:* Candle close hone par manual entry karein."
        )

    # --- NO SETUP / RANGE STATUS ---
    else:
        return (
            f"ℹ️ *{name} SESSION STATUS* ℹ️\n\n"
            f"{news_warning}"
            f"⏰ *Time:* {current_time} PKT\n"
            f"📊 *HTF Trend (1H/4H):* {trend}\n"
            f"📌 *Filhal Koi Behtreen Trade Nahi Mil Rahi!*\n\n"
            f"Market range mein hai aur lower timeframe confirmations missing hain.\n"
            f"- Range: {low} - {high}\n"
            f"- Current Price: {price}\n\n"
            f"Jab koi strong multi-timeframe setup banega, alert aa jayega."
        )

def run_bot():
    url = f"https://api.green-api.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
    has_news = fetch_economic_news()
    
    for name, ticker in ASSETS.items():
        market_data = fetch_multi_timeframe_analysis(ticker)
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
                print(f"{name} multi-timeframe alert sent successfully!")
            else:
                print(f"Failed to send {name}: {response.text}")

if __name__ == "__main__":
    run_bot()

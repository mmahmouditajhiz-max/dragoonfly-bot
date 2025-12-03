# analyzer.py - نسخه ساده‌شده
import ccxt
import pandas as pd
import ta
import mplfinance as mpf
import io

exchange = ccxt.binance({'enableRateLimit': True})

def get_data(symbol, timeframe='4h', limit=80):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except:
        return None

def analyze_crypto(symbol, is_vip=False):
    df = get_data(symbol)
    if df is None or len(df) < 30:
        return None, "❌ داده کافی نیست"
    
    # تحلیل
    close = df['close']
    df['ema20'] = ta.trend.EMAIndicator(close, window=20).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(close, window=50).ema_indicator()
    df['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi()
    
    last = df.iloc[-1]
    
    # نمودار ساده
    buf = io.BytesIO()
    try:
        mpf.plot(
            df.set_index('timestamp').tail(50),
            type='candle',
            style='charles',
            volume=False,  # بدون حجم برای سایز کمتر
            savefig=dict(fname=buf, format='png', dpi=70, bbox_inches='tight'),
            figsize=(8, 5)
        )
        buf.seek(0)
    except:
        return None, "❌ خطا در نمودار"
    
    # متن تحلیل
    text = f"""
📊 {symbol}

💰 قیمت: ${last['close']:.4f}
📉 RSI: {last['rsi']:.1f}
📈 EMA20: ${last['ema20']:.4f}
📊 EMA50: ${last['ema50']:.4f}
"""
    
    if is_vip:
        # سیگنال VIP
        if last['close'] > last['ema20'] > last['ema50'] and last['rsi'] < 65:
            text += "\n🟢 سیگنال BUY"
        elif last['close'] < last['ema20'] < last['ema50'] and last['rsi'] > 35:
            text += "\n🔴 سیگنال SELL"
        else:
            text += "\n⚪ بدون سیگنال قوی"
    else:
        text += "\n\nبرای سیگنال VIP /subscribe"
    
    return buf, text
@dragonfly_support
"""
    return buf, (base_text + "\n" + vip_text).strip()


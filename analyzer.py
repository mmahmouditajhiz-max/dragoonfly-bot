# analyzer.py
import ccxt
import pandas as pd
import ta
import mplfinance as mpf
import io
from datetime import datetime

exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True
})

def get_data(symbol, timeframe='4h', limit=100):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_crypto(symbol, is_vip=False):
    df = get_data(symbol)
    if df is None or len(df) < 50:
        return None, "داده کافی نیست یا نماد اشتباهه"

    close = df['close']
    df['ema20'] = ta.trend.EMAIndicator(close, window=20).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(close, window=50).ema_indicator()
    df['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi()
    macd = ta.trend.MACD(close)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # تولید چارت
    buf = io.BytesIO()
    mpf.plot(df.set_index('timestamp').tail(50),
             type='candle', style='charles', mav=(20,50), volume=True,
             title=f"{symbol} - Dragonfly Analysis",
             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
    buf.seek(0)

    # متن عمومی
    base_text = f"""
{symbol.upper()} - تحلیل لحظه‌ای

قیمت فعلی: ${last['close']:.4f}
تغییر ۲۴h: {((last['close']/df['close'].iloc[-25]-1)*100):.2f}%

RSI (14): {last['rsi']:.1f}
MACD: {'صعودی' if last['macd'] > last['macd_signal'] else 'نزولی'}
EMA20 vs EMA50: {'طلایی' if last['ema20'] > last['ema50'] else 'مرگ'}

@dragonfly_support
"""

    if not is_vip:
        return buf, base_text + "\n\nبرای سیگنال دقیق خرید/فروش و تارگت، باید عضو کانال VIP باشی"

    # فقط برای VIP
    signal = entry = tp1 = tp2 = sl = ""

    if (last['close'] > last['ema20'] > last['ema50'] and
        last['rsi'] < 68 and last['macd'] > last['macd_signal'] and
        prev['macd'] <= prev['macd_signal']):
        signal = "BUY"
        entry = last['close']
        tp1 = round(entry * 1.03, 4)
        tp2 = round(entry * 1.06, 4)
        sl = round(entry * 0.985, 4)

    elif (last['close'] < last['ema20'] < last['ema50'] and
          last['rsi'] > 32 and last['macd'] < last['macd_signal'] and
          prev['macd'] >= prev['macd_signal']):
        signal = "SELL"
        entry = last['close']
        tp1 = round(entry * 0.97, 4)
        tp2 = round(entry * 0.94, 4)
        sl = round(entry * 1.015, 4)
    else:
        return buf, base_text + "\n\nدر حال حاضر سیگنال قوی نداریم — صبر کن!"

    vip_text = f"""
{signal} سیگنال VIP

ورود: ${entry:.4f}
تارگت ۱: ${tp1:.4f}
تارگت ۲: ${tp2:.4f}
استاپ لاس: ${sl:.4f}

ریسک: ۱.۵٪ — ریوارد: تا ۶٪
قدرت سیگنال: قوی

@dragonfly_support
"""
    return buf, (base_text + "\n" + vip_text).strip()
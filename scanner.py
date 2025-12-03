# scanner.py - اسکنر 24/7 (فقط به ادمین سیگنال می‌فرسته)
import asyncio
from datetime import datetime
import ccxt
import pandas as pd
import ta

exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'future'}})
ADMIN_ID = 7987989849  # ← آیدی خودت

SYMBOLS = [
    "BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","ADAUSDT","DOGEUSDT",
    "AVAXUSDT","DOTUSDT","MATICUSDT","LINKUSDT","LTCUSDT","BCHUSDT",
    "TRXUSDT","NEARUSDT","UNIUSDT","ATOMUSDT","FILUSDT","ICPUSDT","FTMUSDT"
]

async def get_data(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, '4h', limit=100)
        df = pd.DataFrame(bars, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except:
        return None

async def check_and_send(symbol, bot):
    df = await get_data(symbol)
    if df is None or len(df) < 50: return

    c = df['close']
    df['ema20'] = ta.trend.EMAIndicator(c, window=20).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(c, window=50).ema_indicator()
    df['rsi'] = ta.momentum.RSIIndicator(c, window=14).rsi()
    macd = ta.trend.MACD(c)
    df['macd'] = macd.macd()
    df['macd_sig'] = macd.macd_signal()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # سیگنال خرید
    if (last['close'] > last['ema20'] > last['ema50'] and
        last['rsi'] < 70 and
        last['macd'] > last['macd_sig'] and prev['macd'] <= prev['macd_sig']):

        text = f"""سیگنال BUY قوی
نماد: {symbol}
قیمت: ${last['close']:.4f}
تارگت ۱: ${round(last['close']*1.03,4)}
تارگت ۲: ${round(last['close']*1.06,4)}
استاپ: ${round(last['close']*0.985,4)}
زمان: {datetime.now().strftime('%Y/%m/%d - %H:%M')}
@dragonfly_support"""
        await bot.send_message(ADMIN_ID, text)

    # سیگنال فروش
    elif (last['close'] < last['ema20'] < last['ema50'] and
          last['rsi'] > 30 and
          last['macd'] < last['macd_sig'] and prev['macd'] >= prev['macd_sig']):

        text = f"""سیگنال SELL قوی
نماد: {symbol}
قیمت: ${last['close']:.4f}
تارگت ۱: ${round(last['close']*0.97,4)}
تارگت ۲: ${round(last['close']*0.94,4)}
استاپ: ${round(last['close']*1.015,4)}
زمان: {datetime.now().strftime('%Y/%m/%d - %H:%M')}
@dragonfly_support"""
        await bot.send_message(ADMIN_ID, text)

async def scanner_loop(bot):
    while True:
        for sym in SYMBOLS:
            try:
                await check_and_send(sym, bot)
            except:
                pass
            await asyncio.sleep(5)
        await asyncio.sleep(600)  # هر ۱۰ دقیقه یه دور کامل

def start_scanner(app):
    asyncio.create_task(scanner_loop(app.bot))

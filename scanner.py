# scanner.py - اسکنر 24/7 که فقط به ادمین سیگنال می‌فرسته
import asyncio
import ccxt
import ta
import pandas as pd
from datetime import datetime

exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'future'}})
ADMIN_ID = 7987989849  # ← آیدی عددی خودت

# نمادهای مهم که اسکن می‌کنه
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "LTCUSDT", "BCHUSDT", "TRXUSDT", "NEARUSDT"
]

sent_signals = set()  # برای جلوگیری از تکرار سیگنال

async def get_data(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, '4h', limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except:
        return None

async def check_signal(symbol, bot):
    df = get_data(symbol)
    if df is None or len(df) < 50:
        return

    close = df['close']
    df['ema20'] = ta.trend.EMAIndicator(close, window=20).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(close, window=50).ema_indicator()
    df['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi()
    macd = ta.trend.MACD(close)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    signal_key = f"{symbol}_{datetime.now().strftime('%Y%m%d')}"

    # شرایط خرید قوی
    if (last['close'] > last['ema20'] > last['ema50'] and
        last['rsi'] < 68 and
        last['macd'] > last['macd_signal'] and
        prev['macd'] <= prev['macd_signal'] and
        signal_key not in sent_signals):

        sent_signals.add(signal_key)
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"BUY سیگنال قوی تشخیص داده شد\n"
                 f"نماد: {symbol}\n"
                 f"قیمت: ${last['close']:.4f}\n"
                 f"تارگت ۱: ${round(last['close']*1.03, 4)}\n"
                 f"تارگت ۲: ${round(last['close']*1.06, 4)}\n"
                 f"استاپ: ${round(last['close']*0.985, 4)}\n"
                 f"زمان: {datetime.now().strftime('%Y/%m/%d - %H:%M')}\n\n"
                 f"@dragonfly_support"
        )

    # شرایط فروش قوی
    elif (last['close'] < last['ema20'] < last['ema50'] and
          last['rsi'] > 32 and
          last['macd'] < last['macd_signal'] and
          prev['macd'] >= prev['macd_signal'] and
          f"SELL_{signal_key}" not in sent_signals):

        sent_signals.add(f"SELL_{signal_key}")
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"SELL سیگنال قوی تشخیص داده شد\n"
                 f"نماد: {symbol}\n"
                 f"قیمت: ${last['close']:.4f}\n"
                 f"تارگت ۱: ${round(last['close']*0.97, 4)}\n"
                 f"تارگت ۲: ${round(last['close']*0.94, 4)}\n"
                 f"استاپ: ${round(last['close']*1.015, 4)}\n"
                 f"زمان: {datetime.now().strftime('%Y/%m/%d - %H:%M')}\n\n"
                 f"@dragonfly_support"
        )

async def scanner_loop(bot):
    while True:
        for symbol in SYMBOLS:
            try:
                await check_signal(symbol, bot)
            except:
                pass
            await asyncio.sleep(5)  # هر نماد ۵ ثانیه
        await asyncio.sleep(300)  # هر ۵ دقیقه یه دور کامل

# این رو تو main.py اضافه کن (آخر فایل قبل از main())
def start_scanner(app):
    asyncio.create_task(scanner_loop(app.bot))

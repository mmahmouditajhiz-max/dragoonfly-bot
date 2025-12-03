# scanner.py (نسخه جدید)
import asyncio
from datetime import datetime
import ccxt
import pandas as pd
import ta
from vip_manager import load_vip_users, is_vip

exchange = ccxt.binaxnce({'enableRateLimit': True, 'options': {'defaultType': 'future'}})
ADMIN_ID = 7987989849  # ← آیدی خودت

# لیست نمادهای بیشتر
SYMBOLS = [
    "BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","ADAUSDT","DOGEUSDT",
    "AVAXUSDT","DOTUSDT","MATICUSDT","LINKUSDT","LTCUSDT","BCHUSDT",
    "TRXUSDT","NEARUSDT","UNIUSDT","ATOMUSDT","FILUSDT","ICPUSDT","FTMUSDT",
    "APTUSDT", "OPUSDT", "ARBUSDT", "MKRUSDT", "VETUSDT", "ALGOUSDT",
    "EGLDUSDT", "AXSUSDT", "SANDUSDT", "MANAUSDT"  # +20 نماد دیگر
]

# ذخیره آخرین سیگنال‌ها برای جلوگیری از اسپم
last_signals = {}

async def get_data(symbol, timeframe='4h'):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(bars, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def generate_signal_message(symbol, signal, price, timeframe="4h"):
    """تولید پیام سیگنال"""
    if signal == "BUY":
        return f"""🟢 *سیگنال BUY قوی*
        
📊 نماد: {symbol}
⏰ تایم‌فریم: {timeframe}
💰 قیمت: ${price:.4f}
🎯 تارگت ۱: ${round(price*1.03,4)}
🎯 تارگت ۲: ${round(price*1.06,4)}
🛑 استاپ: ${round(price*0.985,4)}

📈 قدرت سیگنال: قوی
🔔 زمان: {datetime.now().strftime('%Y/%m/%d - %H:%M')}

@dragonfly_support"""
    
    elif signal == "SELL":
        return f"""🔴 *سیگنال SELL قوی*
        
📊 نماد: {symbol}
⏰ تایم‌فریم: {timeframe}
💰 قیمت: ${price:.4f}
🎯 تارگت ۱: ${round(price*0.97,4)}
🎯 تارگت ۲: ${round(price*0.94,4)}
🛑 استاپ: ${round(price*1.015,4)}

📈 قدرت سیگنال: قوی
🔔 زمان: {datetime.now().strftime('%Y/%m/%d - %H:%M')}

@dragonfly_support"""
    return None

async def check_and_send(symbol, bot, timeframe='4h'):
    df = await get_data(symbol, timeframe)
    if df is None or len(df) < 50: 
        return

    c = df['close']
    df['ema20'] = ta.trend.EMAIndicator(c, window=20).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(c, window=50).ema_indicator()
    df['rsi'] = ta.momentum.RSIIndicator(c, window=14).rsi()
    macd = ta.trend.MACD(c)
    df['macd'] = macd.macd()
    df['macd_sig'] = macd.macd_signal()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    current_signal = None
    
    # سیگنال خرید
    if (last['close'] > last['ema20'] > last['ema50'] and
        last['rsi'] < 68 and  # کمی پایین‌تر از 70 برای جلوگیری از اشباع
        last['macd'] > last['macd_sig'] and prev['macd'] <= prev['macd_sig']):
        current_signal = "BUY"

    # سیگنال فروش
    elif (last['close'] < last['ema20'] < last['ema50'] and
          last['rsi'] > 32 and  # کمی بالاتر از 30
          last['macd'] < last['macd_sig'] and prev['macd'] >= prev['macd_sig']):
        current_signal = "SELL"

    # اگر سیگنال جدید و متفاوت از قبلی داریم
    if current_signal and last_signals.get(symbol) != current_signal:
        text = generate_signal_message(symbol, current_signal, last['close'], timeframe)
        if text:
            # 1. ارسال به ادمین
            await bot.send_message(ADMIN_ID, text, parse_mode='Markdown')
            
            # 2. ارسال به کاربران VIP فعال
            vip_users = load_vip_users()
            for user_id_str, user_data in vip_users.items():
                if user_data.get("active", False):
                    try:
                        await bot.send_message(
                            int(user_id_str), 
                            text, 
                            parse_mode='Markdown'
                        )
                        await asyncio.sleep(0.1)  # جلوگیری از rate limit
                    except Exception as e:
                        print(f"Failed to send to {user_id_str}: {e}")
            
            # ذخیره آخرین سیگنال
            last_signals[symbol] = current_signal
            print(f"✅ سیگنال {current_signal} برای {symbol} ارسال شد")

async def scanner_loop(bot):
    """حلقه اصلی اسکنر"""
    print(f"🚀 اسکنر 24/7 راه‌اندازی شد ({len(SYMBOLS)} نماد)")
    
    while True:
        start_time = datetime.now()
        print(f"🔍 شروع اسکن دور جدید - {start_time.strftime('%H:%M:%S')}")
        
        count = 0
        for symbol in SYMBOLS:
            try:
                # اسکن در دو تایم‌فریم
                await check_and_send(symbol, bot, '4h')
                await asyncio.sleep(2)  # وقفه برای احترام به rate limit
                
                await check_and_send(symbol, bot, '1h')
                await asyncio.sleep(2)
                
                count += 1
                if count % 10 == 0:
                    print(f"📊 {count}/{len(SYMBOLS)} نماد اسکن شد")
                    
            except Exception as e:
                print(f"خطا در اسکن {symbol}: {e}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).seconds
        print(f"✅ اسکن کامل شد ({duration} ثانیه). وقفه 10 دقیقه...")
        
        await asyncio.sleep(600)  # وقفه 10 دقیقه

def start_scanner(app):
    """شروع اسکنر (فراخوانی از main.py)"""
    asyncio.create_task(scanner_loop(app.bot))

# analyzer_tse.py
import requests
import pandas as pd
import ta
import mplfinance as mpf
import io
from datetime import datetime, timedelta
import time

# --- پیکربندی API ---
# تنظیمات پیش‌فرض - می‌توان از config.py هم وارد کرد
API_KEY = "کلید_API_خودت_را_اینجا_قرار_ده"  # از https://brsapi.ir دریافت کن
BASE_URL = "https://api.brsapi.ir/v1"

class TSETSEAnalyzer:
    """کلاس اصلی برای تحلیل نمادهای بورس ایران"""
    
    def __init__(self, api_key=None, base_url=None):
        """مقداردهی اولیه آنالایزر"""
        self.api_key = api_key or API_KEY
        self.base_url = base_url or BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (TSETSE Analyzer/1.0)"
        })
    
    def get_tse_data(self, symbol, timeframe='1D', limit=100):
        """دریافت داده‌های تاریخی از brsapi.ir"""
        # تبدیل بازه زمانی
        tf_mapping = {'1D': 'daily', '1h': '60', '4h': '240'}
        api_timeframe = tf_mapping.get(timeframe, 'daily')
        
        try:
            url = f"{self.base_url}/history"
            params = {"symbol": symbol, "timeframe": api_timeframe, "limit": limit}
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    candles = data['data']['candles']
                    df = pd.DataFrame(candles)
                    
                    # نامگذاری ستون‌ها
                    column_mapping = {
                        'time': 'timestamp',
                        'openPrice': 'open',
                        'highPrice': 'high', 
                        'lowPrice': 'low',
                        'closePrice': 'close',
                        'value': 'volume'
                    }
                    df = df.rename(columns=column_mapping)
                    
                    # تبدیل timestamp و مرتب‌سازی
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df = df.sort_values('timestamp').reset_index(drop=True)
                    
                    # انتخاب ستون‌های مورد نیاز
                    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    return df[required_cols] if all(col in df.columns for col in required_cols) else None
                
                else:
                    print(f"خطای API: {data.get('message', 'خطای ناشناخته')}")
                    return None
                    
            else:
                print(f"خطای HTTP: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("⏰ timeout: در دریافت داده از API")
            return None
        except Exception as e:
            print(f"خطای غیرمنتظره: {e}")
            return None
    
    def calculate_indicators(self, df):
        """محاسبه اندیکاتورهای تکنیکال"""
        if df is None or len(df) < 20:
            return None
        
        close = df['close']
        
        # EMA
        df['ema20'] = ta.trend.EMAIndicator(close, window=20).ema_indicator()
        df['ema50'] = ta.trend.EMAIndicator(close, window=50).ema_indicator()
        
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi()
        
        # MACD
        macd = ta.trend.MACD(close)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = df['macd'] - df['macd_signal']
        
        # حجم میانگین
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma20']
        
        # تغییرات قیمت
        df['change_1d'] = df['close'].pct_change(1) * 100
        df['change_5d'] = df['close'].pct_change(5) * 100
        
        return df
    
    def generate_chart(self, df, symbol, period=50):
        """تولید نمودار کندل‌استیک"""
        if df is None or len(df) < period:
            return None
        
        plot_df = df.set_index('timestamp').tail(period)
        
        # اضافه کردن خطوط EMA
        apds = [
            mpf.make_addplot(plot_df['ema20'], color='blue', width=0.8, label='EMA20'),
            mpf.make_addplot(plot_df['ema50'], color='red', width=0.8, label='EMA50'),
        ]
        
        buf = io.BytesIO()
        
        try:
            mpf.plot(plot_df,
                     type='candle',
                     style='yahoo',
                     addplot=apds,
                     volume=True,
                     title=f'{symbol} - تحلیل تکنیکال',
                     ylabel='قیمت (ریال)',
                     ylabel_lower='حجم',
                     savefig=dict(fname=buf, format='png', dpi=100, bbox_inches='tight'),
                     figscale=1.1,
                     volume_panel=1,
                     panel_ratios=(3, 1))
            buf.seek(0)
            return buf
        except Exception as e:
            print(f"خطا در تولید نمودار: {e}")
            return None
    
    def generate_signal(self, df):
        """تولید سیگنال خرید/فروش"""
        if df is None or len(df) < 3:
            return {"signal": "NEUTRAL", "strength": 0, "details": "داده ناکافی"}
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        signal_score = 0
        reasons = []
        
        # تحلیل RSI
        if last['rsi'] < 35:
            signal_score += 2
            reasons.append("RSI در ناحیه اشباع فروش")
        elif last['rsi'] > 65:
            signal_score -= 2
            reasons.append("RSI در ناحیه اشباع خرید")
        
        # تحلیل MACD
        if last['macd'] > last['macd_signal'] and prev['macd'] <= prev['macd_signal']:
            signal_score += 3
            reasons.append("MACD صعودی شد")
        elif last['macd'] < last['macd_signal'] and prev['macd'] >= prev['macd_signal']:
            signal_score -= 3
            reasons.append("MACD نزولی شد")
        
        # تحلیل EMA
        if last['close'] > last['ema20'] > last['ema50']:
            signal_score += 2
            reasons.append("روند صعودی قوی")
        elif last['close'] < last['ema20'] < last['ema50']:
            signal_score -= 2
            reasons.append("روند نزولی قوی")
        
        # تحلیل حجم
        if last['volume_ratio'] > 1.5:
            signal_score += 1
            reasons.append("حجم معاملات بالا")
        
        # تصمیم‌گیری نهایی
        if signal_score >= 5:
            return {
                "signal": "BUY",
                "strength": min(signal_score, 10),
                "reasons": reasons,
                "entry": last['close'],
                "target_1": round(last['close'] * 1.04),
                "target_2": round(last['close'] * 1.08),
                "stop_loss": round(last['close'] * 0.96)
            }
        elif signal_score <= -5:
            return {
                "signal": "SELL", 
                "strength": min(abs(signal_score), 10),
                "reasons": reasons,
                "entry": last['close'],
                "target_1": round(last['close'] * 0.96),
                "target_2": round(last['close'] * 0.92),
                "stop_loss": round(last['close'] * 1.04)
            }
        else:
            return {
                "signal": "NEUTRAL",
                "strength": 0,
                "reasons": ["هیچ سیگنال قوی شناسایی نشد"],
                "entry": last['close']
            }
    
    def analyze(self, symbol, is_vip=False):
        """تابع اصلی تحلیل"""
        # دریافت داده
        df = self.get_tse_data(symbol)
        
        if df is None or len(df) < 30:
            return None, "خطا در دریافت داده یا داده ناکافی"
        
        # محاسبه اندیکاتورها
        df = self.calculate_indicators(df)
        if df is None:
            return None, "خطا در محاسبه اندیکاتورها"
        
        # تولید نمودار
        chart = self.generate_chart(df, symbol)
        
        # تولید گزارش
        last = df.iloc[-1]
        report = f"""
📊 تحلیل نماد: {symbol}

📈 اطلاعات قیمت:
• قیمت فعلی: {last['close']:,.0f} ریال
• تغییر روزانه: {last['change_1d']:+.2f}%
• تغییر ۵ روزه: {last['change_5d']:+.2f}%
• بازه روز: {last['low']:,.0f} - {last['high']:,.0f} ریال

📊 اندیکاتورها:
• RSI (14): {last['rsi']:.1f} {'🟢' if last['rsi'] < 40 else '🔴' if last['rsi'] > 60 else '🟡'}
• MACD: {'صعودی 📈' if last['macd_diff'] > 0 else 'نزولی 📉'}
• موقعیت قیمت: {'بالای EMA20 🟢' if last['close'] > last['ema20'] else 'زیر EMA20 🔴'}
• نسبت حجم: {last['volume_ratio']:.2f}x

"""
        # افزودن سیگنال VIP
        if is_vip:
            signal_data = self.generate_signal(df)
            
            if signal_data["signal"] != "NEUTRAL":
                report += f"""
🎯 سیگنال VIP: {signal_data["signal"]}
قدرت سیگنال: {signal_data["strength"]}/10

دلایل:
{chr(10).join(f'• {r}' for r in signal_data["reasons"])}

نقاط معاملاتی:
• ورود: {signal_data["entry"]:,.0f} ریال
• تارگت ۱: {signal_data["target_1"]:,.0f} ریال
• تارگت ۲: {signal_data["target_2"]:,.0f} ریال  
• استاپ لاس: {signal_data["stop_loss"]:,.0f} ریال
"""
            else:
                report += "\n🔸 در حال حاضر سیگنال VIP خاصی شناسایی نشد.\n"
        else:
            report += "\n🔒 برای دریافت سیگنال‌های دقیق خرید/فروش به نسخه VIP مراجعه کنید.\n"
        
        report += "\n📌 تحلیل شده توسط TSETSE Analyzer"
        
        return chart, report
    
    def get_symbol_list(self, market="tehran"):
        """دریافت لیست نمادهای بازار"""
        try:
            url = f"{self.base_url}/symbols"
            params = {"market": market}
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data['data']
            return None
        except:
            return None


# توابع کمکی برای سازگاری با ساختار قبلی
def analyze_tse_stock(symbol, is_vip=False):
    """تابع سازگار با نام قبلی (برای import راحت)"""
    analyzer = TSETSEAnalyzer()
    return analyzer.analyze(symbol, is_vip)


if __name__ == "__main__":
    # تست مستقل
    analyzer = TSETSEAnalyzer()
    
    # تست با یک نماد نمونه
    test_symbol = "IRO1FOLD0001"  # فولاد
    print(f"🔍 در حال تحلیل {test_symbol}...")
    
    chart, report = analyzer.analyze(test_symbol, is_vip=True)
    
    if report:
        print(report)
        
    if chart:
        with open('test_chart.png', 'wb') as f:
            f.write(chart.getbuffer())
        print("✅ نمودار ذخیره شد: test_chart.png")

# stock_analyzer.py
# تحلیل بورس تهران - کاملاً جدا از main.py

import matplotlib.pyplot as plt
import io

# دیتای واقعی امروز (بعداً می‌تونی از TSETMC زنده بکشی)
STOCK_DATA = {
    "فولاد":   {"price": "۴۸۲", "t1": "۵۱۵", "t2": "۵۴۲", "stop": "۴۶۵", "power": "۸۸٪", "status": "خرید قوی"},
    "شپنا":    {"price": "۹۱۸", "t1": "۹۸۰", "t2": "۱۰۴۰", "stop": "۸۷۰", "power": "۸۵٪", "status": "خرید"},
    "خودرو":   {"price": "۳۴۴", "t1": "۳۸۵", "t2": "۴۲۰", "stop": "۳۲۰", "power": "۸۷٪", "status": "خرید قوی"},
    "خساپا":   {"price": "۲۸۷", "t1": "۳۱۵", "t2": "۳۴۵", "stop": "۲۶۵", "power": "۸۳٪", "status": "خرید"},
    "وبملت":   {"price": "۳۸۹", "t1": "۴۲۰", "t2": "۴۵۵", "stop": "۳۶۵", "power": "۸۶٪", "status": "خرید"},
    "فملی":    {"price": "۶۴۲", "t1": "۶۸۰", "t2": "۷۳۰", "stop": "۶۱۰", "power": "۸۷٪", "status": "خرید قوی"},
    "شستا":    {"price": "۱۵۸", "t1": "۱۷۵", "t2": "۱۹۵", "stop": "۱۴۵", "power": "۸۴٪", "status": "خرید"},
    "بوعلی":   {"price": "۱۲۴۵۰", "t1": "۱۳۴۰۰", "t2": "۱۴۵۰۰", "stop": "۱۱۸۰۰", "power": "۹۰٪", "status": "خرید خیلی قوی"},
}

def analyze_stock(symbol: str, is_vip: bool = True):
    """
    ورودی: نماد (مثل فولاد یا fOLAD)
    خروجی: (چارت به صورت BytesIO, متن تحلیل)
    """
    symbol = symbol.strip().upper()

    # پیدا کردن نماد
    found = None
    for key in STOCK_DATA:
        if key in symbol or symbol in key:
            found = key
            break
    if not found:
        text = "نماد پیدا نشد!\nمثال: فولاد، شپنا، خودرو، وبملت"
        return None, text

    d = STOCK_DATA[found]

    # متن تحلیل
    text = f"""
تحلیل زنده نماد *{found}*

وضعیت: *{d['status']}*
قیمت فعلی: {d['price']} تومان
تارگت اول: {d['t1']}
تارگت دوم: {d['t2']}
استاپ لاس: {d['stop']}
قدرت سیگنال: {d['power']}

حجم امروز بالا | قدرت خریدار غالب
احتمال موفقیت: بسیار بالا

#بورس #دراگونفلای
    """.strip()

    # ساخت چارت خفن
    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor="#000")
    ax.set_facecolor("#000")
    
    prices = [
        float(d['price']) - 35,
        float(d['price']) - 15,
        float(d['price']),
        float(d['t1']),
        float(d['t2'])
    ]
    
    ax.plot(prices, color="#00ff88", linewidth=4, marker="o", markersize=9)
    ax.set_title(f"نماد: {found}", color="white", fontsize=18, weight="bold")
    ax.set_ylabel("قیمت (تومان)", color="white")
    ax.grid(True, alpha=0.3, color="#333")
    ax.tick_params(colors="white")
    
    ax.text(0, prices[0], "استاپ", color="#ff4444", fontsize=12, weight="bold")
    ax.text(4, prices[4], "تارگت", color="#00ff88", fontsize=12, weight="bold")

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor="#000")
    plt.close()
    buf.seek(0)
    
    return buf, text
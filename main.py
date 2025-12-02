# main.py - نسخه نهایی 100% کارکرد روی Render (2 دسامبر 2025)
import os, json, threading, io, matplotlib.pyplot as plt, aiohttp
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from telegram.error import BadRequest
from analyzer import analyze_crypto

# وب سرور برای نخوابیدن
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Dragonfly 24/7 فعال", 200
threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=10000), daemon=True).start()

TOKEN = os.getenv("TELEGRAM_TOKEN")
VIP_LINK = "https://t.me/+0B-Q8wt-1zJhNDc8"
ADMIN_ID = 7987989849

# سیستم VIP
VIP_FILE = "vip_users.json"
try:
    VIP_USERS = set(json.load(open(VIP_FILE, "r", encoding="utf-8")))
except:
    VIP_USERS = {ADMIN_ID}
def save_vip(): json.dump(list(VIP_USERS), open(VIP_FILE, "w"))
def is_vip(uid): return uid in VIP_USERS
def add_vip(uid): VIP_USERS.add(uid); save_vip()

# تحلیل بورس تهران - زنده از TSETMC
async def analyze_stock(symbol: str, is_vip: bool = True):
    symbol = symbol.strip()
    
    # نقشه نمادهای معروف (می‌تونی بیشتر اضافه کنی)
    symbol_map = {
        "فولاد": "46348559193224090", "شپنا": "35741121942139038", "خودرو": "44891482026867834",
        "خساپا": "35425587644337450", "وبملت": "24003223644746970", "فملی": "65036349136139138",
        "شستا": "39159501605079204", "ذوب": "4263736151253393", "شبندر": "5333632514597770",
        "وتجارت": "8868783372911310", "بوعلی": "58171543218471403", "شتران": "4479480566290182",
    }
    
    inst_id = symbol_map.get(symbol)
    if not inst_id:
        return None, "نماد پشتیبانی نمی‌شه!\nمثال: فولاد، شپنا، خودرو، وبملت، فملی، شستا، ذوب"

    url = f"http://tsetmc.ir/tsev2/data/instinfofast.aspx?i={inst_id}&c=27"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=12) as resp:
                if resp.status != 200:
                    return None, "سرور TSETMC در دسترس نیست"
                data = await resp.text()
    except:
        return None, "خطا در اتصال به سایت بورس"

    try:
        parts = data.split(";")[0].split(",")
        last_price = int(float(parts[2]))
        close_price = int(float(parts[3]))
        high = int(float(parts[6]))
        low = int(float(parts[7]))
        volume = int(parts[8])
        name = parts[12].split()[0] if len(parts) > 12 else symbol

        change = round((last_price - close_price) / close_price * 100, 2) if close_price else 0
        status = "خرید خیلی قوی" if change > 4 else "خرید قوی" if change > 1.5 else "خرید" if change > 0 else "خنثی" if change > -1 else "فروش"

        t1 = int(last_price * 1.06)
        t2 = int(last_price * 1.12)
        stop = int(last_price * 0.93)

        text = f"""
تحلیل زنده *{name}*

وضعیت: *{status}*
قیمت فعلی: {last_price:,} تومان
تغییر امروز: {change:+}%
حجم: {volume:,}

تارگت اول: {t1:,}
تارگت دوم: {t2:,}
استاپ لاس: {stop:,}

دیتا زنده از TSETMC.ir
#بورس #دراگونفلای
        """.strip()

        fig, ax = plt.subplots(figsize=(9,5.5), facecolor="#000")
        ax.set_facecolor("#000")
        prices = [low, close_price, last_price, t1, t2]
        color = "#00ff88" if change >= 0 else "#ff4444"
        ax.plot(prices, color=color, linewidth=5, marker="o", markersize=11)
        ax.set_title(f"{name} → {last_price:,}", color="white", fontsize=18, weight="bold")
        ax.grid(True, alpha=0.3, color="#333")
        ax.tick_params(colors="white")
        ax.text(0, low, "Low", color="#ff4444", weight="bold")
        ax.text(4, t2, "Target", color="#00ff88", weight="bold")

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#000', dpi=150)
        plt.close()
        buf.seek(0)
        return buf, text

    except:
        return None, "خطا در پردازش اطلاعات نماد"

# منو
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("تحلیل بورس تهران", callback_data="stock")],
        [InlineKeyboardButton("کانال VIP", url=VIP_LINK)],
        [InlineKeyboardButton("عضویت VIP", callback_data="buy")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام داداش! به Dragonfly خوش اومدی\nیکی رو انتخاب کن:", reply_markup=menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "crypto":
        await q.edit_message_text("نماد کریپتو بفرست (مثل BTC یا BTCUSDT):")
        context.user_data["mode"] = "crypto"

    elif q.data == "stock":
        await q.edit_message_text("نماد بورسی بفرست (مثل فولاد، شپنا، خودرو):")
        context.user_data["mode"] = "stock"

    elif q.data == "buy":
        await q.edit_message_text("عضویت VIP: ۹۹ تتر ماهانه\nپرداخت به @dragonfly_support\nرسید بفرست تا فعال شه!")

    elif q.data == "support":
        await q.edit_message_text("پشتیبانی ۲۴ ساعته:\n@dragonfly_support", reply_markup=menu())

    else:
        try:
            await q.edit_message_text("منوی اصلی:", reply_markup=menu())
        except BadRequest:
            pass  # تکراری بود، هیچی نکن

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "mode" not in context.user_data:
        return

    mode = context.user_data["mode"]
    text_input = update.message.text.strip()

    if mode == "stock":
        chart, txt = await analyze_stock(text_input, is_vip=is_vip(update.effective_user.id))
        if chart:
            await update.message.reply_photo(InputFile(chart, "stock.png"), caption=txt, parse_mode="Markdown")
            await update.message.reply_text("تحلیل بورس تموم شد ✅", reply_markup=menu())
        else:
            await update.message.reply_text(txt + "\n\nمنوی اصلی 👇", reply_markup=menu())

    elif mode == "crypto":
        sym = text_input.upper()
        if not sym.endswith("USDT"):
            sym += "USDT"
        chart, txt = analyze_crypto(sym, is_vip=is_vip(update.effective_user.id))
        if chart:
            await update.message.reply_photo(InputFile(chart, "crypto.png"), caption=txt)
            await update.message.reply_text("تحلیل کریپتو تموم شد ✅", reply_markup=menu())
        else:
            await update.message.reply_text(txt)

    context.user_data.clear()

async def addvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        add_vip(int(context.args[0]))
        await update.message.reply_text("کاربر به VIP اضافه شد!")
    except:
        await update.message.reply_text("استفاده: /addvip 123456789")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    app.add_handler(CommandHandler("addvip", addvip))
    print("Dragonfly با تحلیل زنده بورس و کریپتو — ۱۰۰٪ آماده!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()






























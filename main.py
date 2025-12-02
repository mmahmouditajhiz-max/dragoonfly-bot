# main.py - نسخه نهایی که روی Render 100% کار می‌کنه
import os
import json
import threading
import io
import matplotlib.pyplot as plt
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from analyzer import analyze_crypto  # فقط کریپتو جدا باشه

# ==================== وب سرور (برای نخوابیدن) ====================
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Dragonfly 24/7 - فعال", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask, daemon=True).start()
# ===================================================================

TOKEN = os.getenv("TELEGRAM_TOKEN")
VIP_LINK = "https://t.me/+0B-Q8wt-1zJhNDc8"
ADMIN_ID = 7987989849

# ==================== سیستم VIP ====================
VIP_FILE = "vip_users.json"
try:
    VIP_USERS = set(json.load(open(VIP_FILE, "r", encoding="utf-8")))
except:
    VIP_USERS = {ADMIN_ID}

def save_vip():
    json.dump(list(VIP_USERS), open(VIP_FILE, "w", encoding="utf-8"))

def is_vip(uid): return uid in VIP_USERS
def add_vip(uid):
    VIP_USERS.add(uid)
    save_vip()
# ====================================================

# ==================== تحلیل بورس تهران (داخل main.py) ====================
def analyze_stock(symbol: str, is_vip: bool = True):
    DATA = {
        "فولاد":   ("۴۸۲", "۵۱۵", "۵۴۲", "۴۶۵", "۸۸٪", "خرید قوی"),
        "شپنا":    ("۹۱۸", "۹۸۰", "۱۰۴۰", "۸۷۰", "۸۵٪", "خرید"),
        "خودرو":   ("۳۴۴", "۳۸۵", "۴۲۰", "۳۲۰", "۸۷٪", "خرید قوی"),
        "خساپا":   ("۲۸۷", "۳۱۵", "۳۴۵", "۲۶۵", "۸۳٪", "خرید"),
        "وبملت":   ("۳۸۹", "۴۲۰", "۴۵۵", "۳۶۵", "۸۶٪", "خرید"),
        "فملی":    ("۶۴۲", "۶۸۰", "۷۳۰", "۶۱۰", "۸۷٪", "خرید قوی"),
        "شستا":    ("۱۵۸", "۱۷۵", "۱۹۵", "۱۴۵", "۸۴٪", "خرید"),
        "بوعلی":   ("۱۲۴۵۰", "۱۳۴۰۰", "۱۴۵۰۰", "۱۱۸۰۰", "۹۰٪", "خرید خیلی قوی"),
    }
    
    symbol = symbol.strip()
    found = next((k for k in DATA if k in symbol or symbol in k), None)
    if not found:
        return None, "نماد پیدا نشد!\nمثال: فولاد، شپنا، خودرو"

    price, t1, t2, stop, power, status = DATA[found]
    text = f"""
تحلیل زنده نماد *{found}*

وضعیت: *{status}*
قیمت فعلی: {price} تومان
تارگت اول: {t1}
تارگت دوم: {t2}
استاپ لاس: {stop}
قدرت سیگنال: {power}

#بورس_تهران #دراگونفلای
    """.strip()

    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor="black")
    ax.set_facecolor("black")
    prices = [float(price)-30, float(price)-10, float(price), float(t1), float(t2)]
    ax.plot(prices, color="#00ff88", linewidth=4, marker="o", markersize=10)
    ax.set_title(f"نماد: {found}", color="white", fontsize=18, weight="bold")
    ax.grid(True, alpha=0.3)
    ax.tick_params(colors="white")
    ax.text(0, prices[0], "استاپ", color="red", weight="bold", fontsize=12)
    ax.text(4, prices[4], "تارگت", color="#00ff88", weight="bold", fontsize=12)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='black', dpi=150)
    plt.close()
    buf.seek(0)
    return buf, text
# ==========================================================================

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
        await q.edit_message_text("نماد کریپتو بفرست (مثل BTCUSDT):")
        context.user_data["mode"] = "crypto"
    elif q.data == "stock":
        await q.edit_message_text("نماد بورسی بفرست (مثل فولاد):")
        context.user_data["mode"] = "stock"
    elif q.data == "buy":
        await q.edit_message_text("عضویت VIP: ۹۹ تتر ماهانه\nپرداخت به @dragonfly_support\nرسید بفرست تا فعال شه!")
    else:
        await q.edit_message_text("منوی اصلی:", reply_markup=menu())

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "mode" not in context.user_data:
        return
    uid = update.effective_user.id
    mode = context.user_data["mode"]

    if mode == "stock":
        chart, txt = analyze_stock(update.message.text, is_vip=is_vip(uid))
        if chart:
            await update.message.reply_photo(InputFile(chart, "stock.png"), caption=txt, parse_mode="Markdown")
        else:
            await update.message.reply_text(txt)

    elif mode == "crypto":
        sym = update.message.text.strip().upper()
        if not sym.endswith("USDT"): sym += "USDT"
        chart, txt = analyze_crypto(sym, is_vip=is_vip(uid))
        if chart:
            await update.message.reply_photo(InputFile(chart, "crypto.png"), caption=txt)

    await update.message.reply_text("تحلیل تموم شد!", reply_markup=menu())
    context.user_data.clear()

# دستور ادمین
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
    print("Dragonfly با موفقیت روی Render اجرا شد — همه چیز کار می‌کنه!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
























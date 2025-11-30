import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ---------- Fake Web Server برای Render (تا نخوابه) ----------
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Dragonfly 24/7 - ربات زنده‌ست 🪰", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

# ---------- تنظیمات لاگ ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- توکن ----------
TOKEN = os.getenv("TELEGRAM_TOKEN")

# ---------- منوی اصلی ----------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("تحلیل بورس", callback_data="stock")],
        [InlineKeyboardButton("سیگنال VIP", callback_data="signal")],
        [InlineKeyboardButton("عضویت در کانال", callback_data="subscribe")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")],
    ])

# ---------- دستور /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ("به Dragonfly خوش اومدی 🪰\n"
            "سنجاقک بازار آماده پرواز کرد!\n\n"
            "یکی از گزینه‌ها رو انتخاب کن")
    await update.message.reply_text(text, reply_markup=main_menu())

# ---------- دکمه‌ها ----------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    texts = {
        "crypto": "نماد کریپتو رو بنویس (مثل BTCUSDT):",
        "stock": "نماد بورسی رو بنویس (مثل فولاد):",
        "signal": "سیگنال‌های VIP در حال اسکن…",
        "subscribe": "عضویت در کانال VIP\nهزینه: ۹۹ تتر (TRC20)\n@dragonfly_support",
        "support": "پشتیبانی سریع:\n@dragonfly_support",
        "start": "به Dragonfly خوش اومدی 🪰\nیکی از گزینه‌ها رو انتخاب کن"
    }

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت 🔙", callback_data="start")]])

    if query.data == "start":
        await query.edit_message_text(texts["start"], reply_markup=main_menu())
    else:
        await query.edit_message_text(texts.get(query.data, "به زودی…"), reply_markup=reply_markup)

# ---------- پیام متنی معمولی ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("این بخش در حال توسعه است... 🔧")

# ---------- تابع اصلی ----------
def main():
    # ساخت اپ تلگرام
    app = Application.builder().token(TOKEN).build()

    # هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # راه‌اندازی وب‌سرور فیک (برای Render)
    threading.Thread(target=run_flask, daemon=True).start()
    print("Fake web server روی پورت 10000 فعال شد — ربات 24/7 می‌مونه!")

    # پیام استارت
    print("Dragonfly روی Render زنده شد و داره کار می‌کنه! 🪰")

    # شروع polling
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
















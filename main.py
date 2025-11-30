import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from analyzer import analyze_crypto

# ---------- Fake Web Server برای Render (تا نخوابه) ----------
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Dragonfly 24/7 - ربات زنده‌ست", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask, daemon=True).start()

# ---------- تنظیمات ----------
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TELEGRAM_TOKEN")
VIP_CHANNEL = "https://t.me/+tAS8b3RGZBcwMWJk"   # ← اسم کانال VIP خودت رو اینجا بنویس

# ---------- منوی اصلی ----------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("تحلیل بورس", callback_data="stock")],
        [InlineKeyboardButton("سیگنال VIP", callback_data="signal")],
        [InlineKeyboardButton("عضویت در کانال", callback_data="subscribe")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")],
    ])

# ---------- دستورات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ("به Dragonfly خوش اومدی\n"
            "سنجاقک بازار آماده پرواز کرد!\n\n"
            "یکی از گزینه‌ها رو انتخاب کن")
    await update.message.reply_text(text, reply_markup=main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "crypto":
        await query.edit_message_text("نماد کریپتو رو بنویس (مثل BTCUSDT):")
        context.user_data['waiting_for'] = 'crypto_symbol'

    elif query.data == "start":
        await query.edit_message_text("منوی اصلی", reply_markup=main_menu())

    else:
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="start")]])
        texts = {
            "stock": "تحلیل بورس به زودی…",
            "signal": "برای دریافت سیگنال VIP باید عضو کانال باشی\n@dragonfly_vip_channel",
            "subscribe": "عضویت در کانال VIP\nهزینه: ۹۹ تتر\n@dragonfly_support",
            "support": "پشتیبانی: @dragonfly_support"
        }
        await query.edit_message_text(texts.get(query.data, "به زودی…"), reply_markup=back_btn)

# ---------- دریافت نماد و تحلیل ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for') == 'crypto_symbol':
        symbol = update.message.text.strip().upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"

        user_id = update.effective_user.id
        await update.message.reply_chat_action("upload_photo")
        await update.message.reply_text("در حال تحلیل... لطفاً صبر کن")

        # چک کردن عضویت در کانال VIP
        is_vip = False
        try:
            member = await context.bot.get_chat_member(VIP_CHANNEL, user_id)
            if member.status in ["member", "administrator", "creator"]:
                is_vip = True
        except:
            pass  # اگر کانال وجود نداشت یا خطا داد → غیر VIP

        chart_buf, analysis_text = analyze_crypto(symbol, is_vip=is_vip)

        if chart_buf:
            await update.message.reply_photo(
                photo=InputFile(chart_buf, filename="chart.png"),
                caption=analysis_text
            )
            await update.message.reply_text(
                "تحلیل جدید آماده شد!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("منوی اصلی", callback_data="start")]])
            )
        else:
            await update.message.reply_text("نماد اشتباهه یا داده نداره! دوباره امتحان کن")

        context.user_data['waiting_for'] = None
        return

    # اگر پیام معمولی بود
    await update.message.reply_text("دستور /start رو بزن")

# ---------- اجرای ربات ----------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Dragonfly با سیستم VIP راه‌اندازی شد!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

















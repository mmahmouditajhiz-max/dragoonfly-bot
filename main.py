import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# برای دیدن ارورها تو Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("تحلیل بورس", callback_data="stock")],
        [InlineKeyboardButton("سیگنال VIP", callback_data="signal")],
        [InlineKeyboardButton("عضویت در کانال", callback_data="subscribe")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "به Dragonfly خوش اومدی\nسنجاقک بازار آماده پرواز کرد!\n\nیکی از گزینه‌ها رو انتخاب کن",
        reply_markup=main_menu()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    texts = {
        "crypto": "نماد کریپتو رو بنویس (مثل BTCUSDT):",
        "stock": "نماد بورسی رو بنویس (مثل فولاد):",
        "signal": "سیگنال VIP فقط برای صاحب ربات",
        "subscribe": "عضویت VIP: ۹۹ تتر\n@dragonfly_support",
        "support": "پشتیبانی: @dragonfly_support",
    }

    await query.edit_message_text(
        texts.get(query.data, "به زودی…"),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="start")]])
    )

    if query.data == "start":
        await query.edit_message_text(
            "به Dragonfly خوش اومدی\nسنجاقک بازار آماده پرواز کرد!\n\nیکی از گزینه‌ها رو انتخاب کن",
            reply_markup=main_menu()
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("این بخش در حال توسعه است...")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Dragonfly روی Render ۱۰۰٪ زنده شد و داره کار می‌کنه!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()














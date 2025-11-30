import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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
    q = update.callback_query
    await q.answer()
    
    texts = {
        "crypto": "نماد کریپتو رو بنویس (مثل BTCUSDT):",
        "stock": "نماد بورسی رو بنویس (مثل فولاد):",
        "signal": "سیگنال VIP فقط برای صاحب ربات",
        "subscribe": "عضویت VIP: ۹۹ تتر\n@dragonfly_support",
        "support": "پشتیبانی: @dragonfly_support",
    }
    
    await q.edit_message_text(
        texts.get(q.data, "به زودی…"),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="start")]])
    )

    if q.data == "start":
        await q.edit_message_text(
            "به Dragonfly خوش اومدی\nسنجاقک بازار آماده پرواز کرد!\n\nیکی از گزینه‌ها رو انتخاب کن",
            reply_markup=main_menu()
        )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("Dragonfly روی Render زنده شد!")
app.run_polling(drop_pending_updates=True)













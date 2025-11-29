import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_ID = 119885988  # آیدی خودت

def main_menu():
    kb = [
        [InlineKeyboardButton("تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("تحلیل بورس", callback_data="stock")],
        [InlineKeyboardButton("سیگنال VIP", callback_data="signal")],
        [InlineKeyboardButton("عضویت در کانال", callback_data="subscribe")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")],
    ]
    return InlineKeyboardMarkup(kb)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="back")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "به Dragonfly خوش اومدی\nسنجاقک بازار آماده پرواز کرد!\n\nیکی از گزینه‌ها رو انتخاب کن"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu())
    else:
        await update.callback_query.message.delete()
        await update.callback_query.message.chat.send_message(text, reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "back":
        await q.message.delete()
        await q.message.chat.send_message(
            "به Dragonfly خوش اومدی\nسنجاقک بازار آماده پرواز کرد!\n\nیکی از گزینه‌ها رو انتخاب کن",
            reply_markup=main_menu()
        )
        return

    texts = {
        "crypto": "نماد کریپتو رو بنویس (مثل BTCUSDT):",
        "stock": "نماد بورسی رو بنویس (مثل فولاد):",
        "signal": "سیگنال‌های VIP در حال اسکن…" if q.from_user.id == OWNER_ID else "این بخش فقط برای صاحب ربات فعال است",
        "subscribe": "عضویت در کانال VIP\n\nهزینه: ۹۹ تتر (TRC20)\nبعد از واریز رسید رو به پشتیبانی بفرست\n\n@dragonfly_support",
        "support": "پشتیبانی Dragonfly\n@dragonfly_support\nسریع جواب می‌دم",
    }

    await q.message.delete()
    await q.message.chat.send_message(texts[q.data], reply_markup=back_button())

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Dragonfly بدون مینا — تمیز و سریع!")
    
    # keep-alive برای Railway (دیگه نمی‌میره)
    app.run_polling(drop_pending_updates=True)
    while True:
        import time
        time.sleep(3600)
        print("Keep-alive: Dragonfly هنوز زنده‌ست!")

if __name__ == "__main__":
    main()











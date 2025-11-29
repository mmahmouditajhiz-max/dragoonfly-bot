import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_ID = 123456789  # ← آیدی عددی خودت رو اینجا بذار

# عکس مینا (ه
MINA_PHOTO = "https://i.ibb.co/5nM3Y8p/mina-dragonfly.jpg"

# منوی اصلی – دقیقاً همون چیزی که تو عکس داری
def main_menu():
    keyboard = [
        [InlineKeyboardButton("تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("تحلیل بورس", callback_data="stock")],
        [InlineKeyboardButton("مینا (هوش مصنوعی)", callback_data="mina")],
        [InlineKeyboardButton("سیگنال VIP", callback_data="signal")],
        [InlineKeyboardButton("عضویت در کانال", callback_data="subscribe")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="back")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "به Dragonfly خوش اومدی 🪰\nسنجاقک بازار آماده پرواز کرد!\n\nیکی از گزینه‌ها رو انتخاب کن 👇"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu())
    else:
        await update.callback_query.message.edit_text(text, reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        await query.edit_message_text(
            "به Dragonfly خوش اومدی 🪰\nسنجاقک بازار آماده پرواز کرد!\n\nیکی از گزینه‌ها رو انتخاب کن 👇",
            reply_markup=main_menu()
        )

    elif query.data == "crypto":
        await query.edit_message_text(
            "لطفاً نماد کریپتو رو به انگلیسی بنویس\nمثال: BTCUSDT | ETHUSDT | SOLUSDT",
            reply_markup=back_button()
        )
        context.user_data["mode"] = "crypto"

    elif query.data == "stock":
        await query.edit_message_text(
            "لطفاً نماد بورسی رو بنویس\nمثال: فولاد | شپنا | وبملت",
            reply_markup=back_button()
        )
        context.user_data["mode"] = "stock"

    elif query.data == "mina":
        await query.edit_message_photo(
            photo=MINA_PHOTO,
            caption="سلام من مینا هستم 🧚🏻‍♀\nمشاور بازارهای مالی و بلاک‌چین در آرزو 🌙\n\nهر سوالی داری همینجا بپرس 👇",
            reply_markup=back_button()
        )
        context.user_data["talking_to_mina"] = True

    elif query.data == "signal":
        if query.from_user.id == OWNER_ID:
            await query.edit_message_text("در حال اسکن بازار… سیگنال‌های VIP به زودی 🚀", reply_markup=back_button())
        else:
            await query.edit_message_text("این بخش فقط برای صاحب ربات فعال است 🔒", reply_markup=back_button())

    elif query.data == "subscribe":
        await query.edit_message_text(
            "عضویت در کانال VIP سیگنال‌ها\n\n"
            "هزینه: ۹۹ تتر (شبکه TRC20)\n\n"
            "بعد از واریز، رسید پرداخت رو به پشتیبانی بفرست 👇\n"
            "پشتیبانی: @MahmoudTajhiz_Max",
            reply_markup=back_button()
        )

    elif query.data == "support":
        await query.edit_message_text(
            "پشتیبانی Dragonfly 🪰\n\n@MahmoudTajhiz_Max\nهر سوالی داشتی سریع جواب می‌دم ❤",
            reply_markup=back_button()
        )

# چت با مینا (فعلاً بدون API تا وقتی کلید بذاری بعداً وصلش می‌کنیم)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("talking_to_mina"):
        await update.message.reply_text("مینا الان داره فکر می‌کنه… چند ثانیه صبر کن 😊\n(به زودی کامل فعال می‌شه!)")
        return

    if context.user_data.get("mode") in ["crypto", "stock"]:
        await update.message.reply_text("تحلیل در حال آماده‌سازیه… به زودی کامل می‌شه 🔥")
        context.user_data["mode"] = None

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Dragonfly با منوی رویایی پرواز کرد! 🪰✨")
    app.run_polling()

if __name__ == "__main__":
    main()




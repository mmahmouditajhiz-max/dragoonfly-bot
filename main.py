import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# ================= تنظیمات =================
TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_ID = 119885988  # ← آیدی عددی خودت رو اینجا بذار

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MINA_PHOTO = "https://i.ibb.co/5nM3Y8p/mina-dragonfly.jpg"

# ================= منوی اصلی (دقیقاً مثل Arezu World) =================
def main_menu():
    kb = [
        [InlineKeyboardButton("📈تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("📉تحلیل بورس", callback_data="stock")],
        [InlineKeyboardButton("🤖 مینا (هوش مصنوعی)", callback_data="mina")],
        [InlineKeyboardButton("📊سیگنال VIP", callback_data="signal")],
        [InlineKeyboardButton("📥عضویت در کانال", callback_data="subscribe")],
        [InlineKeyboardButton("✉پشتیبانی", callback_data="support")],
    ]
    return InlineKeyboardMarkup(kb)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="back")]])

# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "به Dragonfly خوش اومدی 🧚‍♀\nسنجاقک بازار آماده پرواز کرد!\n\nیکی از گزینه‌ها رو انتخاب کن 👇"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu())
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu())

# ================= دکمه‌ها =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "back":
        await q.edit_message_text("به Dragonfly خوش اومدی 🧚‍♀\nسنجاقک بازار آماده پرواز کرد!\n\nیکی از گزینه‌ها رو انتخاب کن 👇",
                                  reply_markup=main_menu())

    elif q.data == "crypto":
        await q.edit_message_text("نماد کریپتو رو بنویس (مثل BTCUSDT):", reply_markup=back_button())
        context.user_data["mode"] = "crypto"

    elif q.data == "stock":
        await q.edit_message_text("نماد بورسی رو بنویس (مثل فولاد):", reply_markup=back_button())
        context.user_data["mode"] = "stock"

    elif q.data == "mina":
        await q.edit_message_photo(
            photo=MINA_PHOTO,
            caption="سلام من مینا هستم 🧚🏻‍♀\nمشاور بازارهای مالی و بلاک‌چین در آرزو 🌙\n\nهر سوالی داری بپرس 👇",
            reply_markup=back_button()
        )
        context.user_data["mina_mode"] = True

    elif q.data == "signal":
        if q.from_user.id == OWNER_ID:
            await q.edit_message_text("سیگنال‌های VIP در حال اسکن… 🚀", reply_markup=back_button())
        else:
            await q.edit_message_text("این بخش فقط برای صاحب ربات فعال است", reply_markup=back_button())

    elif q.data == "subscribe":
        await q.edit_message_text(
            "عضویت در کانال VIP\n\nهزینه: ۹۹ تتر (TRC20)\nبعد از واریز رسید رو به پشتیبانی بفرست\n\n@dragonfly_support",
            reply_markup=back_button()
        )

    elif q.data == "support":
        await q.edit_message_text("پشتیبانی Dragonfly\n@dragonfly_support\nسریع جواب می‌دم ❤", reply_markup=back_button())

# ================= چت با مینا (زنده با Groq) =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mina_mode"):
        await update.message.reply_chat_action("typing")
        try:
            response = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                temperature=0.7,
                messages=[
                    {"role": "system", "content": """
شما مینا هستید — پری خرد مالی آرزو ورلد 🧚🏻‍♀

شخصیت: آرام، جدی اما گرم | لحن استادانه | فارسی | ایموجی‌های 📊✨📈💡
ممنوع: هیچ سیگنال خرید/فروش، هیچ پیش‌بینی قیمت، هیچ قول سود
مجاز: آموزش ذهنیت مالی، روانشناسی سرمایه‌گذاری، صبر، نظم، بلاک‌چین
لحن نمونه: «سرمایه‌گذاری سفر درونی هم هست… صبر و دانش تو را رشد می‌دهد ✨»
                    """},
                    {"role": "user", "content": update.message.text}
                ]
            )
            await update.message.reply_text(response.choices[0].message.content.strip())
        except Exception as e:
            await update.message.reply_text("مینا الان یکم خسته‌ست… چند دقیقه دیگه دوباره امتحان کن 😴")
        return

    if context.user_data.get("mode"):
        await update.message.reply_text("در حال تحلیل… به زودی آماده می‌شه 🔥")
        context.user_data["mode"] = None

# ================= اجرا =================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Dragonfly + مینا زنده شد! 🧚‍♀✨")
    app.run_polling()

if __name__ == "__main__":
    main()






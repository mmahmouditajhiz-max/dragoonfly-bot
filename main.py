import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_ID = 119885988  # ← آیدی خودت

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MINA_PHOTO = "https://files.catbox.moe/g22izd.jpg"  # دائمی و کار می‌کنه

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "به Dragonfly خوش اومدی 🧚‍♀\nسنجاقک بازار آماده پرواز کرد!\n\nیکی از گزینه‌ها رو انتخاب کن 👇"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu())
    else:
        await update.callback_query.message.delete()
        await update.callback_query.message.chat.send_message(text, reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    # دکمه بازگشت — حالا بدون ارور کار می‌کنه
    if q.data == "back":
        await q.message.delete()
        await q.message.chat.send_message(
            "به Dragonfly خوش اومدی 🧚‍♀\nسنجاقک بازار آماده پرواز کرد!\n\nیکی از گزینه‌ها رو انتخاب کن 👇",
            reply_markup=main_menu()
        )
        return

    # دکمه مینا
    if q.data == "mina":
        await q.message.delete()
        await q.message.chat.send_photo(
            photo=MINA_PHOTO,
            caption="سلام من مینا هستم 🧚🏻‍♀\nمشاور بازارهای مالی و بلاک‌چین در آرزو 🌙\n\nهر سوالی داری بپرس 👇",
            reply_markup=back_button()
        )
        context.user_data["mina_mode"] = True
        return

    # بقیه دکمه‌ها (همه با delete + send جدید)
    texts = {
        "crypto": "نماد کریپتو رو بنویس (مثل BTCUSDT):",
        "stock": "نماد بورسی رو بنویس (مثل فولاد):",
        "signal": "این بخش فقط برای صاحب ربات فعال است" if q.from_user.id != OWNER_ID else "سیگنال‌های VIP در حال اسکن…🚀",
        "subscribe": "عضویت در کانال VIP\n\nهزینه: ۹۹ تتر (TRC20)\nبعد از واریز رسید رو به پشتیبانی بفرست\n\n@dragonfly_support",
        "support": "پشتیبانی Dragonfly\n@dragonfly_support\nسریع جواب می‌دم ❤",
    }

    await q.message.delete()
    await q.message.chat.send_message(texts[q.data], reply_markup=back_button())
    if q.data in ["crypto", "stock"]:
        context.user_data["mode"] = q.data

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mina_mode"):
        await update.message.reply_chat_action("typing")
        try:
            response = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                temperature=0.7,
                messages=[
                    {"role": "system", "content": "شما مینا هستید — پری خرد مالی آرزو ورلد. آرام، عمیق، فارسی. فقط آموزش ذهنیت، روانشناسی، صبر و نظم. هیچ سیگنال و پیش‌بینی قیمت نده."},
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

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Dragonfly زنده شد و ۲۴/۷ آنلاینه!")

    # این خط مهم‌ترین تغییره — keep-alive برای Railway
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=2.0,
        timeout=30
    )

    # این لوپ بی‌نهایت باعث می‌شه Railway دیگه کانتینر رو نکشه
    try:
        while True:
            asyncio.run(asyncio.sleep(3600))  # هر ساعت یه بار یه چیزی می‌نویسه تو log
            print("Keep-alive: Dragonfly هنوز زنده‌ست!")
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()










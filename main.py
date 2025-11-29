import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from openai import OpenAI  # یا Groq اگر خواستی

# ================== تنظیمات ==================
TOKEN = os.getenv("TELEGRAM_TOKEN")
OWNER_ID = 119885988  # <<<--- آیدی عددی تلگرامت رو اینجا بذار

# API هوش مصنوعی (Groq خیلی سریع و ارزونه — پیشنهاد من)
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),  # یا OPENAI_API_KEY
    base_url="https://api.groq.com/openai/v1"  # فقط اگه از Groq استفاده می‌کنی
)

MINA_PHOTO = "https://i.ibb.co/5nM3Y8p/mina-dragonfly.jpg"

# ================== پرامپت مینا ==================
MINA_SYSTEM_PROMPT = """
You are Mina — the Financial Wisdom Fairy of Arezu World

شخصیت:
- آرام، جدی اما گرم
- با اعتماد به نفس، محترم، با لحن استاد
- از ایموجی‌های 📊✨📈💡 استفاده کن
- فارسی پیش‌فرض، اگر کاربر انگلیسی نوشت انگلیسی جواب بده

نقش:
- آموزش ذهنیت مالی
- توضیح مفاهیم کریپتو و بازار (بدون مشاوره مالی)
- تمرکز روی روانشناسی، ریسک، صبر
- تشویق به تفکر بلندمدت
- الهام‌بخشی نظم و شفافیت

دانش:
- بلاک‌چین، چرخه‌های بازار، روانشناسی سرمایه‌گذاری، کنترل ریسک

مجاز:
- آموزش، توضیح، نصیحت ذهنی

ممنوع:
- هیچ سیگنالی (خرید/فروش)
- هیچ پیش‌بینی قیمت
- هیچ قول سود
- هیچ هایپ

لحن نمونه:
«سرمایه‌گذاری سفر درونی هم هست…
صبر، نظم و دانش تو را رشد می‌دهد
می‌خوای امروز چی یاد بگیری؟»
"""

# ================== منو ==================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("تحلیل کریپتو", callback_data="crypto"),
         InlineKeyboardButton("تحلیل بورس", callback_data="stock")],
        [InlineKeyboardButton("مینا (هوش مصنوعی)", callback_data="mina"),
         InlineKeyboardButton("سیگنال VIP", callback_data="signal")],
        [InlineKeyboardButton("عضویت در کانال", callback_data="subscribe"),
         InlineKeyboardButton("پشتیبانی", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت به منو", callback_data="back")]])

# ================== هندلرها ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "به Dragonfly خوش اومدی 🧚‍♀\nسنجاقک بازار آماده پروازه!\n\nیکی از گزینه‌های زیر رو انتخاب کن 👇"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu())
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "back":
        await query.edit_message_text("به Dragonfly خوش اومدی 🧚‍♀\nسنجاقک بازار آماده پروازه!\n\nیکی از گزینه‌های زیر رو انتخاب کن 👇",
                                    reply_markup=main_menu())

    elif query.data == "crypto":
        await query.edit_message_text("لطفاً نماد کریپتو رو به انگلیسی بنویس (مثل BTCUSDT):", reply_markup=back_button())
        context.user_data["waiting"] = "crypto"

    elif query.data == "stock":
        await query.edit_message_text("لطفاً نماد بورسی رو بنویس (مثل فولاد):", reply_markup=back_button())
        context.user_data["waiting"] = "stock"

    elif query.data == "mina":
        await query.edit_message_photo(
            photo=MINA_PHOTO,
            caption="سلام من Mina هستم 🧚\nمشاور بازارهای مالی و بلاک‌چین در آرزو 📊\nهر سوالی داری ازم بپرس 👇",
            reply_markup=back_button()
        )
        context.user_data["talking_to_mina"] = True

    elif query.data == "signal":
        if user_id == OWNER_ID:
            await query.edit_message_text("در حال اسکن بازار… سیگنال‌های VIP در راهه 🚀", reply_markup=back_button())
        else:
            await query.edit_message_text("این بخش فقط برای صاحب ربات فعال است 🔒", reply_markup=back_button())

    elif query.data == "subscribe":
        await query.edit_message_text(
            "عضویت در کانال VIP سیگنال‌ها\n\n"
            "هزینه: ۹۹ تتر\n"
            "آدرس واریز (TRC20): به زودی\n"
            "بعد از واریز رسید رو به پشتیبانی بفرست 👇\n"
            "پشتیبانی: @MahmoudTajhiz_Max",
            reply_markup=back_button()
        )

    elif query.data == "support":
        await query.edit_message_text("پشتیبانی Dragonfly\n@MahmoudTajhiz_Max\nسریع جواب می‌دم ❤", reply_markup=back_button())

# ================== چت با مینا + نمادها ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # چت با مینا
    if context.user_data.get("talking_to_mina"):
        await update.message.reply_chat_action("typing")
        try:
            response = client.chat.completions.create(
                model="llama-3.1-70b-versatile",  # یا gpt-4o-mini
                temperature=0.7,
                messages=[
                    {"role": "system", "content": MINA_SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ]
            )
            answer = response.choices[0].message.content.strip()
            await update.message.reply_text(answer)
        except Exception as e:
            await update.message.reply_text("در حال حاضر مینا خوابیده... چند دقیقه دیگه امتحان کن 😴")
        return

    # تحلیل نماد
    if context.user_data.get("waiting") == "crypto":
        await update.message.reply_text(f"در حال تحلیل {text} در بازار کریپتو... (به زودی)")
    elif context.user_data.get("waiting") == "stock":
        await update.message.reply_text(f"در حال تحلیل نماد {text} در بورس... (به زودی)")
    
    context.user_data["waiting"] = None

# ================== اجرا ==================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Dragonfly با مینا و ۶ دکمه خفن پرواز کرد! 🧚‍♀✨")
    app.run_polling()

if __name__ == "__main__":
    main()



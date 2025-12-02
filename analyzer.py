# main.py - نسخه نهایی با ارسال خودکار سیگنال به کانال VIP
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from analyzer import analyze_crypto

# وب سرور برای Render
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Dragonfly 24/7", 200
threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=10000), daemon=True).start()

# تنظیمات
TOKEN = os.getenv("TELEGRAM_TOKEN")
VIP_CHANNEL_ID = -1003186797547   # ← آیدی کانال VIP شما
ADMIN_ID = 7987989849             # ← آیدی ادمین (خودت)

# منو
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("کانال VIP", url="https://t.me/+0B-Q8wt-1zJhNDc8")],
        [InlineKeyboardButton("عضویت VIP", callback_data="buy")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("به Dragonfly خوش اومدی!\nیکی رو انتخاب کن:", reply_markup=main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "crypto":
        await q.edit_message_text("نماد کریپتو بفرست (مثل BTC یا BTCUSDT):")
        context.user_data["mode"] = "crypto"

    elif q.data == "buy":
        await q.edit_message_text("عضویت VIP: ۹۹ تتر ماهانه\nپرداخت به @dragonfly_support\nرسید بفرست")

    elif q.data == "support":
        await q.edit_message_text("پشتیبانی ۲۴ ساعته:\n@dragonfly_support", reply_markup=main_menu())

    else:
        try:
            await q.edit_message_text("منوی اصلی:", reply_markup=main_menu())
        except:
            pass

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mode") != "crypto":
        return

    sym = update.message.text.strip().upper()
    if not sym.endswith("USDT"):
        sym += "USDT"

    user_id = update.effective_user.id
    is_vip_user = (user_id == ADMIN_ID)  # ادمین همیشه VIPه

    # چک کردن عضویت در کانال VIP
    try:
        member = await context.bot.get_chat_member(VIP_CHANNEL_ID, user_id)
        if member.status in ["member", "administrator", "creator"]:
            is_vip_user = True
    except:
        pass  # اگه خطا داد، یعنی عضو نیست

    chart, txt = analyze_crypto(sym, is_vip=is_vip_user)

    if chart:
        await update.message.reply_photo(InputFile(chart, "chart.png"), caption=txt)

        # ارسال خودکار به کانال VIP فقط اگه کاربر VIP باشه
        if is_vip_user:
            try:
                await context.bot.send_photo(
                    chat_id=VIP_CHANNEL_ID,
                    photo=chart,
                    caption=f"سیگنال VIP 🔥\n\n{txt}\n\n@dragonfly_support",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print("خطا در ارسال به کانال VIP:", e)
    else:
        await update.message.reply_text(txt or "نماد پیدا نشد!")

    await update.message.reply_text("تحلیل تموم شد", reply_markup=main_menu())
    context.user_data.clear()

# دستور اضافه کردن VIP (فقط ادمین)
async def addvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        uid = int(context.args[0])
        await context.bot.send_message(uid, "شما به VIP اضافه شدید!")
        await update.message.reply_text("کاربر اضافه شد")
    except:
        await update.message.reply_text("استفاده: /addvip 123456789")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    app.add_handler(CommandHandler("addvip", addvip))
    print("Dragonfly با ارسال خودکار سیگنال VIP راه‌اندازی شد!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

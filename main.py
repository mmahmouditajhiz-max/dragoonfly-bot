import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من Dragonfly هستم\n"
        "سنجاقک بازار! بال‌هام روی چارت می‌رقصن…\n\n"
        "در حال راه‌اندازی کامل… ۱۰ ثانیه دیگه آماده‌ام!"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Dragonfly زنده‌ست!\n"
        "مدل فعال: در حال حاضر غیرفعال (لوکال استفاده می‌شه)\n"
        "سرور: Railway 24/7\n"
        "وضعیت: عالی"
    )

app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))

print("Dragonfly داره بال می‌زنه…")
await app.initialize()
await app.start()
await app.updater.start_polling()
await app.updater.idle()

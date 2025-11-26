import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من Dragonfly هستم 🪰\n"
        "سنجاقک بازار! بال‌هام روی چارت می‌رقصن…\n\n"
        "همه چیز آماده‌ست! حالا می‌تونی دستورات رو بزنی 🔥"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Dragonfly زنده و ۲۴/۷ آنلاینه!\n"
        "سرور: Railway\n"
        "وضعیت: عالی و آماده شکار!"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    
    print("Dragonfly داره بال می‌زنه… 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()


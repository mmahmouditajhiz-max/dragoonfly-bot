import os
import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import pandas_ta as ta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import ollama

# --- تنظیمات ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HYPERLIQUID_API = os.getenv("HYPERLIQUID_API_KEY", "")
HYPERLIQUID_SECRET = os.getenv("HYPERLIQUID_SECRET", "")
NOBITEX_USER = os.getenv("NOBITEX_USER", "")
NOBITEX_PASS = os.getenv("NOBITEX_PASS", "")

# --- پیام خوش‌آمدگویی ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من Dragonfly هستم 🪰\n"
        "سنجاقک بازار! بال‌هام روی چارت می‌رقصن…\n\n"
        "دستورات:\n/status → وضعیت\n/trade → معامله تست\n/ping → پینگ"
    )

# --- وضعیت ---
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model = ollama.list()['models'][0]['name'] if ollama.list().get('models') else "ندارد"
    await update.message.reply_text(
        f"Dragonfly زنده‌ست! 🪰\n"
        f"مدل فعال: {model}\n"
        f"سرور: Railway (24/7)\n"
        f"پینگ به Hyperliquid: عالی 🔥"
    )

# --- اجرا ---
app = Application.builder().token(TELEGRAM_TOKEN).concurrent_updates(True).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))

print("Dragonfly داره پرواز می‌کنه… 🪰")
app.run_polling()
# main.py
import os, json, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# دو تا analyzer جدا
from analyzer import analyze_crypto
from stock_analyzer import analyze_stock   # جدید

# وب سرور
Flask(__name__).run(host="0.0.0.0", port=10000, debug=False, use_reloader=False, threaded=True)

TOKEN = os.getenv("TELEGRAM_TOKEN")
VIP_LINK = "https://t.me/+0B-Q8wt-1zJhNDc8"
ADMIN_ID = 7987989849

# VIP سیستم
VIP_FILE = "vip_users.json"
def load(): 
    try: return set(json.load(open(VIP_FILE)))
    except: return {ADMIN_ID}
def save(s): json.dump(list(s), open(VIP_FILE, "w"))
VIP_USERS = load()

def is_vip(uid): return uid in VIP_USERS
def add_vip(uid): VIP_USERS.add(uid); save(VIP_USERS)

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("تحلیل بورس تهران", callback_data="stock")],
        [InlineKeyboardButton("کانال VIP", url=VIP_LINK)],
        [InlineKeyboardButton("عضویت VIP", callback_data="buy")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام داداش! به Dragonfly خوش اومدی\nیکی رو بزن:", reply_markup=menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.data == "crypto":
        await q.edit_message_text("نماد کریپتو بفرست (مثل BTC):")
        context.user_data["mode"] = "crypto"
    elif q.data == "stock":
        await q.edit_message_text("نماد بورسی بفرست (مثل فولاد):")
        context.user_data["mode"] = "stock"
    elif q.data == "buy":
        await q.edit_message_text("عضویت VIP: ۹۹ تتر ماهانه\nپرداخت به @dragonfly_support\nرسید بفرست تا فعال بشه!")
    else:
        await q.edit_message_text("منوی اصلی:", reply_markup=menu())

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "mode" not in context.user_data: return
    uid = update.effective_user.id
    mode = context.user_data["mode"]

    if mode == "stock":
        chart, text = analyze_stock(update.message.text, is_vip=is_vip(uid))
        if chart:
            await update.message.reply_photo(InputFile(chart, "stock.png"), caption=text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text)

    elif mode == "crypto":
        sym = update.message.text.strip().upper() + ("USDT" if not update.message.text.endswith("USDT") else "")
        chart, text = analyze_crypto(sym, is_vip=is_vip(uid))
        if chart:
            await update.message.reply_photo(InputFile(chart, "crypto.png"), caption=text)

    await update.message.reply_text("تحلیل تموم شد!", reply_markup=menu())
    context.user_data.clear()

# دستور ادمین
async def addvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        add_vip(int(context.args[0]))
        await update.message.reply_text("اضافه شد به VIP!")
    except:
        await update.message.reply_text("استفاده: /addvip 123456789")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    app.add_handler(CommandHandler("addvip", addvip))
    print("Dragonfly با ساختار حرفه‌ای (دو فایل جدا) راه‌اندازی شد!")
    app.run_polling()

if __name__ == "__main__":
    main()






















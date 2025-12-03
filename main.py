import os
import logging
import threading
import asyncio
import json
from datetime import datetime
from scanner import start_scanner
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from analyzer import analyze_crypto

# ---------- Fake Web Server ----------
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Dragonfly 24/7 - ربات زنده‌ست", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask, daemon=True).start()

# ---------- مدیرت VIP ----------
VIP_FILE = "vip_users.json"

def load_vip_users():
    if os.path.exists(VIP_FILE):
        try:
            with open(VIP_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_vip_users(users_dict):
    with open(VIP_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=2)

def add_vip_user(user_id, username=""):
    users = load_vip_users()
    users[str(user_id)] = {
        "active": True,
        "username": username or f"user_{user_id}",
        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_vip_users(users)

def remove_vip_user(user_id):
    users = load_vip_users()
    if str(user_id) in users:
        del users[str(user_id)]
        save_vip_users(users)

def is_vip_user(user_id):
    users = load_vip_users()
    user_data = users.get(str(user_id))
    return user_data and user_data.get("active", False)

# ---------- تنظیمات ----------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 7987989849  # ← آیدی خودت

# ---------- وضعیت کاربران ----------
user_states = {}

# ---------- منوی اصلی ----------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("🚨 سیگنال VIP", callback_data="signal")],
        [InlineKeyboardButton("⭐ عضویت VIP", callback_data="subscribe")],
        [InlineKeyboardButton("📊 وضعیت VIP", callback_data="vip_status")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="support")],
    ])

# ---------- دستورات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
👋 سلام {user.first_name}!

به *Dragonfly Trading Bot* خوش آمدید.
سنجاقک بازار آماده پرواز! 🚀

📊 امکانات:
• تحلیل تکنیکال لحظه‌ای
• اسکنر 24/7 نمادها
• سیگنال‌های VIP
• پشتیبانی حرفه‌ای

یکی از گزینه‌ها رو انتخاب کن:
"""
    await update.message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 راهنما

/start - منوی اصلی
/analyze BTCUSDT - تحلیل سریع
/subscribe - اطلاعات عضویت
/vip_status - وضعیت VIP
/support - پشتیبانی

💡 نکته: برای تحلیل، نماد رو مثل BTCUSDT وارد کن
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("نماد رو وارد کن:\nمثال: /analyze BTCUSDT", parse_mode='Markdown')
        return
    
    symbol = context.args[0].strip().upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    
    await process_analysis(update, context, symbol)

async def process_analysis(update, context, symbol):
    """پردازش تحلیل"""
    user_id = update.effective_user.id
    is_vip = is_vip_user(user_id)
    
    if user_id == ADMIN_ID:
        is_vip = True
    
    try:
        await update.message.reply_chat_action("upload_photo")
        await update.message.reply_text(f"🔍 تحلیل {symbol}...")
        
        chart_buf, analysis_text = analyze_crypto(symbol, is_vip=is_vip)
        
        if chart_buf and analysis_text:
            # ارسال عکس
            await update.message.reply_photo(
                photo=InputFile(chart_buf, filename="chart.png"),
                caption=analysis_text[:1024],
                parse_mode='Markdown'
            )
            
            # دکمه بازگشت
            await update.message.reply_text(
                "✅ تحلیل آماده!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📈 تحلیل نماد دیگر", callback_data="crypto")],
                    [InlineKeyboardButton("🏠 منوی اصلی", callback_data="start")]
                ])
            )
        else:
            await update.message.reply_text("❌ خطا! نماد رو چک کن.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)[:100]}")
        print(f"خطای تحلیل: {e}")

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_vip_user(user_id):
        await update.message.reply_text("✅ شما VIP هستید!")
        return
    
    subscribe_text = f"""
🎟 عضویت VIP

با عضویت دریافت می‌کنید:
✅ سیگنال‌های لحظه‌ای از اسکنر 24/7
✅ تحلیل‌های پیشرفته
✅ پشتیبانی اختصاصی

💰 هزینه: ۹۹ دلار

📞 برای عضویت پیام بدید به:
@dragonfly_support

🆔 آیدی شما: {user_id}
"""
    await update.message.reply_text(subscribe_text, parse_mode='Markdown')

async def vip_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_vip_user(user_id):
        await update.message.reply_text("✅ شما عضو VIP هستید!")
    else:
        await update.message.reply_text("❌ VIP نیستید. برای عضویت /subscribe")

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    support_text = """
📞 پشتیبانی

@dragonfly_support

🕒 24/7
"""
    await update.message.reply_text(support_text, parse_mode='Markdown')

async def vip_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ فقط ادمین!")
        return
    
    if len(context.args) < 2:
        help_text = """
👑 مدیریت VIP

/vip add 123456789
/vip remove 123456789
/vip list
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    command = context.args[0].lower()
    
    if command == "add" and len(context.args) == 2:
        try:
            target_id = int(context.args[1])
            add_vip_user(target_id)
            await update.message.reply_text(f"✅ {target_id} اضافه شد!")
        except:
            await update.message.reply_text("❌ آیدی عددی!")
    
    elif command == "remove" and len(context.args) == 2:
        try:
            target_id = int(context.args[1])
            remove_vip_user(target_id)
            await update.message.reply_text(f"✅ {target_id} حذف شد!")
        except:
            await update.message.reply_text("❌ آیدی عددی!")
    
    elif command == "list":
        users = load_vip_users()
        if not users:
            await update.message.reply_text("📭 لیست VIP خالی")
        else:
            text = "📋 لیست VIP:\n\n"
            for uid, data in users.items():
                text += f"👤 {uid}\n"
            await update.message.reply_text(text, parse_mode='Markdown')

# ---------- کنترل دکمه‌ها ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "start":
        await query.edit_message_text("منوی اصلی:", reply_markup=main_menu())
    
    elif query.data == "crypto":
        await query.edit_message_text("🔍 نماد رو وارد کن (مثل BTCUSDT):")
        user_states[user_id] = "waiting_symbol"
    
    elif query.data == "signal":
        if is_vip_user(user_id):
            await query.edit_message_text("🚨 شما VIP هستید! سیگنال‌ها خودکار می‌رسند.")
        else:
            await query.edit_message_text("⚠ برای سیگنال باید VIP باشید. /subscribe")
    
    elif query.data == "subscribe":
        await query.delete_message()
        await subscribe_command(update, context)
    
    elif query.data == "vip_status":
        await query.delete_message()
        await vip_status_command(update, context)
    
    elif query.data == "support":
        await query.delete_message()
        await support_command(update, context)

# ---------- دریافت پیام ----------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # اگر در حالت انتظار نماد هست
    if user_states.get(user_id) == "waiting_symbol":
        symbol = text.upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"
        
        # پاک کردن حالت
        user_states[user_id] = None
        
        # پردازش تحلیل
        await process_analysis(update, context, symbol)
        return
    
    # اگر پیام معمولی
    if text.startswith('/'):
        # اگر دستور ناشناخته
        await update.message.reply_text("دستور /start رو بزن", reply_markup=main_menu())
    else:
        await update.message.reply_text("از منو استفاده کن:", reply_markup=main_menu())

# ---------- اجرا ----------
def main():
    print("🚀 راه‌اندازی Dragonfly...")
    
    app = Application.builder().token(TOKEN).build()
    
    # اضافه کردن handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("vip_status", vip_status_command))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(CommandHandler("vip", vip_admin_command))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ ربات آماده!")
    print(f"👑 ادمین: {ADMIN_ID}")
    
    # راه‌اندازی اسکنر
    def start_scanner_delayed():
        import time
        time.sleep(5)
        start_scanner(app.bot)
    
    scanner_thread = threading.Thread(target=start_scanner_delayed, daemon=True)
    scanner_thread.start()
    
    # اجرای ربات
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main() 











































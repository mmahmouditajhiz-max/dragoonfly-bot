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

# ---------- Fake Web Server برای Render (تا نخوابه) ----------
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
    """بارگذاری لیست کاربران VIP"""
    if os.path.exists(VIP_FILE):
        try:
            with open(VIP_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_vip_users(users_dict):
    """ذخیره لیست کاربران VIP"""
    with open(VIP_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=2)

def add_vip_user(user_id, username=""):
    """اضافه کردن کاربر VIP"""
    users = load_vip_users()
    users[str(user_id)] = {
        "active": True,
        "username": username or f"user_{user_id}",
        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_vip_users(users)

def remove_vip_user(user_id):
    """حذف کاربر VIP"""
    users = load_vip_users()
    if str(user_id) in users:
        del users[str(user_id)]
        save_vip_users(users)

def is_vip_user(user_id):
    """چک کردن وضعیت VIP بودن"""
    users = load_vip_users()
    user_data = users.get(str(user_id))
    return user_data and user_data.get("active", False)

# ---------- تنظیمات ----------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
VIP_CHANNEL = "https://t.me/+0B-Q8wt-1zJhNDc8"   # ← کانال VIP
ADMIN_ID = 7987989849  # ← آی‌دی تلگرام خودت

# ---------- منوی اصلی ----------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("📉 تحلیل بورس", callback_data="stock")],
        [InlineKeyboardButton("🚨 سیگنال VIP", callback_data="signal")],
        [InlineKeyboardButton("⭐ عضویت VIP", callback_data="subscribe")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="support")],
        [InlineKeyboardButton("📊 وضعیت VIP", callback_data="vip_status")],
    ])

# ---------- دستورات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع"""
    user = update.effective_user
    welcome_text = f"""
👋 سلام {user.first_name}!

به *Dragonfly Trading Bot* خوش آمدید.
سنجاقک بازار آماده پرواز! 🚀

📊 امکانات ربات:
• تحلیل تکنیکال لحظه‌ای
• اسکنر 24/7 نمادها
• سیگنال‌های VIP
• پشتیبانی حرفه‌ای

یکی از گزینه‌های زیر رو انتخاب کنید:
    """
    await update.message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور راهنما"""
    help_text = """
📖 راهنمای ربات Dragonfly

/start - شروع ربات و منوی اصلی
/analyze BTCUSDT - تحلیل یک نماد خاص
/subscribe - اطلاعات عضویت VIP
/vip_status - بررسی وضعیت VIP بودن شما
/support - ارتباط با پشتیبانی

💡 نکات مهم:
• برای تحلیل، نماد رو مثل BTCUSDT وارد کن
• سیگنال‌های VIP فقط برای اعضا ارسال میشه
• ربات 24/7 در حال اسکن بازار هست
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور تحلیل سریع"""
    if not context.args:
        await update.message.reply_text("لطفاً نماد رو وارد کن:\nمثال: /analyze BTCUSDT", parse_mode='Markdown')
        return
    
    symbol = context.args[0].strip().upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    
    user_id = update.effective_user.id
    is_vip = is_vip_user(user_id)
    
    await update.message.reply_chat_action("upload_photo")
    await update.message.reply_text(f"🔍 در حال تحلیل {symbol}...")
    
    chart_buf, analysis_text = analyze_crypto(symbol, is_vip=is_vip)
    
    if chart_buf:
        await update.message.reply_photo(
            photo=InputFile(chart_buf, filename="chart.png"),
            caption=analysis_text,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ خطا در دریافت داده! نماد رو چک کن.")

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عضویت در سیستم VIP"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "بدون نام"
    
    if is_vip_user(user_id):
        await update.message.reply_text("✅ شما در حال حاضر عضو VIP هستید!")
        return
    
    subscribe_text = f"""
🎟 عضویت در سیستم VIP ربات Dragonfly

با عضویت VIP دریافت می‌کنید:
✅ سیگنال‌های لحظه‌ای از اسکنر 24/7
✅ تحلیل‌های پیشرفته با تارگت و استاپ دقیق
✅ پشتیبانی اختصاصی
✅ دسترسی به کانال VIP

💰 هزینه عضویت: 99 دلار (USDT)

📞 برای عضویت با پشتیبانی تماس بگیرید:
@{VIP_CHANNEL.split('/')[-1]}

🆔 آیدی شما: {user_id}
👤 یوزرنیم: @{username}

💎 پس از پرداخت، آیدی شما به سیستم اضافه می‌شود و سیگنال‌ها را دریافت می‌کنید.
    """
    
    # اطلاع به ادمین
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"🎯 درخواست عضویت VIP\n\n👤 کاربر: {username}\n🆔 آیدی: {user_id}\n📅 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
    except:
        pass
    
    await update.message.reply_text(subscribe_text, parse_mode='Markdown')

async def vip_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی وضعیت VIP"""
    user_id = update.effective_user.id
    
    if is_vip_user(user_id):
        users = load_vip_users()
        user_data = users.get(str(user_id), {})
        added_date = user_data.get("added_date", "نامشخص")
        
        status_text = f"""
✅ وضعیت: عضو VIP

👤 اطلاعات شما:
🆔 آیدی: {user_id}
📅 تاریخ عضویت: {added_date}
🚨 وضعیت: فعال

هم اکنون سیگنال‌های اسکنر 24/7 را دریافت می‌کنید!
        """
    else:
        status_text = """
❌ وضعیت: عضو عادی

شما در حال حاضر عضو VIP نیستید.
برای دریافت سیگنال‌های لحظه‌ای و تحلیل‌های پیشرفته:

1. دستور /subscribe رو بزن
2. با پشتیبانی تماس بگیر
3. هزینه عضویت رو پرداخت کن

💎 با عضویت VIP، اسکنر 24/7 برای شما کار می‌کند!
        """
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور پشتیبانی"""
    support_text = f"""
📞 پشتیبانی Dragonfly

برای ارتباط با پشتیبانی:
👉 @dragonfly_support

🕒 ساعات پاسخگویی: 24/7

🔗 کانال VIP:
{VIP_CHANNEL}

⚠ توجه: فقط در موارد زیر پیام بدید:
• مشکل در تحلیل نماد
• درخواست عضویت VIP
• گزارش باگ ربات
• پیشنهادات و انتقادات
    """
    await update.message.reply_text(support_text, parse_mode='Markdown')

async def vip_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت VIP (فقط ادمین)"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ این دستور فقط برای ادمین است!")
        return
    
    if len(context.args) < 2:
        help_text = """
👑 پنل مدیریت VIP

/vip add 123456789 - اضافه کردن کاربر VIP
/vip remove 123456789 - حذف کاربر VIP
/vip list - نمایش لیست VIP‌ها
/vip check 123456789 - بررسی وضعیت کاربر
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    command = context.args[0].lower()
    
    if command == "add" and len(context.args) == 2:
        try:
            target_id = int(context.args[1])
            username = f"user_{target_id}"
            add_vip_user(target_id, username)
            
            # اطلاع به کاربر
            try:
                await context.bot.send_message(
                    target_id,
                    "🎉 تبریک!\n\nشما به جمع اعضای VIP Dragonfly پیوستید!\n\nاز این لحظه، سیگنال‌های اسکنر 24/7 را دریافت خواهید کرد.\n\nبرای تحلیل می‌تونید از دستور /analyze استفاده کنید یا منتظر سیگنال‌های خودکار باشید!",
                    parse_mode='Markdown'
                )
            except:
                pass
            
            await update.message.reply_text(f"✅ کاربر {target_id} به VIP اضافه شد!")
            
        except ValueError:
            await update.message.reply_text("❌ آیدی باید عددی باشد!")
    
    elif command == "remove" and len(context.args) == 2:
        try:
            target_id = int(context.args[1])
            remove_vip_user(target_id)
            await update.message.reply_text(f"✅ کاربر {target_id} از VIP حذف شد!")
        except ValueError:
            await update.message.reply_text("❌ آیدی باید عددی باشد!")
    
    elif command == "list":
        users = load_vip_users()
        if not users:
            await update.message.reply_text("📭 لیست VIP خالی است")
        else:
            text = "📋 لیست کاربران VIP:\n\n"
            for uid, data in users.items():
                text += f"👤 {uid}\n"
                text += f"   🏷 {data.get('username', 'بدون نام')}\n"
                text += f"   📅 {data.get('added_date', 'نامشخص')}\n"
                text += f"   ✅ فعال\n\n"
            await update.message.reply_text(text, parse_mode='Markdown')
    
    elif command == "check" and len(context.args) == 2:
        try:
            target_id = int(context.args[1])
            if is_vip_user(target_id):
                users = load_vip_users()
                user_data = users.get(str(target_id), {})
                added_date = user_data.get("added_date", "نامشخص")
                await update.message.reply_text(
                    f"✅ کاربر {target_id} VIP است\n📅 تاریخ عضویت: {added_date}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ کاربر {target_id} VIP نیست")
        except ValueError:
            await update.message.reply_text("❌ آیدی باید عددی باشد!")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کنترل کلیک دکمه‌ها"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "crypto":
        await query.edit_message_text("🔍 لطفاً نماد کریپتو را وارد کنید (مثل BTCUSDT):")
        context.user_data['waiting_for'] = 'crypto_symbol'
    
    elif query.data == "stock":
        await query.edit_message_text("📊 تحلیل بورس به زودی اضافه خواهد شد...")
    
    elif query.data == "signal":
        if is_vip_user(user_id):
            await query.edit_message_text("🚨 شما عضو VIP هستید! سیگنال‌ها به صورت خودکار برای شما ارسال می‌شوند.")
        else:
            await query.edit_message_text(
                f"⚠ برای دریافت سیگنال‌های VIP باید عضو شوید:\n\n{VIP_CHANNEL}\n\nیا از دستور /subscribe استفاده کنید.",
                parse_mode='Markdown'
            )
    
    elif query.data == "subscribe":
        await query.delete_message()
        await subscribe_command(update, context)
    
    elif query.data == "support":
        await query.delete_message()
        await support_command(update, context)
    
    elif query.data == "vip_status":
        await query.delete_message()
        await vip_status_command(update, context)
    
    elif query.data == "start":
        await query.edit_message_text("منوی اصلی", reply_markup=main_menu())

# ---------- دریافت نماد و تحلیل ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام متنی"""
    if context.user_data.get('waiting_for') == 'crypto_symbol':
        symbol = update.message.text.strip().upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"
        
        user_id = update.effective_user.id
        await update.message.reply_chat_action("upload_photo")
        await update.message.reply_text(f"🔍 در حال تحلیل {symbol}...")
        
        # چک کردن VIP بودن
        is_vip = is_vip_user(user_id)
        
        # اگر ادمین هست، VIP در نظر بگیر
        if user_id == ADMIN_ID:
            is_vip = True
        
        chart_buf, analysis_text = analyze_crypto(symbol, is_vip=is_vip)
        
        if chart_buf:
            await update.message.reply_photo(
                photo=InputFile(chart_buf, filename="chart.png"),
                caption=analysis_text,
                parse_mode='Markdown'
            )
            await update.message.reply_text(
                "✅ تحلیل آماده شد!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 منوی اصلی", callback_data="start")]])
            )
        else:
            await update.message.reply_text("❌ خطا در تحلیل! نماد رو چک کن.")
        
        context.user_data['waiting_for'] = None
        return
    
    # اگر پیام معمولی بود
    await update.message.reply_text(
        "🤔 دستور /start رو بزن یا از منو استفاده کن.",
        reply_markup=main_menu()
    )

# ---------- اجرای ربات ----------
def main():
    """تابع اصلی اجرای ربات"""
    print("🚀 در حال راه‌اندازی Dragonfly Trading Bot...")
    
    app = Application.builder().token(TOKEN).build()
    
    # اضافه کردن handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("vip_status", vip_status_command))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(CommandHandler("vip", vip_admin_command))
    
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ Dragonfly با موفقیت راه‌اندازی شد!")
    print(f"👑 آیدی ادمین: {ADMIN_ID}")
    print("🤖 ربات در حال اجرا...")
    
    # راه‌اندازی اسکنر در یک تهد جداگانه
    def start_scanner_in_thread():
        import time
        time.sleep(5)  # ۵ ثانیه صبر کن تا ربات کامل بالا بیاد
        start_scanner(app)  # اسکنر رو شروع کن
    
    # اجرای اسکنر در تهد جداگانه
    scanner_thread = threading.Thread(target=start_scanner_in_thread, daemon=True)
    scanner_thread.start()
    
    # اجرای ربات
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()   










































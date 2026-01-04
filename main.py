import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from analyzer import analyze_crypto

# ---------- تنظیمات ----------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_TOKEN not found in environment variables!")
    raise ValueError("لطفا TELEGRAM_TOKEN را در متغیرهای محیطی تنظیم کنید")

VIP_CHANNEL = "@your_vip_channel"  # یا "https://t.me/+0B-Q8wt-1zJhNDc8"
ADMIN_ID = 7987989849  # آی‌دی عددی خودت

# ---------- Flask برای Render ----------
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Dragonfly 24/7 - ربات زنده‌ست", 200

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    """Flask را در یک پورت جداگانه اجرا کن"""
    # پورت 8080 یا هر پورت دیگه‌ای غیر از 8443 و 10000
    flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

# ---------- منوی اصلی ----------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("📥 عضویت در کانال VIP", callback_data="subscribe")],
        [InlineKeyboardButton("✉ پشتیبانی", callback_data="support")],
    ])

# ---------- دستورات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "به Dragonfly خوش اومدی 🐉\n"
        "سنجاقک بازار آماده شکار کردنه!\n\n"
        "یکی از گزینه‌ها رو انتخاب کن:"
    )
    await update.message.reply_text(text, reply_markup=main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "crypto":
        await query.edit_message_text("🔍 نماد کریپتو رو بنویس (مثل BTC یا BTCUSDT):")
        context.user_data['waiting_for'] = 'crypto_symbol'
        return

    elif query.data == "start":
        await query.edit_message_text("منوی اصلی:", reply_markup=main_menu())
        return

    elif query.data == "subscribe":
        text = (
            "🌟 **عضویت در کانال VIP** 🌟\n\n"
            "با عضویت در کانال VIP:\n"
            "✅ دریافت سیگنال‌های لحظه‌ای\n"
            "✅ تحلیل‌های تخصصی\n"
            "✅ پشتیبانی مستقیم\n\n"
            f"برای عضویت روی لینک کلیک کن:\n{VIP_CHANNEL}"
        )
    elif query.data == "support":
        text = "📞 پشتیبانی: @dragonfly_support\n\nبرای هرگونه سوال یا مشکل در خدمتیم!"
    else:
        text = "به زودی ویژگی‌های بیشتری اضافه میشه... 🚀"

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="start")]])
    await query.edit_message_text(text, reply_markup=back_btn, parse_mode="Markdown")

# ---------- دریافت نماد و تحلیل ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for') == 'crypto_symbol':
        symbol = update.message.text.strip().upper()
        
        # اگر USDT نداشت اضافه کن
        if not symbol.endswith("USDT"):
            symbol += "USDT"
        
        user_id = update.effective_user.id
        
        # اطلاع به کاربر
        await update.message.reply_chat_action("upload_photo")
        processing_msg = await update.message.reply_text("🔮 در حال تحلیل... لطفاً صبر کن")
        
        # بررسی عضویت VIP
        is_vip = False
        
        # ادمین اصلی
        if user_id == ADMIN_ID:
            is_vip = True
            logger.info(f"Admin {user_id} requested analysis for {symbol}")
        else:
            # چک عضویت در کانال
            try:
                # اگر VIP_CHANNEL لینک هست، اول یوزرنیمش رو استخراج کن
                if "t.me/" in VIP_CHANNEL:
                    channel_username = VIP_CHANNEL.split("/")[-1]
                else:
                    channel_username = VIP_CHANNEL.lstrip("@")
                
                member = await context.bot.get_chat_member(f"@{channel_username}", user_id)
                if member.status in ["member", "administrator", "creator"]:
                    is_vip = True
                    logger.info(f"VIP user {user_id} requested analysis for {symbol}")
                else:
                    logger.info(f"Non-VIP user {user_id} requested analysis for {symbol}")
            except Exception as e:
                logger.error(f"Error checking VIP status: {e}")
                is_vip = False
        
        # تحلیل
        try:
            chart_buf, analysis_text = analyze_crypto(symbol, is_vip=is_vip)
            
            if chart_buf:
                # حذف پیام "در حال تحلیل..."
                await processing_msg.delete()
                
                # ارسال عکس و تحلیل
                await update.message.reply_photo(
                    photo=InputFile(chart_buf, filename=f"{symbol}_chart.png"),
                    caption=analysis_text,
                    parse_mode="Markdown"
                )
                
                # دکمه بازگشت
                await update.message.reply_text(
                    "✅ تحلیل کامل شد!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 تحلیل نماد دیگر", callback_data="crypto")],
                        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="start")]
                    ])
                )
            else:
                await update.message.reply_text(
                    "❌ نماد پیدا نشد یا مشکلی در تحلیل پیش اومد.\n"
                    "لطفاً نماد معتبری وارد کن (مثل: BTC, ETH, ...)"
                )
                
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            await update.message.reply_text(
                "⚠️ خطایی در تحلیل رخ داد. لطفاً بعداً تلاش کن یا با پشتیبانی تماس بگیر."
            )
        
        # پاک کردن وضعیت انتظار
        context.user_data['waiting_for'] = None
        return
    
    # اگر پیام معمولی بود
    await update.message.reply_text(
        "سلام! 👋\nبرای شروع از دستور /start استفاده کن.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("شروع /start", callback_data="start")]])
    )

# ---------- خطاها ----------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کن."
            )
        except:
            pass

# ---------- اجرای ربات ----------
def main():
    # شروع Flask در ترد جداگانه
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask server started on port 8080")
    
    # ساخت اپلیکیشن تلگرام
    app = Application.builder().token(TOKEN).build()
    
    # اضافه کردن هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # هندلر خطا
    app.add_error_handler(error_handler)
    
    logger.info("🤖 Dragonfly Bot is starting...")
    
    # اجرای ربات
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()

 























































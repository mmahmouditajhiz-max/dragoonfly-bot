import os
import logging
import threading
import time
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

VIP_CHANNEL = "https://t.me/+0B-Q8wt-1zJhNDc8"   # از لینک استفاده کن بهتره
ADMIN_ID = 7987989849  # آی‌دی عددی خودت

# ---------- Flask برای Render ----------
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Dragonfly 24/7 - ربات زنده‌ست 🐉", 200

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    """Flask را در پورت Render اجرا کن"""
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(
        host="0.0.0.0", 
        port=port, 
        debug=False, 
        use_reloader=False,
        threaded=True
    )

# ---------- منوی اصلی ----------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("📥 عضویت در کانال VIP", callback_data="subscribe")],
        [InlineKeyboardButton("✉️ پشتیبانی", callback_data="support")],
    ])

# ---------- دستورات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "به Dragonfly خوش اومدی 🐉\n"
        "سنجاقک بازار آماده شکار کردنه!\n\n"
        "یکی از گزینه‌ها رو انتخاب کن:"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu())
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "crypto":
        await query.edit_message_text("🔍 نماد کریپتو رو بنویس (مثل BTC یا BTCUSDT):")
        context.user_data['waiting_for'] = 'crypto_symbol'
        return

    elif query.data == "start":
        await start(update, context)
        return

    elif query.data == "subscribe":
        text = (
            "🌟 عضویت در کانال VIP 🌟\n\n"
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
    await query.edit_message_text(text, reply_markup=back_btn)

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
                # برای لینک private
                if "t.me/+" in VIP_CHANNEL:
                    # برای لینک invite خصوصی، باید چک متفاوت باشه
                    # یا از کاربر بخوایید در کانال عضو بشه
                    is_vip = False  # یا منطق چک خودتون
                else:
                    # اگر یوزرنیم معمولیه
                    channel_id = VIP_CHANNEL.replace("@", "").replace("https://t.me/", "")
                    member = await context.bot.get_chat_member(f"@{channel_id}", user_id)
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
                try:
                    await processing_msg.delete()
                except:
                    pass
                
                # ارسال عکس و تحلیل - بدون parse_mode یا با HTML
                await update.message.reply_photo(
                    photo=InputFile(chart_buf, filename=f"{symbol}_chart.png"),
                    caption=analysis_text,
                    parse_mode=None  # ایموجی‌ها بدون markdown بهترن
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
            logger.error(f"Error in analysis: {e}", exc_info=True)
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
    logger.error(f"Update {update} caused error {context.error}", exc_info=True)
    
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
    logger.info(f"Flask server started on port {os.environ.get('PORT', 8080)}")
    
    # کمی صبر کن Flask بالا بیاد
    time.sleep(3)
    
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
    try:
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        raise

if __name__ == "__main__":
    main()

 
























































import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from analyzer import analyze_crypto
from analyzer_tse import TSETSEAnalyzer  # تحلیل بورس ایران

# ---------- Fake Web Server برای Render ----------
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Dragonfly 24/7 - ربات زنده است", 200

@flask_app.route('/health')
def health():
    return {"status": "healthy", "service": "dragonfly_bot"}, 200

def run_flask():
    port = int(os.getenv("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, debug=False)

threading.Thread(target=run_flask, daemon=True).start()

# ---------- تنظیمات ----------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
VIP_CHANNEL = "https://t.me/+0B-Q8wt-1zJhNDc8"   # کانال VIP
TSE_API_KEY = os.getenv("TSE_API_KEY", "کلید_API_خودت")  # از محیطی بخوان

# ---------- منوی اصلی ----------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 تحلیل کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("📉 تحلیل بورس ایران", callback_data="tse")],
        [InlineKeyboardButton("📥 عضویت VIP", callback_data="subscribe")],
        [
            InlineKeyboardButton("🔧 تنظیمات", callback_data="settings"),
            InlineKeyboardButton("ℹ️ راهنما", callback_data="help")
        ]
    ])

def crypto_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏆 BTC/USDT", callback_data="crypto_BTCUSDT")],
        [InlineKeyboardButton("⚡ ETH/USDT", callback_data="crypto_ETHUSDT")],
        [InlineKeyboardButton("🌟 BNB/USDT", callback_data="crypto_BNBUSDT")],
        [InlineKeyboardButton("✏️ نماد دلخواه", callback_data="crypto_custom")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ])

def tse_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛢️ فولاد", callback_data="tse_IRO1FOLD0001")],
        [InlineKeyboardButton("🏦 وبملت", callback_data="tse_IRO1BMLT0001")],
        [InlineKeyboardButton("🚗 خودرو", callback_data="tse_IRO1KHOD0001")],
        [InlineKeyboardButton("⚗️ شبندر", callback_data="tse_IRO1BPAR0001")],
        [InlineKeyboardButton("✏️ نماد دلخواه", callback_data="tse_custom")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ])

# ---------- دستورات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع /start"""
    user = update.effective_user
    welcome_text = (
        f"👋 سلام {user.first_name}!\n"
        "به ربات Dragonfly خوش اومدی 🐉\n\n"
        "🔹 تحلیل لحظه‌ای کریپتو\n"
        "🔹 تحلیل بورس ایران\n"
        "🔹 سیگنال‌های VIP\n\n"
        "یکی از گزینه‌ها رو انتخاب کن:"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=main_menu())
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت کلیک روی دکمه‌ها"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "start":
        await start(update, context)
    
    elif data == "crypto":
        await query.edit_message_text(
            "🪙 تحلیل ارز دیجیتال\n\n"
            "یکی از نمادهای پرطرفدار رو انتخاب کن یا نماد دلخواه وارد کن:",
            reply_markup=crypto_menu()
        )
    
    elif data.startswith("crypto_"):
        if data == "crypto_custom":
            await query.edit_message_text(
                "📝 نماد کریپتو رو بنویس:\n\n"
                "مثال‌ها:\n"
                "• BTCUSDT\n"
                "• ETHUSDT\n"
                "• SOLUSDT\n\n"
                "یا میتونی فقط بزنی: BTC"
            )
            context.user_data['waiting_for'] = 'crypto_symbol'
            context.user_data['last_menu'] = 'crypto'
        else:
            # تحلیل نماد از پیش تعیین شده
            symbol = data.split("_")[1]
            await analyze_crypto_handler(query, context, symbol)
    
    elif data == "tse":
        await query.edit_message_text(
            "🏛️ تحلیل بورس ایران\n\n"
            "یکی از نمادهای پرطرفدار رو انتخاب کن یا نماد دلخواه وارد کن:",
            reply_markup=tse_menu()
        )
    
    elif data.startswith("tse_"):
        if data == "tse_custom":
            await query.edit_message_text(
                "📝 کد نماد بورس رو بنویس:\n\n"
                "مثال‌ها (کد ۱۲ رقمی):\n"
                "• IRO1FOLD0001 (فولاد)\n"
                "• IRO1BMLT0001 (وبملت)\n"
                "• IRO1KHOD0001 (خودرو)\n\n"
                "یا میتونی از کد ۵ رقمی TSETMC استفاده کنی"
            )
            context.user_data['waiting_for'] = 'tse_symbol'
            context.user_data['last_menu'] = 'tse'
        else:
            # تحلیل نماد از پیش تعیین شده
            symbol = data.split("_")[1]
            await analyze_tse_handler(query, context, symbol)
    
    elif data == "subscribe":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 عضویت VIP", url=VIP_CHANNEL)],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
        ])
        await query.edit_message_text(
            "🌟 عضویت در کانال VIP\n\n"
            "با عضویت VIP:\n"
            "✅ دریافت سیگنال‌های دقیق خرید/فروش\n"
            "✅ نقاط ورود و خروج مشخص\n"
            "✅ تحلیل‌های پیشرفته\n"
            "✅ پشتیبانی اختصاصی\n\n"
            "هزینه: ۹۹ تتر / ماه\n"
            "برای خرید اشتراک روی دکمه زیر کلیک کن:",
            reply_markup=keyboard
        )
    
    elif data == "settings":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 تنظیم نوتیفیکیشن", callback_data="notify")],
            [InlineKeyboardButton("⚙️ زبان/زمان‌بندی", callback_data="lang")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
        ])
        await query.edit_message_text(
            "⚙️ تنظیمات ربات\n\n"
            "از طریق این بخش می‌تونی ربات رو شخصی‌سازی کنی:",
            reply_markup=keyboard
        )
    
    elif data == "help":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 آموزش تحلیل", callback_data="tutorial")],
            [InlineKeyboardButton("❓ سوالات متداول", callback_data="faq")],
            [InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/dragonfly_support")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
        ])
        await query.edit_message_text(
            "ℹ️ راهنمای استفاده\n\n"
            "📌 نحوه کار با ربات:\n"
            "1. از منوی اصلی بازار مورد نظرت رو انتخاب کن\n"
            "2. نماد رو وارد کن یا از پیش‌تعیین‌شده‌ها انتخاب کن\n"
            "3. تحلیل کامل رو دریافت کن\n\n"
            "💡 نکات:\n"
            "• برای نمادهای کریپتو می‌تونی USDT ننویسی\n"
            "• تحلیل بورس کمی زمان می‌بره (وابسته به API)\n"
            "• کاربران VIP سیگنال کامل دریافت می‌کنن",
            reply_markup=keyboard
        )
    
    elif data in ["notify", "lang", "tutorial", "faq"]:
        # پیاده‌سازی ساده برای حال حاضر
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]])
        messages = {
            "notify": "🔔 تنظیم نوتیفیکیشن به زودی اضافه می‌شه...",
            "lang": "🌍 زبان فارسی پشتیبانی می‌شه. زبان انگلیسی به زودی...",
            "tutorial": "📚 آموزش‌های تحلیل به زودی در کانال قرار می‌گیره...",
            "faq": "❓ سوالات متداول در حال آماده‌سازی..."
        }
        await query.edit_message_text(messages.get(data, "به زودی..."), reply_markup=keyboard)

async def check_vip_status(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """بررسی وضعیت VIP بودن کاربر"""
    ADMIN_ID = 7987989849  # آی‌دی ادمین اصلی
    
    # ادمین همیشه VIP است
    if user_id == ADMIN_ID:
        return True
    
    # بررسی عضویت در کانال VIP
    try:
        member = await context.bot.get_chat_member(VIP_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.warning(f"خطا در بررسی عضویت VIP برای کاربر {user_id}: {e}")
        return False

async def analyze_crypto_handler(query, context, symbol: str):
    """تحلیل ارز دیجیتال"""
    user_id = query.from_user.id
    await query.edit_message_text(f"🔍 در حال تحلیل {symbol}...")
    
    # بررسی وضعیت VIP
    is_vip = await check_vip_status(user_id, context)
    
    # اجرای تحلیل
    try:
        chart_buf, analysis_text = analyze_crypto(symbol, is_vip=is_vip)
        
        if chart_buf:
            # ارسال نمودار
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=InputFile(chart_buf, filename=f"{symbol}_chart.png"),
                caption=analysis_text[:1024]  # محدودیت تلگرام
            )
            
            # ارسال بقیه تحلیل اگر طولانی بود
            if len(analysis_text) > 1024:
                remaining_text = analysis_text[1024:]
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=remaining_text[:4096]
                )
            
            # دکمه بازگشت
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تحلیل دیگر", callback_data="crypto")],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="start")]
            ])
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="✅ تحلیل کامل شد!",
                reply_markup=keyboard
            )
        else:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("♻️ دوباره امتحان کن", callback_data="crypto")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
            ])
            await query.edit_message_text(
                "❌ خطا در تحلیل!\n\n"
                "ممکنه:\n"
                "• نماد اشتباه باشه\n"
                "• مشکل شبکه باشه\n"
                "• API محدود شده باشه",
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"خطا در تحلیل کریپتو {symbol}: {e}")
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]])
        await query.edit_message_text(
            f"⚠️ خطای سیستمی:\n{str(e)[:200]}",
            reply_markup=keyboard
        )

async def analyze_tse_handler(query, context, symbol: str):
    """تحلیل بورس ایران"""
    user_id = query.from_user.id
    await query.edit_message_text(f"🏛️ در حال تحلیل {symbol}...\n(ممکنه 10-20 ثانیه طول بکشه)")
    
    # بررسی وضعیت VIP
    is_vip = await check_vip_status(user_id, context)
    
    # اجرای تحلیل
    try:
        analyzer = TSETSEAnalyzer(api_key=TSE_API_KEY)
        chart_buf, analysis_text = analyzer.analyze(symbol, is_vip=is_vip)
        
        if chart_buf and analysis_text:
            # ارسال نمودار
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=InputFile(chart_buf, filename=f"{symbol}_chart.png"),
                caption=analysis_text[:1024]
            )
            
            # ارسال بقیه تحلیل اگر طولانی بود
            if len(analysis_text) > 1024:
                remaining_text = analysis_text[1024:]
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=remaining_text[:4096]
                )
            
            # دکمه بازگشت
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏛️ تحلیل بورس دیگر", callback_data="tse")],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="start")]
            ])
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="✅ تحلیل بورس کامل شد!",
                reply_markup=keyboard
            )
        else:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("♻️ دوباره امتحان کن", callback_data="tse")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
            ])
            await query.edit_message_text(
                "❌ خطا در تحلیل بورس!\n\n"
                "ممکنه:\n"
                "• کد نماد اشتباه باشه\n"
                "• API کلید نداشته باشه\n"
                "• بازار بسته باشه",
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"خطا در تحلیل بورس {symbol}: {e}")
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]])
        await query.edit_message_text(
            f"⚠️ خطا در تحلیل بورس:\n{str(e)[:200]}",
            reply_markup=keyboard
        )

# ---------- دریافت نماد از کاربر ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پیام‌های متنی کاربر"""
    text = update.message.text.strip().upper()
    waiting_for = context.user_data.get('waiting_for')
    
    if waiting_for == 'crypto_symbol':
        # پردازش نماد کریپتو
        symbol = text
        if not symbol.endswith("USDT"):
            symbol += "USDT"
        
        await update.message.reply_chat_action("upload_photo")
        await update.message.reply_text(f"🔍 در حال تحلیل {symbol}...")
        
        # بررسی VIP بودن
        user_id = update.effective_user.id
        is_vip = await check_vip_status(user_id, context)
        
        # تحلیل
        try:
            chart_buf, analysis_text = analyze_crypto(symbol, is_vip=is_vip)
            
            if chart_buf:
                await update.message.reply_photo(
                    photo=InputFile(chart_buf, filename="chart.png"),
                    caption=analysis_text
                )
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 تحلیل دیگر", callback_data="crypto")],
                    [InlineKeyboardButton("🏠 منوی اصلی", callback_data="start")]
                ])
                await update.message.reply_text(
                    "✅ تحلیل کامل شد!",
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text(
                    "❌ نماد اشتباهه یا داده نداره!\n"
                    "دوباره امتحان کن یا از منو انتخاب کن",
                    reply_markup=crypto_menu()
                )
                
        except Exception as e:
            logger.error(f"خطا در تحلیل کریپتو {symbol}: {e}")
            await update.message.reply_text(
                f"⚠️ خطا در تحلیل: {str(e)[:100]}",
                reply_markup=crypto_menu()
            )
        
        context.user_data['waiting_for'] = None
    
    elif waiting_for == 'tse_symbol':
        # پردازش نماد بورس
        symbol = text
        
        await update.message.reply_chat_action("upload_photo")
        await update.message.reply_text(f"🏛️ در حال تحلیل {symbol}...\n(لطفا صبر کن)")
        
        # بررسی VIP بودن
        user_id = update.effective_user.id
        is_vip = await check_vip_status(user_id, context)
        
        # تحلیل
        try:
            analyzer = TSETSEAnalyzer(api_key=TSE_API_KEY)
            chart_buf, analysis_text = analyzer.analyze(symbol, is_vip=is_vip)
            
            if chart_buf and analysis_text:
                await update.message.reply_photo(
                    photo=InputFile(chart_buf, filename="tse_chart.png"),
                    caption=analysis_text
                )
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏛️ تحلیل دیگر", callback_data="tse")],
                    [InlineKeyboardButton("🏠 منوی اصلی", callback_data="start")]
                ])
                await update.message.reply_text(
                    "✅ تحلیل بورس کامل شد!",
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text(
                    "❌ خطا در تحلیل بورس!\n"
                    "مطمئن شو کد نماد درسته\n"
                    "مثال: IRO1FOLD0001",
                    reply_markup=tse_menu()
                )
                
        except Exception as e:
            logger.error(f"خطا در تحلیل بورس {symbol}: {e}")
            await update.message.reply_text(
                f"⚠️ خطا در تحلیل بورس: {str(e)[:100]}",
                reply_markup=tse_menu()
            )
        
        context.user_data['waiting_for'] = None
    
    else:
        # پیام معمولی
        await update.message.reply_text(
            "👋 از منوی اصلی استفاده کن\n"
            "یا دستور /start رو بزن",
            reply_markup=main_menu()
        )

# ---------- خطای کلی ----------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت خطاهای ربات"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ متأسفانه خطایی رخ داد!\n"
                "لطفا دوباره امتحان کن یا /start رو بزن",
                reply_markup=main_menu()
            )
        except:
            pass

# ---------- اجرای ربات ----------
def main():
    """تابع اصلی اجرای ربات"""
    if not TOKEN:
        logger.error("⚠️ TELEGRAM_TOKEN پیدا نشد!")
        logger.error("لطفا در محیط (Environment) تنظیم کن:")
        logger.error("export TELEGRAM_TOKEN='توکن_ربات'")
        return
    
    # ایجاد برنامه
    app = Application.builder().token(TOKEN).build()
    
    # افزودن هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # هندلر خطا
    app.add_error_handler(error_handler)
    
    # راه‌اندازی
    logger.info("🚀 ربات Dragonfly در حال راه‌اندازی...")
    logger.info(f"📢 کانال VIP: {VIP_CHANNEL}")
    
    if TSE_API_KEY == "کلید_API_خودت":
        logger.warning("⚠️ کلید API بورس تنظیم نشده! تحلیل بورس کار نمی‌کنه")
    
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()
 
















































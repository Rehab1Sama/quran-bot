from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import json

# --- القوائم ---
main_menu = [
    [InlineKeyboardButton("📖 قرآن", callback_data="quran")],
    [InlineKeyboardButton("🤲 دعاء", callback_data="dua")],
    [InlineKeyboardButton("📚 كتاب", callback_data="book")]
]

quran_menu = [
    [InlineKeyboardButton("🧮 حدد نصابك", callback_data="official")],
    [InlineKeyboardButton("🎧 تلاوة مختارة", callback_data="private")],
    [InlineKeyboardButton("⬅ رجوع", callback_data="main")]
]

official_readers = [
    [InlineKeyboardButton("عبدالباسط", callback_data="reader_abd")],
    [InlineKeyboardButton("الحصري", callback_data="reader_husary")],
    [InlineKeyboardButton("⬅ رجوع", callback_data="quran")]
]

private_readers = []  # سيتم ملؤه من private_data.json

# --- تحميل التلاوات الخاصة ---
if os.path.exists("private_data.json"):
    with open("private_data.json", "r", encoding="utf-8") as f:
        private_data = json.load(f)
        for reader in private_data.keys():
            private_readers.append([InlineKeyboardButton(reader, callback_data=f"private_{reader}")])
        private_readers.append([InlineKeyboardButton("⬅ رجوع", callback_data="quran")])
else:
    private_data = {}

# --- أوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(main_menu)
    await update.message.reply_text("مرحبًا! اختر القسم:", reply_markup=keyboard)

# --- التعامل مع الأزرار ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main":
        await query.edit_message_text("اختر القسم:", reply_markup=InlineKeyboardMarkup(main_menu))

    elif data == "quran":
        await query.edit_message_text("اختر نوع القرآن:", reply_markup=InlineKeyboardMarkup(quran_menu))

    elif data == "official":
        await query.edit_message_text("اختر القارئ الرسمي:", reply_markup=InlineKeyboardMarkup(official_readers))

    elif data == "private":
        await query.edit_message_text("اختر قارئك الخاص:", reply_markup=InlineKeyboardMarkup(private_readers))

    elif data.startswith("reader_") or data.startswith("private_"):
        reader_name = data.replace("reader_", "").replace("private_", "")
        await query.edit_message_text(f"تم اختيار القارئ: {reader_name}\n(ستتم إضافة خيارات الجزء والسورة لاحقًا)")

    elif data == "dua":
        await query.edit_message_text("قسم الدعاء (تطوير لاحقًا)")

    elif data == "book":
        await query.edit_message_text("قسم الكتب (تطوير لاحقًا)")

# --- التطبيق ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # على Render نضع توكن البوت هنا
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()

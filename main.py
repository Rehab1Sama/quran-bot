from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
import json

# --- بياناتك ---
OWNER_ID = 6993426656  # فقط أنت من يمكنه إرسال التلاوات

# --- مسارات التخزين ---
PRIVATE_DIR = "private_recitations"
PRIVATE_JSON = "private_data.json"

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

# --- تحميل التلاوات الخاصة ---
private_readers = []
if os.path.exists(PRIVATE_JSON):
    with open(PRIVATE_JSON, "r", encoding="utf-8") as f:
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
        # إعادة تحميل private_readers من JSON لضمان تحديثها
        if os.path.exists(PRIVATE_JSON):
            with open(PRIVATE_JSON, "r", encoding="utf-8") as f:
                private_data = json.load(f)
            private_readers.clear()
            for reader in private_data.keys():
                private_readers.append([InlineKeyboardButton(reader, callback_data=f"private_{reader}")])
            private_readers.append([InlineKeyboardButton("⬅ رجوع", callback_data="quran")])
        await query.edit_message_text("اختر قارئك الخاص:", reply_markup=InlineKeyboardMarkup(private_readers))

    elif data.startswith("reader_") or data.startswith("private_"):
        reader_name = data.replace("reader_", "").replace("private_", "")
        await query.edit_message_text(f"تم اختيار القارئ: {reader_name}\n(ستتم إضافة خيارات الجزء والسورة لاحقًا)")

    elif data == "dua":
        await query.edit_message_text("قسم الدعاء (تطوير لاحقًا)")

    elif data == "book":
        await query.edit_message_text("قسم الكتب (تطوير لاحقًا)")

# --- استقبال تلاواتك الخاصة فقط ---
async def handle_my_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if user.id != OWNER_ID:
        await update.message.reply_text("⚠ فقط صاحب البوت يمكن إضافة التلاوات.")
        return

    audio = update.message.audio or update.message.document
    if audio:
        caption = update.message.caption or "Unknown"
        reader = caption.strip()

        # إنشاء المجلد إذا لم يكن موجود
        reader_dir = os.path.join(PRIVATE_DIR, reader)
        os.makedirs(reader_dir, exist_ok=True)

        # حفظ الملف
        file_path = os.path.join(reader_dir, audio.file_name)
        file = await audio.get_file()
        await file.download_to_drive(file_path)

        # تحديث JSON
        if os.path.exists(PRIVATE_JSON):
            with open(PRIVATE_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        if reader not in data:
            data[reader] = []

        data[reader].append({"title": audio.file_name, "file": file_path})

        with open(PRIVATE_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        await update.message.reply_text(f"✅ تم حفظ التلاوة لـ {reader}")

# --- التطبيق ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.AUDIO | filters.Document.ALL, handle_my_audio))

app.run_polling()

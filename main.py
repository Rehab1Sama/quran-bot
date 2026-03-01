import os
import json
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAudio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ---------------- Google Drive Setup ----------------
creds_data = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
SCOPES = ['https://www.googleapis.com/auth/drive.file']
credentials = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)
DRIVE_FOLDER_NAME = "QuranBotRecitations"

def get_or_create_folder(folder_name, parent_id=None):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query = f"'{parent_id}' in parents and " + query
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id:
        file_metadata['parents'] = [parent_id]
    folder = drive_service.files().create(body=file_metadata, fields='id').execute()
    return folder['id']

MAIN_FOLDER_ID = get_or_create_folder(DRIVE_FOLDER_NAME)

def upload_to_drive(file_path, reciter_name):
    reciter_folder_id = get_or_create_folder(reciter_name, parent_id=MAIN_FOLDER_ID)
    media = MediaFileUpload(file_path, mimetype='audio/mpeg')
    drive_service.files().create(body={'name': os.path.basename(file_path),
                                       'parents':[reciter_folder_id]},
                                 media_body=media).execute()

def list_reciter_files(reciter_name):
    reciter_folder_id = get_or_create_folder(reciter_name, parent_id=MAIN_FOLDER_ID)
    results = drive_service.files().list(q=f"'{reciter_folder_id}' in parents", fields="files(id, name)").execute()
    return results.get('files', [])

def download_file(file_id):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh

# ---------------- Telegram Bot ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6993426656

# ---------------- Data ----------------
# 114 سورة كاملة
SURAS = ["الفاتحة","البقرة","آل عمران","النساء","المائدة","الأنعام","الأعراف","الأنفال","التوبة","يونس",
"هود","يوسف","الرعد","ابراهيم","الحجر","النحل","الإسراء","الكهف","مريم","طه",
"الأنبياء","الحج","المؤمنون","النّور","الفرقان","الشعراء","النمل","القصص","العنكبوت","الروم",
"لقمان","السجدة","الأحزاب","سبأ","فاطر","يس","الصافات","ص","الزمر","غافر",
"فصلت","الشورى","الزخرف","الدخان","الجاثية","الأحقاف","محمد","الفتح","الحجرات","ق",
"الذاريات","الطور","النجم","القمر","الرحمن","الواقعة","الحشر","الممتحنة","الصف","الجمعة",
"المنافقون","التغابن","الطلاق","التحريم","الملك","القلم","الحاقة","المعارج","نوح","الجن",
"المزمل","المدثر","القيامة","الإنسان","المرسلات","النبأ","النازعات","عبس","التكوير","الإنفطار",
"المطففين","الإنشقاق","البروج","الطارق","الأعلى","الغاشية","الفجر","البلد","الشمس","الليل",
"الضحى","الشرح","التين","العلق","القدر","البينة","الزلزلة","العاديات","القارعة","التكاثر",
"العصر","الهمزة","الفيل","قريش","الماعون","الكوثر","الكافرون","النصر","المسد","الإخلاص",
"الفلق","الناس"]

# أكثر من 20 قارئ رسمي
OFFICIAL_RECITERS = ["Alafasy","AbdulBaset","MaherMuaiqly","Sudais","Minshawi",
                     "Husary","Shuraim","Ghamdi","Alajmi","Alhussary","Alkuwaiti",
                     "Alqarni","Alhussary_Murattal","Alafasy_HQ","Basfar","Hani_Rifai",
                     "Hani_Shukri","Saleh_AlTalib","Abdullah_AlAmri","Saad_AlGhamdi"]

# ---------------- Command / Start ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📖 قرآن ▼", callback_data="dropdown_quran")],
        [InlineKeyboardButton("🤲 دعاء", callback_data="dua")],
        [InlineKeyboardButton("📚 كتاب", callback_data="book")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر من القائمة:", reply_markup=reply_markup)

# ---------------- Dropdown محاكاة ----------------
async def dropdown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "dropdown_quran":
        keyboard = []
        row = []
        for i, sura in enumerate(SURAS, start=1):
            row.append(InlineKeyboardButton(sura, callback_data=f"sura_{i}"))
            if i % 3 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        # إضافة خيار تلاواتك الخاصة
        keyboard.append([InlineKeyboardButton("🎙 تلاواتي الخاصة", callback_data="my_recitations")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("اختر السورة أو تلاواتك:", reply_markup=reply_markup)

# ---------------- اختيار السورة ----------------
async def sura_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sura_index = int(query.data.split("_")[1]) - 1
    sura_name = SURAS[sura_index]
    keyboard = [[InlineKeyboardButton(r, callback_data=f"reciter_{r}_{sura_name}")] for r in OFFICIAL_RECITERS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"اختر القارئ للسورة {sura_name}:", reply_markup=reply_markup)

# ---------------- اختيار القارئ ----------------
async def reciter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    reciter_name = parts[1]
    sura_name = "_".join(parts[2:])
    await query.edit_message_text(f"جارٍ تجهيز التلاوة للسورة {sura_name} بصوت {reciter_name}... 🔊")

# ---------------- تلاواتك الخاصة ----------------
async def my_recitations_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    results = drive_service.files().list(q=f"'{MAIN_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder'",
                                         fields="files(id, name)").execute()
    reciters = [f['name'] for f in results.get('files', [])]
    if not reciters:
        await query.edit_message_text("لا توجد تلاوات خاصة لديك حتى الآن.")
        return
    keyboard = [[InlineKeyboardButton(r, callback_data=f"myreciter_{r}")] for r in reciters]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("اختر القارئ من تلاواتك الخاصة:", reply_markup=reply_markup)

async def send_my_reciter_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    reciter_name = query.data.split("_")[1]
    files = list_reciter_files(reciter_name)
    if not files:
        await query.edit_message_text("لا توجد ملفات لهذا القارئ.")
        return
    media_group = []
    for f in files:
        file_io = download_file(f['id'])
        media_group.append(InputMediaAudio(file_io, filename=f['name']))
    await query.edit_message_text(f"جارٍ إرسال التلاوات الخاصة بـ {reciter_name}...")
    await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)

# ---------------- استقبال التلاوات الخاصة ----------------
async def handle_private_recitation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
        return
    if update.message.audio:
        audio_file = update.message.audio.get_file()
        file_path = f"temp_{audio_file.file_id}.mp3"
        await audio_file.download_to_drive(file_path)
        reciter_name = update.message.caption if update.message.caption else "Unknown"
        upload_to_drive(file_path, reciter_name)
        os.remove(file_path)
        await update.message.reply_text(f"تم رفع التلاوة للقارئ: {reciter_name}")

# ---------------- Main ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(dropdown_handler, pattern="^dropdown_quran$"))
app.add_handler(CallbackQueryHandler(sura_handler, pattern="^sura_"))
app.add_handler(CallbackQueryHandler(reciter_handler, pattern="^reciter_"))
app.add_handler(CallbackQueryHandler(my_recitations_handler, pattern="^my_recitations$"))
app.add_handler(CallbackQueryHandler(send_my_reciter_files, pattern="^myreciter_"))
app.add_handler(MessageHandler(filters.AUDIO, handle_private_recitation))
app.run_polling()

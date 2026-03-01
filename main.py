import os
import json
import io
import requests
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ---------------- 1. إعدادات قوقل درايف ----------------
creds_json = os.getenv("GOOGLE_CREDENTIALS")
creds_data = json.loads(creds_json)
SCOPES = ['https://www.googleapis.com/auth/drive.file']
credentials = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)
DRIVE_FOLDER_NAME = "QuranBotRecitations"

def get_or_create_folder(folder_name, parent_id=None):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id: query = f"'{parent_id}' in parents and " + query
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    if files: return files[0]['id']
    file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id: file_metadata['parents'] = [parent_id]
    folder = drive_service.files().create(body=file_metadata, fields='id').execute()
    return folder['id']

MAIN_FOLDER_ID = get_or_create_folder(DRIVE_FOLDER_NAME)

def upload_to_drive(file_path, reciter_name):
    reciter_folder_id = get_or_create_folder(reciter_name, parent_id=MAIN_FOLDER_ID)
    media = MediaFileUpload(file_path, mimetype='audio/mpeg')
    drive_service.files().create(
        body={'name': os.path.basename(file_path), 'parents': [reciter_folder_id]},
        media_body=media
    ).execute()

# ---------------- 2. البيانات (114 سورة و 20+ قارئ) ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6993426656 

SURAS = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس",
    "هود", "يوسف", "الرعد", "إبراهيم", "الحجر", "النحل", "الإسراء", "الكهف", "مريم", "طه",
    "الأنبياء", "الحج", "المؤمنون", "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص", "الزمر", "غافر",
    "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
    "الذاريات", "الطور", "النجم", "القمر", "الرحمن", "الواقعة", "الحشر", "الممتحنة", "الصف", "الجمعة",
    "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك", "القلم", "الحاقة", "المعارج", "نوح", "الجن",
    "المزمل", "المدثر", "القيامة", "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس", "التكوير", "الانفطار",
    "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد", "الشمس", "الليل",
    "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة", "الزلزلة", "العاديات", "القارعة", "التكاثر",
    "العصر", "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون", "النصر", "المسد", "الإخلاص",
    "الفلق", "الناس"
]

OFFICIAL_RECITERS = {
    "ماهر المعيقلي": "ar.mahermuaiqly", "مشاري العفاسي": "ar.alafasy", "عبدالباسط": "ar.abdulsamad",
    "المنشاوي": "ar.minshawi", "ياسر الدوسري": "ar.yasseradosari", "الحصري": "ar.husary",
    "السديس": "ar.as-sudais", "الشريم": "ar.saoodshuraym", "ناصر القطامي": "ar.nasser_alqatami",
    "فارس عباد": "ar.faresabbad", "أحمد العجمي": "ar.ahmedajamy", "سعد الغامدي": "ar.saad_al_ghamidi",
    "أبو بكر الشاطري": "ar.abu_bakr_ash-shatree", "إدريس أبكر": "ar.idrees_abkar", "خالد القحطاني": "ar.khalid_al_kahtanee",
    "علي الحذيفي": "ar.al-hudhaifi", "محمد اللحيدان": "ar.mohammad_al_lohaidan", "صلاح البدير": "ar.salah_al_budair",
    "عبدالله المطرود": "ar.abdullah_matroud", "محمد الطبلاوي": "ar.mohammad_al_tablawy", "هاني الرفاعي": "ar.hani_ar-rifai"
}

# ---------------- 3. الدوال البرمجية ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📖 تلاوات المصحف كامل (١١٤ سورة)", callback_data="off_list_0")],
        [InlineKeyboardButton("🎙 تلاوات منتقاة", callback_data="private_menu")]
    ]
    await update.message.reply_text("✨ أهلًا بك فِي أَثَــر\n\nيمكنكِ اختيار السور والقراء، أو رفع تلاواتكِ الخاصة مباشرة.", reply_markup=InlineKeyboardMarkup(keyboard))

async def official_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # تقسيم السور لصفحات إذا لزم الأمر، هنا سنعرضها كاملة منظمة
    keyboard = []
    for i in range(0, len(SURAS), 3):
        row = [InlineKeyboardButton(SURAS[j], callback_data=f"select_sura_{j+1}") for j in range(i, min(i+3, len(SURAS)))]
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")])
    await query.edit_message_text("يرجى اختيار السورة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def sura_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sura_id = query.data.split("_")[2]
    keyboard = []
    reciter_names = list(OFFICIAL_RECITERS.keys())
    for i in range(0, len(reciter_names), 2):
        row = [InlineKeyboardButton(reciter_names[j], callback_data=f"play_{sura_id}_{OFFICIAL_RECITERS[reciter_names[j]]}") for j in range(i, min(i+2, len(reciter_names)))]
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ رجوع للسور", callback_data="off_list_0")])
    await query.edit_message_text(f"اختر القارئ لسورة {SURAS[int(sura_id)-1]}:", reply_markup=InlineKeyboardMarkup(keyboard))

async def play_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري جلب التلاوة... ⏳")
    _, sura_id, rec_id = query.data.split("_")
    url = f"https://api.alquran.cloud/v1/surah/{sura_id}/{rec_id}"
    try:
        res = requests.get(url).json()
        audio_url = res['data']['ayahs'][0]['audio']
        await context.bot.send_audio(chat_id=query.message.chat_id, audio=audio_url, caption=f"✅ سورة {SURAS[int(sura_id)-1]}")
    except: await query.message.reply_text("❌ حدث خطأ")

async def handle_admin_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID: return
    if update.message.audio:
        audio = update.message.audio
        name = update.message.caption if update.message.caption else "قارئ غير معروف"
        msg = await update.message.reply_text("⏳ جاري الرفع لدرايف...")
        f = await audio.get_file()
        path = f"temp_{audio.file_id}.mp3"
        await f.download_to_drive(path)
        upload_to_drive(path, name)
        os.remove(path)
        await msg.edit_text(f"✅ تم الرفع للقارئ: {name}")

# --- قوقل درايف للمستخدمين ---
async def private_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    res = drive_service.files().list(q=f"'{MAIN_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder'", fields="files(id, name)").execute()
    folders = res.get('files', [])
    if not folders:
        await query.edit_message_text("لا يوجد تلاوات خاصة حالياً.")
        return
    keyboard = [[InlineKeyboardButton(f['name'], callback_data=f"drv_{f['id']}")] for f in folders]
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")])
    await query.edit_message_text("تلاوات منتقاة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_drive_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري التحميل... 📥")
    fid = query.data.split("_")[1]
    res = drive_service.files().list(q=f"'{fid}' in parents", fields="files(id, name)").execute()
    for f in res.get('files', []):
        req = drive_service.files().get_media(fileId=f['id'])
        fh = io.BytesIO(); downloader = MediaIoBaseDownload(fh, req)
        done = False
        while not done: _, done = downloader.next_chunk()
        fh.seek(0)
        await context.bot.send_audio(chat_id=query.message.chat_id, audio=fh, filename=f['name'])

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("📖 المنصات الرسمية", callback_data="off_list_0")], [InlineKeyboardButton("🎙 نصاب محدد", callback_data="private_menu")]]
    await query.edit_message_text("اختر من القائمة:", reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------- 4. الخادم والتشغيل ----------------
def run_port():
    with TCPServer(("", 8080), SimpleHTTPRequestHandler) as httpd: httpd.serve_forever()

threading.Thread(target=run_port, daemon=True).start()

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(official_list_handler, pattern="^off_list_"))
app.add_handler(CallbackQueryHandler(sura_selected, pattern="^select_sura_"))
app.add_handler(CallbackQueryHandler(play_audio, pattern="^play_"))
app.add_handler(CallbackQueryHandler(private_menu, pattern="^private_menu$"))
app.add_handler(CallbackQueryHandler(send_drive_audio, pattern="^drv_"))
app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_start$"))
app.add_handler(MessageHandler(filters.AUDIO, handle_admin_upload))

print("البوت يعمل بنجاح!")
app.run_polling()

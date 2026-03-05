import telebot
import json
import os
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaFileUpload
import tempfile

# ---------------------------
# إعداد البوت
# ---------------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("ضع TELEGRAM_BOT_TOKEN في Environment Variables")
bot = telebot.TeleBot(TOKEN)

# ---------------------------
# إعداد Google Drive
# ---------------------------
if not os.getenv("GOOGLE_CREDENTIALS"):
    raise ValueError("ضع GOOGLE_CREDENTIALS في Environment Variables")

creds = Credentials.from_service_account_info(json.loads(os.getenv("GOOGLE_CREDENTIALS")))
drive_service = build('drive', 'v3', credentials=creds)

# هنا ضع ID المجلد في Drive حيث ستُرفع التلاوات
DRIVE_FOLDER_ID = "ضع_هنا_folder_id"

# ---------------------------
# تحميل الأذكار
# ---------------------------
with open("adhkar.json", "r", encoding="utf-8") as f:
    adhkar = json.load(f)

# ---------------------------
# تخزين تلاوات المستخدمين
# الصيغة: {chat_id: [{"name": "تلاوة 1", "url": "..."}]}
user_recitations = {}

# ---------------------------
# تخزين تقدم المستخدم للأذكار
# ---------------------------
user_positions = {}

# ---------------------------
# الواجهة الرئيسية
# ---------------------------
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📖 القرآن", "🌿 الأذكار")
    markup.row("🔢 عداد التسبيح", "⚙️ الإعدادات")
    markup.row("🎵 تلاوات مختارة")
    bot.send_message(message.chat.id, "أهلاً بك في بوت أَثَــر ✨", reply_markup=markup)

# ---------------------------
# الأذكار
# ---------------------------
@bot.message_handler(func=lambda m: m.text == "🌿 الأذكار")
def start_adhkar(message):
    chat_id = message.chat.id
    user_positions[chat_id] = {"section": "الصباح", "index": 0}
    send_next_adhkar(chat_id)

def send_next_adhkar(chat_id):
    pos = user_positions[chat_id]
    section = pos["section"]
    index = pos["index"]
    if index < len(adhkar[section]):
        text = adhkar[section][index]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("التالي ➡️", callback_data="next_adhkar"))
        bot.send_message(chat_id, text, reply_markup=markup)
        pos["index"] += 1
    else:
        bot.send_message(chat_id, "✅ انتهت الأذكار لهذا القسم 🌸")

@bot.callback_query_handler(func=lambda c: c.data == "next_adhkar")
def handle_next_adhkar(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    send_next_adhkar(call.message.chat.id)

# ---------------------------
# تلاوات مختارة (من Google Drive)
# ---------------------------
@bot.message_handler(func=lambda m: m.text == "🎵 تلاوات مختارة")
def show_user_recitations(message):
    chat_id = message.chat.id
    recs = user_recitations.get(chat_id, [])
    if not recs:
        bot.send_message(chat_id, "لا توجد تلاوات محفوظة بعد.")
        return
    markup = InlineKeyboardMarkup()
    for r in recs:
        markup.add(InlineKeyboardButton(r["name"], callback_data=f"user_rec_{r['id']}"))
    bot.send_message(chat_id, "اختر التلاوة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("user_rec_"))
def send_user_rec(call):
    chat_id = call.message.chat.id
    rec_id = call.data.replace("user_rec_", "")
    rec = next((r for r in user_recitations[chat_id] if r['id'] == rec_id), None)
    if rec:
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        bot.send_audio(chat_id, rec['url'])

# ---------------------------
# رفع تلاوات جديدة من المستخدم على Google Drive
# ---------------------------
@bot.message_handler(content_types=['audio'])
def save_user_rec(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.audio.file_id)
    file_path = file_info.file_path
    file_name = message.audio.file_name or f"تلاوة {len(user_recitations.get(chat_id, []))+1}"

    # تحميل مؤقت للملف
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    downloaded = bot.download_file(file_path)
    temp_file.write(downloaded)
    temp_file.close()

    # رفع الملف على Google Drive
    file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(temp_file.name, mimetype='audio/mpeg')
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = uploaded_file.get('id')
    share_link = f"https://drive.google.com/uc?id={file_id}&export=download"

    # تخزين رابط المشاركة في الذاكرة
    user_recitations.setdefault(chat_id, []).append({"name": file_name, "url": share_link, "id": file_id})

    bot.send_message(chat_id, f"تم حفظ تلاوتك: {file_name} ✅")

# ---------------------------
# لتشغيل البوت بثبات
# ---------------------------
bot.infinity_polling()

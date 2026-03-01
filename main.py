import os
import telebot
import requests
from telebot import types
import http.server
import socketserver
import threading

# جلب التوكن من إعدادات Render
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# قائمة القراء المعرفين في API المنصة العالمية
RECITERS = {
    "المنشاوي (المجود)": "ar.minshawi",
    "الحصري": "ar.husary",
    "عبدالباسط (المجود)": "ar.abdulsamad",
    "مشاري العفاسي": "ar.alafasy",
    "ياسر الدوسري": "ar.yasseradosari",
    "ماهر المعيقلي": "ar.mahermuaiqly",
    "ناصر القطامي": "ar.nasser_alqatami",
    "سعود الشريم": "ar.saoodshuraym",
    "عبدالرحمن السديس": "ar.as-sudais",
    "أحمد العجمي": "ar.ahmedajamy",
    "فارس عباد": "ar.faresabbad",
    "سعد الغامدي": "ar.saad_al_ghamidi",
    "أبو بكر الشاطري": "ar.abu_bakr_ash-shatree"
}

user_data = {} # لتخزين خيارات المستخدم مؤقتاً

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=name, callback_data=f"reciter_{id}") for name, id in RECITERS.items()]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "✨ مرحباً بكِ في بوت القرآن الكريم\n\nالرجاء اختيار القارئ من القائمة التالية:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reciter_'))
def handle_reciter_choice(call):
    reciter_id = call.data.replace('reciter_', '')
    user_data[call.message.chat.id] = {'reciter': reciter_id}
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "تم اختيار القارئ بنجاح ✅\n\nالآن أرسلي السورة والآية بهذا الشكل (مثلاً 2:255):")
    bot.register_next_step_handler(msg, process_quran_request)

def process_quran_request(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "الرجاء البدء بـ /start أولاً.")
        return

    try:
        surah, ayah = message.text.split(':')
        reciter = user_data[chat_id]['reciter']
        
        # طلب الرابط من API المنصة العالمية
        url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/{reciter}"
        response = requests.get(url)
        
        if response.status_code == 200:
            audio_url = response.json()['data']['audio']
            bot.send_audio(chat_id, audio_url, caption=f"📖 سورة رقم {surah} - آية رقم {ayah}\nتم جلبها من المنصة الرسمية.")
        else:
            bot.send_message(chat_id, "عذراً، لم أجد هذه الآية. تأكدي من الأرقام (السور من 1-114).")
    except:
        bot.send_message(chat_id, "يرجى إرسال الطلب بشكل صحيح، مثال: 1:5")

# كود الخادم الوهمي لـ Render لضمان بقاء البوت Live
def start_server():
    PORT = 8080
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=start_server, daemon=True).start()

bot.polling(none_stop=True)

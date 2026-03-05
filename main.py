import telebot
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("ضع TELEGRAM_BOT_TOKEN في Environment Variables")

bot = telebot.TeleBot(TOKEN)

# تحميل JSON القراء والأذكار
with open("reciters.json","r",encoding="utf-8") as f:
    reciters_data = json.load(f)["قائمة_القراء"]

with open("adhkar.json","r",encoding="utf-8") as f:
    adhkar = json.load(f)

# تلاوات المستخدمين الخاصة
user_recitations = {}
user_positions = {}

# 🌿 الواجهة الرئيسية
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📖 القرآن", "🌿 الأذكار")
    markup.row("🔢 عداد التسبيح", "⚙️ الإعدادات")
    markup.row("🎵 تلاوات مختارة")
    bot.send_message(message.chat.id, "أهلاً بك في بوت أَثَــر ✨", reply_markup=markup)

# 🌿 الأذكار تفاعلي
@bot.message_handler(func=lambda m: m.text == "🌿 الأذكار")
def start_adhkar(message):
    chat_id = message.chat.id
    user_positions[chat_id] = {"section":"الصباح","index":0}
    send_next_adhkar(chat_id)

def send_next_adhkar(chat_id):
    pos = user_positions[chat_id]
    if pos["index"] < len(adhkar[pos["section"]]):
        text = adhkar[pos["section"]][pos["index"]]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("التالي ➡️",callback_data="next_adhkar"))
        bot.send_message(chat_id,text,reply_markup=markup)
        pos["index"] += 1
    else:
        bot.send_message(chat_id,"✅ انتهت الأذكار 🌸")

@bot.callback_query_handler(func=lambda c: c.data=="next_adhkar")
def handle_next_adhkar(call):
    bot.edit_message_reply_markup(call.message.chat.id,call.message.message_id,reply_markup=None)
    send_next_adhkar(call.message.chat.id)

# 🎵 تلاوات مختارة
@bot.message_handler(func=lambda m: m.text=="🎵 تلاوات مختارة")
def show_user_rec(message):
    chat_id = message.chat.id
    recs = user_recitations.get(chat_id,[])
    if not recs:
        bot.send_message(chat_id,"لا توجد تلاوات محفوظة")
        return
    markup = InlineKeyboardMarkup()
    for r in recs:
        markup.add(InlineKeyboardButton(r["name"],callback_data=f"user_{r['url']}"))
    bot.send_message(chat_id,"اختر تلاوة:",reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("user_"))
def send_user_rec(call):
    url = call.data.replace("user_","")
    bot.edit_message_reply_markup(call.message.chat.id,call.message.message_id,reply_markup=None)
    bot.send_audio(call.message.chat.id,url)

@bot.message_handler(content_types=["audio"])
def save_user_rec(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.audio.file_id)
    url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
    rec_name = message.audio.file_name or f"تلاوة {len(user_recitations.get(chat_id,[]))+1}"
    user_recitations.setdefault(chat_id,[]).append({"name":rec_name,"url":url})
    bot.send_message(chat_id,f"تم حفظ التلاوة: {rec_name} ✅")

# 📖 القرآن
@bot.message_handler(func=lambda m: m.text=="📖 القرآن")
def send_reciters(message):
    markup = InlineKeyboardMarkup()
    row=[]
    for i, r in enumerate(reciters_data, start=1):
        row.append(InlineKeyboardButton(r["name"],callback_data=f"reciter_{i-1}"))
        if len(row)==3:
            markup.add(*row); row=[]
    if row: markup.add(*row)
    bot.send_message(message.chat.id,"اختر القارئ:",reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("reciter_"))
def handle_reciter(call):
    idx=int(call.data.split("_")[1])
    rec=reciters_data[idx]
    bot.edit_message_reply_markup(call.message.chat.id,call.message.message_id,reply_markup=None)
    markup=InlineKeyboardMarkup()
    # سور الـ 114
    for i in range(1,115):
        name=f"{i:03}"
        markup.add(InlineKeyboardButton(f"سورة {name}",callback_data=f"sura_{idx}_{i}"))
    # خيار الصفحات
    if rec["has_pages"]:
        markup.add(InlineKeyboardButton("📑 اختيار نطاق صفحات",callback_data=f"pages_{idx}"))
    bot.send_message(call.message.chat.id,f"اختر السورة أو الصفحات لـ {rec['name']}:",reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sura_"))
def send_sura(call):
    parts=call.data.split("_")
    idx=int(parts[1]); s_id=int(parts[2])
    rec=reciters_data[idx]
    audio_url=f"{rec['server']}/{s_id:03}.mp3"
    bot.edit_message_reply_markup(call.message.chat.id,call.message.message_id,reply_markup=None)
    bot.send_audio(call.message.chat.id,audio_url)

# تشغيل البوت
bot.infinity_polling()        count = users[user_id]["tasbeeh"]

        keyboard = [
            [InlineKeyboardButton("➕ سبح", callback_data="addtasbeeh")],
            [InlineKeyboardButton("🔄 تصفير", callback_data="resettasbeeh")],
            [InlineKeyboardButton("⬅ رجوع", callback_data="back")]
        ]

        await query.edit_message_text(
            f"🧮 عداد التسبيح\n\nعدد التسبيحات: {count}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "addtasbeeh":
        users = load_users()
        user_id = str(query.from_user.id)
        users[user_id]["tasbeeh"] += 1
        save_users(users)
        count = users[user_id]["tasbeeh"]

        await query.edit_message_text(
            f"🧮 عداد التسبيح\n\nعدد التسبيحات: {count}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ سبح", callback_data="addtasbeeh")],
                [InlineKeyboardButton("🔄 تصفير", callback_data="resettasbeeh")],
                [InlineKeyboardButton("⬅ رجوع", callback_data="back")]
            ])
        )

    elif data == "resettasbeeh":
        users = load_users()
        user_id = str(query.from_user.id)
        users[user_id]["tasbeeh"] = 0
        save_users(users)
        await query.edit_message_text(
            "تم تصفير العداد ✅",
            reply_markup=main_menu()
        )

    elif data == "back":
        await query.edit_message_text(
            "🌿 القائمة الرئيسية:",
            reply_markup=main_menu()
        )

    else:
        await query.edit_message_text(
            "🚧 هذا القسم قيد التطوير...",
            reply_markup=main_menu()
        )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    print("Bot is running...")
    app.run_polling()

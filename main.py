import json
import os
import random
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")

USERS_FILE = "users.json"

# إنشاء ملف المستخدمين إذا غير موجود
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# آيات مدمجة
AYAT = [
    "﴿ وَقُل رَّبِّ زِدْنِي عِلْمًا ﴾ [طه:114]",
    "﴿ إِنَّ مَعَ الْعُسْرِ يُسْرًا ﴾ [الشرح:6]",
    "﴿ وَاللَّهُ خَيْرُ الرَّازِقِينَ ﴾ [الجمعة:11]",
    "﴿ أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ ﴾ [الرعد:28]"
]

ADHKAR = {
    "morning": "🌅 أذكار الصباح:\n\nسبحان الله وبحمده (100 مرة)",
    "evening": "🌇 أذكار المساء:\n\nأعوذ بكلمات الله التامات من شر ما خلق (3 مرات)",
    "sleep": "🌙 أذكار النوم:\n\nباسمك اللهم أموت وأحيا"
}

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📖 القرآن الكريم", callback_data="quran")],
        [InlineKeyboardButton("🎙 تلاواتي الخاصة", callback_data="myrecitations")],
        [InlineKeyboardButton("📿 الأذكار", callback_data="adhkar")],
        [InlineKeyboardButton("🌟 آية اليوم", callback_data="ayah")],
        [InlineKeyboardButton("🧮 عداد التسبيح", callback_data="tasbeeh")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    if str(user.id) not in users:
        users[str(user.id)] = {"tasbeeh": 0}
        save_users(users)

    text = (
        "🌿 أهلاً بك في بوت *أَثَــر*\n\n"
        "أثرٌ يبقى في قلبك...\n\n"
        "اختر من القائمة التالية:"
    )
    await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "ayah":
        ayah = random.choice(AYAT)
        await query.edit_message_text(
            f"🌟 *آية اليوم*\n\n{ayah}",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    elif data == "adhkar":
        keyboard = [
            [InlineKeyboardButton("🌅 الصباح", callback_data="morning")],
            [InlineKeyboardButton("🌇 المساء", callback_data="evening")],
            [InlineKeyboardButton("🌙 النوم", callback_data="sleep")],
            [InlineKeyboardButton("⬅ رجوع", callback_data="back")]
        ]
        await query.edit_message_text(
            "📿 اختر نوع الذكر:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data in ADHKAR:
        await query.edit_message_text(
            ADHKAR[data],
            reply_markup=main_menu()
        )

    elif data == "tasbeeh":
        users = load_users()
        user_id = str(query.from_user.id)
        count = users[user_id]["tasbeeh"]

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

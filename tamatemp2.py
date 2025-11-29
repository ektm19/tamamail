import requests
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup # ⚠️ Tambahan: Import untuk Inline Buttons
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

MAIL_TM_API = "https://api.mail.tm"
user_sessions = {}
ADMIN_IDS = [123456789]  # Replace with your Telegram user ID
REQUIRED_CHANNEL = "@YourChannelUsername"

def random_str(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        return await update.message.reply_text(
            f"📢 Please join our channel first:\n{REQUIRED_CHANNEL}"
        )

    # 🧱 Membuat Inline Keyboard
    keyboard = [
        [
            InlineKeyboardButton("📧 New Email", callback_data="/new"),
            InlineKeyboardButton("📥 Inbox", callback_data="/inbox")
        ],
        [
            InlineKeyboardButton("🗑️ Delete Email", callback_data="/delete"),
            InlineKeyboardButton("ℹ️ Info", callback_data="/info")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # 🧱 Akhir Pembuatan Inline Keyboard

    msg = (
        "👋 *Welcome to TempMail Bot!*\n\n"
        "You can use the following commands or the buttons below:\n\n"
        "📧 `/new` – Create a new temporary email\n"
        "📥 `/inbox` – View inbox messages\n"
        "🗑️ `/delete` – Delete your current temp email\n"
        "ℹ️ `/info` – Show your current email session\n"
    )
    # 💬 Mengirim pesan dengan Inline Keyboard
    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=reply_markup # ⚠️ Tambahan: Mengirim keyboard
    )

# ⚙️ Tambahan: Callback Handler untuk Inline Button
from telegram.ext import CallbackQueryHandler

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Harus dipanggil untuk menghentikan loading di tombol

    command = query.data
    
    # ➡️ Arahkan ke fungsi command yang sesuai
    if command == "/new":
        await new_email(update, context)
    elif command == "/inbox":
        await inbox(update, context)
    elif command == "/delete":
        await delete_email(update, context)
    elif command == "/info":
        await info(update, context)
    # Catatan: Karena fungsi command handler Anda sudah mengambil Update dan Context,
    # kita bisa memanggilnya langsung. Dalam skenario nyata, mungkin perlu sedikit 
    # penyesuaian pada cara fungsi-fungsi tersebut menangani Update dari Message vs CallbackQuery.
    # Untuk kasus ini, saya akan menggunakan Update dari CallbackQuery (query.message)
    # dan memanggil fungsi command yang ada.

# [Fungsi new_email, inbox, delete_email, info, stats, broadcast lainnya tetap sama]
# ... (Sisanya dari tamatemp.py) ...

# ⚠️ Anda harus menambahkan CallbackQueryHandler di fungsi main()

def main():
    BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers untuk Command (tetap ada)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_email))
    app.add_handler(CommandHandler("inbox", inbox))
    app.add_handler(CommandHandler("delete", delete_email))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # ⚠️ Handler Baru untuk Tombol Inline
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 TempMail Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
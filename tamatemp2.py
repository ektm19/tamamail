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
ADMIN_IDS = [1188483395]  # Replace with your Telegram user ID
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
async def new_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    username = random_str()
    password = random_str()

    # Get domain
    domains_resp = requests.get(f"{MAIL_TM_API}/domains")
    if domains_resp.status_code != 200:
        return await update.message.reply_text("❌ Failed to fetch mail domains.")
    domain = domains_resp.json()["hydra:member"][0]["domain"]
    email = f"{username}@{domain}"

    # Create account
    create_resp = requests.post(f"{MAIL_TM_API}/accounts", json={"address": email, "password": password})
    if create_resp.status_code not in [200, 201]:
        return await update.message.reply_text("❌ Failed to create email.")

    # Auth token
    token_resp = requests.post(f"{MAIL_TM_API}/token", json={"address": email, "password": password})
    if token_resp.status_code != 200:
        return await update.message.reply_text("❌ Failed to authenticate.")

    token = token_resp.json()["token"]
    user_sessions[user_id] = {
        "email": email,
        "password": password,
        "token": token
    }

    await update.message.reply_text(f"✅ Your temp email:\n📧 `{email}`", parse_mode="Markdown")

async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if not session:
        return await update.message.reply_text("ℹ️ Use /new to create a temporary email first.")

    headers = {"Authorization": f"Bearer {session['token']}"}
    r = requests.get(f"{MAIL_TM_API}/messages", headers=headers)
    data = r.json()
    if not data["hydra:member"]:
        return await update.message.reply_text("📭 Inbox is empty.")

    for m in data["hydra:member"][:3]:
        msg_id = m["id"]
        detail_resp = requests.get(f"{MAIL_TM_API}/messages/{msg_id}", headers=headers)
        if detail_resp.status_code != 200:
            continue

        msg_detail = detail_resp.json()
        sender = msg_detail["from"]["address"]
        subject = msg_detail["subject"] or "(no subject)"
        body = msg_detail.get("text", "(No content)")

        text = (
            f"*From:* `{sender}`\n"
            f"*Subject:* _{subject}_\n\n"
            f"*Message:*\n"
            f"\n{body.strip()[:1000]}\n"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

async def delete_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        user_sessions.pop(user_id)
        await update.message.reply_text("🗑️ Your temp email has been deleted.")
    else:
        await update.message.reply_text("ℹ️ No temp email to delete.")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    if session:
        email = session['email']
        await update.message.reply_text(f"📧 Your current temp email:\n`{email}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("ℹ️ You don't have a temp email yet.")

# Admin Commands
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    total_users = len(user_sessions)
    await update.message.reply_text(f"👤 Total active users: {total_users}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    msg = ' '.join(context.args)
    count = 0
    for user_id in user_sessions:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg)
            count += 1
        except:
            continue
    await update.message.reply_text(f"✅ Message sent to {count} users.")

# ⚠️ Anda harus menambahkan CallbackQueryHandler di fungsi main()

def main():
    BOT_TOKEN = "8271421272:AAHDcwdsveSmwKVXvqAHn4VpdKSpXH37cG4"  # Replace with your bot token
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




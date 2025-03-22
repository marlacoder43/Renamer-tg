import sqlite3
import random
import string
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔹 Pyrogram sozlamalari
app = Client(
    "my_bot",
    api_id=22074001,
    api_hash="cc284bc8899943302cef9f2a3d513b97",
    bot_token="7307280462:AAHC-HKLawpcDubtaVZNbatwZ5HYPXGAOnQ"
)

DATABASE_CHANNEL = -1002470781771  # Kanal ID
ADMINS = [6856658357, 987654321]  # Adminlar ID

# 📌 SQL bazani yaratish
conn = sqlite3.connect("files.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    file_id TEXT,
    file_name TEXT,
    file_size TEXT,
    token TEXT UNIQUE
)
""")
conn.commit()

TEMP_FILES = {}

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=33))

@app.on_message(filters.private & filters.document)
async def save_file(client, message):
    if message.from_user.id not in ADMINS:
        await message.reply_text("⚠️ Siz fayl yubora olmaysiz! Faqat adminlar yuklay oladi.")
        return

    file_id = message.document.file_id
    file_name = message.document.file_name if message.document.file_name else "Noma’lum fayl"
    file_size = round(message.document.file_size / 1024 / 1024, 2)

    TEMP_FILES[message.from_user.id] = {
        "file_id": file_id,
        "file_name": file_name,
        "file_size": file_size
    }

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Rasm qo‘shish", callback_data="send_thumb")],
        [InlineKeyboardButton("⏩ O‘tkazib yuborish", callback_data="skip_thumb")]
    ])

    await message.reply_text("🖼 Faylga rasm qo‘shishni xohlaysizmi?", reply_markup=buttons)

@app.on_callback_query()
async def handle_thumbnail(client, callback_query):
    user_id = callback_query.from_user.id

    if user_id not in TEMP_FILES:
        await callback_query.answer("❌ Avval fayl yuboring!", show_alert=True)
        return

    if callback_query.data == "send_thumb":
        await callback_query.message.edit_text("🖼 Endi rasm yuboring.")
        TEMP_FILES[user_id]["waiting_thumb"] = True
    elif callback_query.data == "skip_thumb":
        await callback_query.message.edit_text("⏩ Rasm qo‘shilmadi. Fayl saqlanmoqda...")
        await upload_file(client, user_id)

@app.on_message(filters.private & filters.photo)
async def receive_thumbnail(client, message):
    user_id = message.from_user.id

    if user_id in TEMP_FILES and TEMP_FILES[user_id].get("waiting_thumb"):
        # 🔹 "Iltimos, kuting..." xabarini reply sifatida yuborish
        processing_msg = await message.reply_text("⏳ Iltimos, kuting... Yuklanmoqda...", reply_to_message_id=message.id)

        thumb_path = await client.download_media(message.photo.file_id)
        TEMP_FILES[user_id]["thumb_path"] = thumb_path
        TEMP_FILES[user_id]["waiting_thumb"] = False  

        # 🔹 "Yuklanmoqda..." xabarini o‘chirib, faylni yuklash
        await processing_msg.delete()
        await upload_file(client, user_id)

async def upload_file(client, user_id):
    if user_id not in TEMP_FILES:
        return

    file_data = TEMP_FILES.pop(user_id)
    file_id, file_name, file_size = file_data["file_id"], file_data["file_name"], file_data["file_size"]
    thumb_path = file_data.get("thumb_path")

    # 📥 Faylni yuklab olish
    downloaded_path = await client.download_media(file_id)

    # 🔥 Fayl kengaytmasini to‘g‘rilash
    file_extension = os.path.splitext(file_name)[-1]  
    correct_path = downloaded_path

    if not downloaded_path.endswith(file_extension):  
        correct_path = downloaded_path + file_extension
        os.rename(downloaded_path, correct_path)
    
    # 📤 Faylni kanalga yuklash
    sent_message = await client.send_document(
        DATABASE_CHANNEL,
        document=correct_path,
        thumb=thumb_path if thumb_path else None,
        caption=f"📂 **{file_name}**\n📦 **{file_size} MB**",
        disable_notification=True,
        protect_content=True
    )

    # 🗑 Yuklangan fayllarni o‘chirish
    os.remove(correct_path)
    if thumb_path:
        os.remove(thumb_path)

    # 🔗 Link yaratish
    token = generate_token()
    cur.execute("INSERT INTO files (file_id, file_name, file_size, token) VALUES (?, ?, ?, ?)", 
                (sent_message.document.file_id, file_name, file_size, token))
    conn.commit()

    bot_username = (await client.get_me()).username
    link = f"https://t.me/{bot_username}?start={token}"

    share_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Ulashish", url=f"https://t.me/share/url?url={link}")]
    ])

    await client.send_message(user_id, f"✅ Fayl saqlandi!\n\n🔗 **Havola:** {link}", reply_markup=share_button)

@app.on_message(filters.private & filters.command("start"))
async def send_file(client, message):
    if len(message.command) > 1:
        token = message.command[1]

        cur.execute("SELECT file_id, file_name, file_size FROM files WHERE token = ?", (token,))
        file_data = cur.fetchone()

        if file_data:
            file_id, file_name, file_size = file_data
            await message.reply_document(
                file_id,
                caption=f"📂 **{file_name}**\n📦 **{file_size} MB**"
            )
            return
        else:
            await message.reply_text("⚠️ Bunday fayl topilmadi yoki link eskirgan.")
    else:
        await message.reply_text(
            "👋 Salom!\n\n"
            "📂 Ushbu bot orqali fayllarni faqat **start havola** orqali olishingiz mumkin.\n"
            "⚠️ Agar sizda start havola bo‘lmasa, admin bilan bog‘laning."
        )

app.run()

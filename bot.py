import telebot
import requests
import re
import os
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
REEL_API = os.getenv("REEL_API")
PIN_API = os.getenv("PIN_API")
INFO_API = os.getenv("INFO_API")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="MarkdownV2")
app = Flask(__name__)

LAST_UPDATE_ID = 0

def escape(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text or ""))

@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(
        m.chat.id,
        "*🔥 Multi Downloader Bot*\n\n"
        "📥 Send:\n"
        "• Instagram Reel link\n"
        "• Pinterest link\n"
        "• `/info username`\n\n"
        "_Fast • Stable • Secure_"
    )

@bot.message_handler(commands=["info"])
def info(m):
    if not m.text:
        return

    parts = m.text.split()
    if len(parts) < 2:
        bot.send_message(m.chat.id, "❌ *Usage:* `/info username`")
        return

    try:
        res = requests.get(
            INFO_API,
            params={"key": API_KEY, "username": parts[1]},
            timeout=10
        )

        data = res.json()
        if "data" not in data:
            bot.send_message(m.chat.id, "❌ *User not found or private*")
            return

        d = data["data"]

        caption = (
            "*👤 Instagram User Info*\n\n"
            f"*Username:* `{escape(d.get('username'))}`\n"
            f"*Name:* {escape(d.get('full_name'))}\n"
            f"*Bio:* {escape(d.get('bio'))}\n\n"
            f"*Followers:* `{d.get('followers')}`\n"
            f"*Following:* `{d.get('following')}`\n"
            f"*Posts:* `{d.get('posts')}`\n\n"
            f"*Verified:* `{d.get('is_verified')}`\n"
            f"*Private:* `{d.get('is_private')}`\n\n"
            f"[🔗 Open Profile]({escape(d.get('direct_link'))})"
        )

        bot.send_photo(m.chat.id, d.get("profile_image_hd"), caption=caption)

    except Exception:
        bot.send_message(m.chat.id, "❌ *Failed to fetch info*")

@bot.message_handler(func=lambda m: bool(m.text))
def detect(m):
    text = m.text

    if "instagram.com" in text:
        wait = bot.send_message(m.chat.id, "⏳ *Downloading Reel\\.\\.\\.*")
        try:
            r = requests.get(REEL_API, params={"key": API_KEY, "url": text}, timeout=15).json()
            if r.get("status") == "success":
                bot.edit_message_text("✅ *Reel Downloaded*", m.chat.id, wait.message_id)
                bot.send_video(m.chat.id, r["video"], caption="🎬 *Instagram Reel*")
            else:
                bot.edit_message_text("❌ *Failed*", m.chat.id, wait.message_id)
        except:
            bot.edit_message_text("❌ *Error*", m.chat.id, wait.message_id)

    elif "pin.it" in text or "pinterest.com" in text:
        wait = bot.send_message(m.chat.id, "⏳ *Downloading Pin\\.\\.\\.*")
        try:
            r = requests.get(PIN_API, params={"key": API_KEY, "url": text}, timeout=15).json()
            if r.get("status") == "success":
                bot.edit_message_text("✅ *Pin Downloaded*", m.chat.id, wait.message_id)
                bot.send_photo(m.chat.id, r["photo"], caption="📌 *Pinterest Image*")
            else:
                bot.edit_message_text("❌ *Failed*", m.chat.id, wait.message_id)
        except:
            bot.edit_message_text("❌ *Error*", m.chat.id, wait.message_id)

@app.route("/webhook", methods=["POST"])
def webhook():
    global LAST_UPDATE_ID
    try:
        update = telebot.types.Update.de_json(request.data.decode("utf-8"))
        if update.update_id <= LAST_UPDATE_ID:
            return "OK", 200
        LAST_UPDATE_ID = update.update_id
        bot.process_new_updates([update])
    except Exception:
        pass
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

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

def escape(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(
        m,
        "*🔥 Multi Downloader Bot*\n\n"
        "📥 Send:\n"
        "• Instagram Reel link\n"
        "• Pinterest link\n"
        "• `/info username`\n\n"
        "_Fast • Secure • Free_"
    )

@bot.message_handler(commands=['info'])
def info(m):
    try:
        parts = m.text.split()
        if len(parts) < 2:
            bot.reply_to(m, "❌ *Usage:* `/info username`")
            return

        r = requests.get(
            INFO_API,
            params={"key": API_KEY, "username": parts[1]},
            timeout=15
        ).json()

        d = r["data"]

        caption = (
            "*👤 Instagram User Info*\n\n"
            f"*Username:* `{escape(d['username'])}`\n"
            f"*Name:* {escape(d['full_name'])}\n"
            f"*Bio:* {escape(d['bio'])}\n\n"
            f"*Followers:* `{d['followers']}`\n"
            f"*Following:* `{d['following']}`\n"
            f"*Posts:* `{d['posts']}`\n\n"
            f"*Verified:* `{d['is_verified']}`\n"
            f"*Private:* `{d['is_private']}`\n\n"
            f"[🔗 Open Profile]({escape(d['direct_link'])})"
        )

        bot.send_photo(m.chat.id, d["profile_image_hd"], caption=caption)
    except:
        bot.reply_to(m, "❌ *Failed to fetch info*")

@bot.message_handler(func=lambda m: True)
def detect(m):
    text = m.text or ""

    if "instagram.com" in text:
        wait = bot.reply_to(m, "⏳ *Downloading Reel\\.\\.\\.*")
        r = requests.get(REEL_API, params={"key": API_KEY, "url": text}, timeout=20).json()

        if r.get("status") == "success":
            bot.edit_message_text("✅ *Reel Downloaded*", m.chat.id, wait.message_id)
            bot.send_video(m.chat.id, r["video"], caption="🎬 *Instagram Reel*\n\n@UseSir")
        else:
            bot.edit_message_text("❌ *Failed to download reel*", m.chat.id, wait.message_id)

    elif "pin.it" in text or "pinterest.com" in text:
        wait = bot.reply_to(m, "⏳ *Downloading Pin\\.\\.\\.*")
        r = requests.get(PIN_API, params={"key": API_KEY, "url": text}, timeout=20).json()

        if r.get("status") == "success":
            bot.edit_message_text("✅ *Pin Downloaded*", m.chat.id, wait.message_id)
            bot.send_photo(m.chat.id, r["photo"], caption="📌 *Pinterest Image*\n\n@UseSir")
        else:
            bot.edit_message_text("❌ *Failed to download pin*", m.chat.id, wait.message_id)

@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

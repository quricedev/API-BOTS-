import os
import re
import requests
from flask import Flask, request
from telebot import TeleBot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
REEL_API = os.getenv("REEL_API")
PIN_API = os.getenv("PIN_API")
INFO_API = os.getenv("INFO_API")

bot = TeleBot(BOT_TOKEN, parse_mode="MarkdownV2")
app = Flask(__name__)

def escape_md(text):
    if not text:
        return ""
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", str(text))

def is_instagram_reel(url):
    return "instagram.com/reel" in url or "instagram.com/p/" in url

def is_pinterest(url):
    return "pinterest." in url or "pin.it" in url

@bot.message_handler(commands=["start"])
def start_handler(message):
    text = (
        "*Multi Downloader Bot*\n\n"
        "• Instagram Reel Downloader\n"
        "• Pinterest Image Downloader\n"
        "• Instagram User Info\n\n"
        "Send a Reel or Pinterest link\n"
        "Or use:\n"
        "`/info username`"
    )
    bot.send_message(message.chat.id, escape_md(text))

@bot.message_handler(commands=["info"])
def info_handler(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, escape_md("Usage:\n/info username"))
        return

    username = parts[1]
    status_msg = bot.send_message(message.chat.id, escape_md("Fetching info..."))

    try:
        r = requests.get(INFO_API.format(key=API_KEY, username=username), timeout=15)
        data = r.json()

        if "data" not in data:
            raise ValueError

        d = data["data"]

        caption = (
            "*Instagram User Info*\n\n"
            f"*Username:* {escape_md(d.get('username'))}\n"
            f"*Name:* {escape_md(d.get('full_name'))}\n"
            f"*Bio:* {escape_md(d.get('bio'))}\n\n"
            f"*Followers:* {escape_md(d.get('followers'))}\n"
            f"*Following:* {escape_md(d.get('following'))}\n"
            f"*Posts:* {escape_md(d.get('posts'))}\n\n"
            f"[Open Profile]({escape_md(d.get('direct_link'))})"
        )

        bot.edit_message_text(
            caption,
            message.chat.id,
            status_msg.message_id,
            disable_web_page_preview=False
        )

        if d.get("profile_image_hd"):
            bot.send_message(
                message.chat.id,
                escape_md(d.get("profile_image_hd"))
            )

    except:
        bot.edit_message_text(
            escape_md("Failed to fetch user info."),
            message.chat.id,
            status_msg.message_id
        )

@bot.message_handler(func=lambda m: True)
def link_handler(message):
    text = message.text.strip()
    status_msg = bot.send_message(message.chat.id, escape_md("Downloading..."))

    try:
        if is_instagram_reel(text):
            r = requests.get(REEL_API.format(key=API_KEY, url=text), timeout=20)
            data = r.json()

            if data.get("status") and data.get("video"):
                bot.edit_message_text(
                    escape_md("Instagram Reel Downloaded"),
                    message.chat.id,
                    status_msg.message_id
                )
                bot.send_message(message.chat.id, escape_md(data["video"]))
                return

        if is_pinterest(text):
            r = requests.get(PIN_API.format(key=API_KEY, url=text), timeout=20)
            data = r.json()

            if data.get("status") and data.get("photo"):
                bot.edit_message_text(
                    escape_md("Pinterest Image Downloaded"),
                    message.chat.id,
                    status_msg.message_id
                )
                bot.send_message(message.chat.id, escape_md(data["photo"]))
                return

        bot.edit_message_text(
            escape_md("Unsupported or invalid link."),
            message.chat.id,
            status_msg.message_id
        )

    except:
        bot.edit_message_text(
            escape_md("Download failed."),
            message.chat.id,
            status_msg.message_id
        )

@app.route("/", methods=["POST"])
def webhook():
    bot.process_new_updates([bot.parse_update(request.get_json())])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200

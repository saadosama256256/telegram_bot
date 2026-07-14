import os
import asyncio
import logging
import httpx
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN   = os.getenv("BOT_TOKEN", "8219609386:AAGGG9-cNbE3j_-CFX1VTGgLCJhwuFZjLb8")
CHAT_ID     = int(os.getenv("CHAT_ID", "7138537775"))
N8N_WEBHOOK = os.getenv("N8N_WEBHOOK", "")

app = Flask(__name__)

@app.route("/send", methods=["POST"])
def send_message():
    data = request.json or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "no text"}), 400

    async def _send():
        trequest = HTTPXRequest(connection_pool_size=1)
        send_bot = Bot(token=BOT_TOKEN, request=trequest)
        async with send_bot:
            await send_bot.send_message(
                chat_id=CHAT_ID,
                text=text,
                parse_mode="Markdown"
            )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_send())
    finally:
        loop.close()

    return jsonify({"success": True})

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    text        = msg.text or ""
    reply_to    = msg.reply_to_message
    quoted_text = reply_to.text if reply_to else ""

    logger.info(f"Reply received: {text}")

    if N8N_WEBHOOK:
        async with httpx.AsyncClient() as client:
            await client.post(N8N_WEBHOOK, json={
                "user_reply":  text,
                "quoted_text": quoted_text,
            })

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(MessageHandler(filters.REPLY & filters.TEXT, handle_reply))

if __name__ == "__main__":
    import threading

    def run_flask():
        app.run(host="0.0.0.0", port=5000)

    threading.Thread(target=run_flask, daemon=True).start()

    logger.info("Bot started...")
    application.run_polling()

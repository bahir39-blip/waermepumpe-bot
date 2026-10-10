import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Hier tragen wir gleich die Schlüssel ein
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """
Du bist ein professioneller KI-Berater für Wärmepumpen in Deutschland. 
Deine Aufgabe ist es, Hausbesitzer in Telegram zu begrüßen, ihr Anliegen zu verstehen 
und nach der Postleitzahl (PLZ) sowie dem aktuellen Heizungssystem zu fragen, 
um sie an lokale Handwerker zu vermitteln. Antworte freundlich und auf Deutsch.
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    }
    
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    result = response.json()
    ai_reply = result["choices"][0]["message"]["content"]
    
    await update.message.reply_text(ai_reply)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot gestartet...")
    app.run_polling()
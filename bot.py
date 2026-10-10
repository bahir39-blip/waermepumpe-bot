import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# API-Schlüssel aus den Render-Umgebungsvariablen laden
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """
Du bist ein professioneller KI-Berater für Wärmepumpen in Deutschland. 
Deine Aufgabe ist es, Hausbesitzer in Telegram zu begrüßen, ihr Anliegen zu verstehen 
und nach der Postleitzahl (PLZ) sowie dem aktuellen Heizungssystem zu fragen, 
um sie an lokale Handwerker zu vermitteln. Antworte freundlich und auf Deutsch.
"""

# Einfacher HTTP-Dummy-Server für Render Health Checks
class DummyHealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHealthCheckHandler)
    server.serve_forever()

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
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        result = response.json()
        ai_reply = result["choices"][0]["message"]["content"]
    except Exception as e:
        ai_reply = "Entschuldigung, es gab einen kurzen Fehler bei der Verarbeitung."

    await update.message.reply_text(ai_reply)

if __name__ == "__main__":
    # Starte den Dummy-Server in einem separaten Thread für Render
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # Starte den Telegram-Bot
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot gestartet...")
    app.run_polling()

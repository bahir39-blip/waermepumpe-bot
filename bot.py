import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """
Du bist ein erfahrener Heizungsbau-Meister und Fachberater für Wärmepumpen in Deutschland mit über 15 Jahren Praxiserfahrung. 

Deine Persönlichkeit:
- Du sprichst höflich, hochprofessionell, aber sehr menschlich, nahbar und verständlich.
- Vermeide komplizierte Schachtelsätze oder reine Standard-Floskeln.
- Begrüße den Kunden NUR EINMALig ganz am Anfang des Chats.
- Antworte präzise auf die Fragen des Kunden. Halte dich kurz und knackig (2 bis 4 Sätze pro Antwort), damit es ein natürlicher Chat bleibt.

Dein Fachwissen:
- Du kennst dich perfekt mit Luft-Wasser-, Sole-Wasser- (Erdwärme) und Wasser-Wasser-Wärmepumpen aus.
- Du kennst technische Details wie Vorlauftemperaturen, Altbau-Eignung, Fußbodenheizung vs. Heizkörper und Jahresarbeitszahlen (JAZ).
- Du kennst die aktuellen KfW-Förderungen (BEG EM) in Deutschland genau:
  * Grundförderung: 30 % für alle Wohngebäude.
  * Geschwindigkeitsbonus: +20 % für den schnellen Austausch alter fossiler Heizungen.
  * Einkommensbonus: +30 % für Haushalte mit bis zu 40.000 € zu versteuerndem Jahreseinkommen.
  * Effizienzbonus: +5 % für natürliche Kältemittel (z. B. R290 Propann).
  * Maximaler Zuschuss gekappt bei 70 % (max. Förderdeckel liegt bei 30.000 € für die erste Wohneinheit).

Dein Ziel im Gespräch:
- Beantworte alle Fach- und Förderfragen des Kunden kompetent.
- Wenn der Kunde begeistert ist oder Fragen beantwortet wurden, frage nach seiner Postleitzahl (PLZ) und der aktuellen Heizung (z. B. Öl oder Gas), um ihm einen passenden Fachbetrieb aus der Region für ein kostenloses Angebot zu vermitteln.
"""

# Dummy HTTP-Server für Render Health Checks
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
    
    # Gesprächsverlauf laden oder initialisieren
    if "history" not in context.user_data:
        context.user_data["history"] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Nachricht des Nutzers an den Verlauf anhängen
    context.user_data["history"].append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": context.user_data["history"]
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        result = response.json()
        ai_reply = result["choices"][0]["message"]["content"]
        
        # Antwort der KI im Verlauf speichern
        context.user_data["history"].append({"role": "assistant", "content": ai_reply})
    except Exception as e:
        ai_reply = "Entschuldigung, da gab es kurz eine kleine Störung. Was kann ich für Sie tun?"

    await update.message.reply_text(ai_reply)

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot gestartet...")
    app.run_polling()

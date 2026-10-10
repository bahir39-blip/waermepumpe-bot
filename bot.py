import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Trage hier deine persönliche Telegram-ID als Zahl ein (z. B. 123456789)
ADMIN_CHAT_ID = 1536340598  # <--- HIER DEINE ID EINTRAGEN

SYSTEM_PROMPT = """
Du bist ein erfahrener, absolut vertrauenswürdiger Meister im Heizungsbau und Top-Fachberater für Wärmepumpen mit über 15 Jahren Praxiserfahrung in Deutschland.

Deine Verkaufs- und Kommunikationsphilosophie:
- Du agierst extrem menschlich, warmherzig, professionell und auf Augenhöhe. Du bist absolut **niemals aufdringlich**, sondern überzeugst durch fachliche Kompetenz und echten Mehrwert.
- Du hörst dem Kunden zu, nimmst seine Sorgen (z. B. zu Altbau-Eignung, Stromkosten oder Investition) ernst und nimmst sie ihm durch faktenbasierte, beruhigende Antworten.
- Du kennst die aktuellen KfW-Förderungen (BEG EM) perfekt (bis zu 70 % Gesamtzuschuss: 30 % Grundförderung + Geschwindigkeitsbonus + Einkommensbonus).

Deine Strategie zur Termin- und Lead-Gewinnung:
1. Beantworte alle Fragen des Kunden präzise, natürlich und verständlich (halte Antworten kompakt, max. 2–3 Sätze).
2. Verknüpfe den Mehrwert deines Fachbetriebs geschickt mit dem nächsten Schritt: Um eine exakte Wirtschaftlichkeitsberechnung und das maximale Fördervolumen für sein spezifisches Haus zu berechnen, bietet sich ein unverbindliches, kurzes Fachgespräch an.
3. Frage charmant und organisch nach der **Postleitzahl (PLZ)**, der **Telefonnummer** und dem **aktuellen Heizungssystem**, damit sich ein regionaler Experte für ein maßgeschneidertes Festpreis-Angebot melden kann. 
4. Sobald der Kunde seine Kontaktdaten oder einen Terminwunsch nennt, bedanke dich herzlich, bestätige den Termin professionell und weise darauf hin, dass sich der Fachberater in Kürze bei ihm meldet.
"""

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
    user_name = update.effective_user.first_name or "Kunde"
    user_handle = f"@{update.effective_user.username}" if update.effective_user.username else "Kein Username"
    
    if "history" not in context.user_data:
        context.user_data["history"] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
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
        context.user_data["history"].append({"role": "assistant", "content": ai_reply})
    except Exception as e:
        ai_reply = "Entschuldigung, da gab es einen kurzen technischen Hänger. Wie kann ich Ihnen weiterhelfen?"

    # Lead-Erfassung: Wenn der Kunde Kontaktdaten/Zahlen sendet, loggen wir das direkt für dich!
    print(f"\n--- NEUE NACHRICHT VON {user_name} ({user_handle}) ---")
    print(f"Nachricht: {user_message}")
    print(f"Bot-Antwort: {ai_reply}\n")

    await update.message.reply_text(ai_reply)

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot gestartet...")
    app.run_polling()

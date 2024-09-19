
import os  
from flask import Flask, request, jsonify 
from functools import wraps 
from openai import OpenAI 
from dotenv import load_dotenv  
from flask_cors import CORS  
from telegram import Update, Bot 
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackContext  
app = Flask(__name__)
CORS(app)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  
bot = Bot(token=TELEGRAM_TOKEN)

def require_token_auth(func):
    @wraps(func)
    def check_token(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Token de autenticação não fornecido"}), 401
        
        token = auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else None
        expected_token = os.getenv("BEARER_TOKEN")
        if not token or token != expected_token:
            return jsonify({"error": "Token de autenticação inválido"}), 401
        
        return func(*args, **kwargs)
    
    return check_token

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

system_prompt = "Você é uma assistente Geral"

def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    response = get_chatbot_response(user_message)
    
    update.message.reply_text(response)

def get_chatbot_response(user_content):
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )

        response_content = completion.choices[0].message.content
        return response_content

    except Exception as e:
        return f"Erro ao gerar resposta: {e}"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Olá! Eu sou o assistente Geral. Como posso ajudar?")

def setup_telegram_bot():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    setup_telegram_bot()

    app.run(debug=True, host="0.0.0.0", port=5000)

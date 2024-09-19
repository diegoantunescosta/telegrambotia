import os
import requests
from flask import Flask, request, jsonify
from functools import wraps
from openai import OpenAI
from dotenv import load_dotenv
from flask_cors import CORS
from datetime import datetime, timedelta
import calendar

app = Flask(__name__)
CORS(app)

load_dotenv()

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

# Initialize system_prompt as a global variable
system_prompt = "Você é uma assistente da granja."

def fetch_and_update_data():
    global system_prompt  # Ensure system_prompt is global within this function
    last_business_day = get_last_business_day()
    try:
        # Fetch data from APIs
        cotacao_response = requests.get(f'http://213.199.37.135:5000/api/egg-prices?date={last_business_day}')
        online_response = requests.get('http://213.199.37.135:5000/api/eggs_online')
        additional_data_response = requests.get('http://213.199.37.135:5000/getData')
        
        if (cotacao_response.status_code == 200 and
            online_response.status_code == 200 and
            additional_data_response.status_code == 200):
            cotacao_data = cotacao_response.json()
            online_data = online_response.json()
            additional_data = additional_data_response.json()
            
            # Update the system prompt with the new data
            system_prompt = (
                f"Você é uma assistente geral. Dados de cotação: {cotacao_data}, "
                f"Dados online: {online_data}, Dados adicionais: {additional_data}"
            )
        else:
            print("Erro ao obter dados das APIs")

    except Exception as e:
        print(f"Erro ao atualizar dados: {e}")

def get_last_business_day():
    now = datetime.now()
    last_business_day = now - timedelta(days=1)
    while last_business_day.weekday() in [calendar.SATURDAY, calendar.SUNDAY]:
        last_business_day -= timedelta(days=1)

    return last_business_day.strftime('%Y-%m-%d')

# Rota protegida com autenticação Bearer Token
@app.route('/analyze', methods=['POST'])
@require_token_auth
def analyze():
    data = request.json
    user_content = data.get("content")
    
    if not user_content:
        return jsonify({"error": "Content is required"}), 400

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )

        response_content = completion.choices[0].message.content
        response_json = {
            "response": response_content
        }
        
        return jsonify(response_json)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Perform the initial data update
    # fetch_and_update_data()

    # Start the Flask app
    app.run(debug=True, host="0.0.0.0", port=5000)

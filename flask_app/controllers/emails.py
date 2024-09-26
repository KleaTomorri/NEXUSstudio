import os
from flask import Flask, request, jsonify, render_template, redirect, session, flash
import requests
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_bcrypt import Bcrypt
from flask_app.models.auth import User
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify

load_dotenv()

emails_bp = Blueprint('emails', __name__)
bcrypt = Bcrypt()
s = URLSafeTimedSerializer(os.getenv("SECRET_KEY"))

@emails_bp.route('/generate-emails')
def dashboard():
    return render_template('email.html')

app = Flask(__name__)

api_key = os.getenv("API_KEY")
api_url = os.getenv("API_URL")

def generate_email(context, tone, audience, purpose):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"Write a well structured and an {tone} email for {audience} with the purpose of {purpose}. The context is: {context}"

    payload = {
        "model": "tiiuae/falcon-180B-chat",
        "messages": [
            {"role": "system", "content": "Generate an email based on user input."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        email_content = data["choices"][0]["message"]["content"]
        return email_content

    except requests.exceptions.RequestException as e:
        return str(e)

@emails_bp.route('/generate_email', methods=['POST'])
def generate_email_endpoint():
    print("Request received")
    data = request.json
    print(data)

    context = data.get('context')
    tone = data.get('tone')
    audience = data.get('audience')
    purpose = data.get('purpose')

    try:
        generated_email = generate_email(context, tone, audience, purpose)
        return jsonify({'generated_email': generated_email})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

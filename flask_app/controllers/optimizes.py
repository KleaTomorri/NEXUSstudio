from flask import Flask, request, jsonify, render_template, Blueprint
import requests
import os
from werkzeug.utils import secure_filename
from docx import Document
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

optimize_bp = Blueprint('optimize', __name__)
app = Flask(__name__)

# Fetch API key and URL from environment variables
api_key = os.getenv("API_KEY")
api_url = os.getenv("API_URL")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_file_content(file_path, file_extension):
    content = ""
    if file_extension == 'txt':
        with open(file_path, 'r') as file:
            content = file.read()
    elif file_extension == 'docx':
        doc = Document(file_path)
        content = '\n'.join([para.text for para in doc.paragraphs])
    elif file_extension == 'pdf':
        reader = PdfReader(file_path)
        content = '\n'.join([page.extract_text() for page in reader.pages])
    return content

@optimize_bp.route('/optimize-content')
def dashboard():
    return render_template('optimize.html')

@optimize_bp.route('/identify_flaws', methods=['POST'])
def identify_flaws():
    content_input = request.form.get('contentInput', '')
    file_content = ''

    if 'fileUpload' in request.files:
        file = request.files['fileUpload']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            file_extension = filename.rsplit('.', 1)[1].lower()
            file_content = read_file_content(file_path, file_extension)

    if not content_input.strip() and not file_content:
        return jsonify({'error': 'No content provided.'}), 400

    content = content_input if content_input.strip() else file_content

    prompt = (f"You are an assistant that helps users improve their content with its clarity, grammar, style and overall. "
              f"You should only display the parts or phrases or words which need to be improved. You should give the user instruction on how to improve those specific words or phrases. "
              f"The original content is: {content}")

    payload = {
        "model": "tiiuae/falcon-180B-chat",
        "messages": [
            {"role": "system", "content": prompt}
        ]
    }

    try:
        response = requests.post(api_url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload)
        response.raise_for_status()
        data = response.json()

        flaws = data['choices'][0]['message']['content'] if 'choices' in data else 'No flaws identified.'

        return jsonify({'flaws': flaws})

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@optimize_bp.route('/optimize_content', methods=['POST'])
def optimize_content():
    improvement_type = request.form.get('improvementType')
    target_audience = request.form.get('targetAudience')
    tone = request.form.get('tone')
    content_input = request.form.get('contentInput', '')

    file_content = ''
    if 'fileUpload' in request.files:
        file = request.files['fileUpload']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            file_extension = filename.rsplit('.', 1)[1].lower()
            file_content = read_file_content(file_path, file_extension)

    if not content_input.strip() and not file_content:
        return jsonify({'error': 'No content provided.'}), 400

    content = content_input if content_input.strip() else file_content

    prompt = (f"You are an assistant that helps users improve their content for {improvement_type}. "
              f"Generate optimized content suitable for a {tone} tone aimed at {target_audience}. "
              f"The original content is: {content}")

    payload = {
        "model": "tiiuae/falcon-180B-chat",
        "messages": [
            {"role": "system", "content": prompt}
        ]
    }

    try:
        response = requests.post(api_url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload)
        response.raise_for_status()
        data = response.json()

        optimized_content = data['choices'][0]['message']['content'] if 'choices' in data else 'No optimized content available.'

        return jsonify({
            'flaws': '',  # Only if you want to keep a default message for optimization calls
            'optimizedContent': optimized_content
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

import os
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/api/ask', methods=['POST'])
def ask_lab_ai():
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'error': 'API key not configured'}), 500
    
    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': 'claude-3-5-sonnet-20241022',
                'max_tokens': 1000,
                'messages': [
                    {
                        'role': 'user',
                        'content': f'You are the Lab AI on a biology/chemistry/biotechnology learning page called Field Notes. Explain the following in plain, friendly language for a beginner, in 3-5 short sentences: {question}'
                    }
                ]
            }
        )
        
        if response.status_code != 200:
            print(f'Anthropic API error: {response.status_code} {response.text}')
            return jsonify({'error': 'API request failed'}), response.status_code
        
        data = response.json()
        text = '\n'.join([b['text'] for b in data.get('content', []) if b.get('type') == 'text'])
        
        return jsonify({'answer': text or 'Sorry, no answer came back for that.'})
    
    except Exception as error:
        print(f'Error: {error}')
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)

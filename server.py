import os
import sqlite3
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
DB_PATH = os.path.join(os.path.dirname(__file__), 'biohelix.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS high_scores (
            game TEXT PRIMARY KEY,
            best INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    conn.commit()
    conn.close()


def get_best_score(game):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT best FROM high_scores WHERE game = ?', (game,)).fetchone()
    conn.close()
    return int(row[0]) if row else 0


def upsert_best_score(game, score):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        '''
        INSERT INTO high_scores (game, best)
        VALUES (?, ?)
        ON CONFLICT(game) DO UPDATE SET
            best = CASE
                WHEN excluded.best > high_scores.best THEN excluded.best
                ELSE high_scores.best
            END,
            updated_at = CURRENT_TIMESTAMP
        ''',
        (game, score)
    )
    row = conn.execute('SELECT best FROM high_scores WHERE game = ?', (game,)).fetchone()
    conn.commit()
    conn.close()
    return int(row[0]) if row else 0


init_db()

@app.route('/')
def serve_index():
    return send_file('index.html')


@app.route('/api/highscore', methods=['GET'])
def get_highscore():
    game = (request.args.get('game') or '').strip()
    if not game:
        return jsonify({'error': 'Game is required'}), 400
    return jsonify({'game': game, 'best': get_best_score(game)})


@app.route('/api/highscore', methods=['POST'])
def save_highscore():
    data = request.get_json() or {}
    game = str(data.get('game', '')).strip()
    score_raw = data.get('score')
    if not game:
        return jsonify({'error': 'Game is required'}), 400
    if not isinstance(score_raw, int) or score_raw < 0:
        return jsonify({'error': 'Score must be a non-negative integer'}), 400

    previous_best = get_best_score(game)
    new_best = upsert_best_score(game, score_raw)
    return jsonify({
        'game': game,
        'best': new_best,
        'is_new_best': new_best > previous_best
    })

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

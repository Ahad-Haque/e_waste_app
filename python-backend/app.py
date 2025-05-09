# python-backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sqlite3

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS multiplication_results (
        id INTEGER PRIMARY KEY,
        result INTEGER
    )''')
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

@app.route('/multiply', methods=['POST'])
def multiply():
    data = request.json
    num1 = data.get('num1', 0)
    num2 = data.get('num2', 0)
    result = num1 * num2
    return jsonify({'result': result})

@app.route('/save-result', methods=['POST'])
def save_result():
    data = request.json
    result = data.get('result', 0)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if we already have a record
    cursor.execute("SELECT COUNT(*) FROM multiplication_results WHERE id = 1")
    record_exists = cursor.fetchone()[0] > 0
    
    if record_exists:
        cursor.execute("UPDATE multiplication_results SET result = ? WHERE id = 1", (result,))
    else:
        cursor.execute("INSERT INTO multiplication_results (id, result) VALUES (1, ?)", (result,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': 'Result saved'})

@app.route('/fetch-result', methods=['GET'])
def fetch_result():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT result FROM multiplication_results WHERE id = 1")
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return jsonify({'result': result[0]})
    else:
        return jsonify({'result': 'NA'})

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Python backend is running!'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
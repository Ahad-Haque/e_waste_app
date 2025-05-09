# python-backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/multiply', methods=['POST'])
def multiply():
    data = request.json
    num1 = data.get('num1', 0)
    num2 = data.get('num2', 0)
    result = num1 * num2
    return jsonify({'result': result})

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Python backend is running!'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
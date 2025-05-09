# python-backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sqlite3
import cv2
import numpy as np
import base64
import datetime
import traceback
import random  # For demo purposes

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS face_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        gender TEXT,
        age INTEGER
    )''')
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

# Global variables
face_cascade = None

def init_models():
    global face_cascade
    
    try:
        # Load face detection classifier using Haar Cascade (more reliable than DNN for our purpose)
        face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(face_cascade_path)
        
        if face_cascade.empty():
            print(f"Error: Couldn't load face cascade from {face_cascade_path}")
            return False
            
        print("Face detection model loaded successfully")
        return True
    except Exception as e:
        print(f"Error loading models: {str(e)}")
        traceback.print_exc()
        return False

def detect_face_age_gender(image_data):
    global face_cascade
    
    try:
        # Decode image
        nparr = np.frombuffer(base64.b64decode(image_data.split(',')[1]), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None or img.size == 0:
            return {"gender": "Unknown", "age": 0, "error": "Invalid image data"}
            
        # Get original dimensions for scaling
        img_height, img_width = img.shape[:2]
            
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        results = []
        
        # If at least one face is detected
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                face = img[y:y+h, x:x+w]
                
                if face.size == 0 or face.shape[0] == 0 or face.shape[1] == 0:
                    continue
                
                # Simple heuristic (not accurate, just for demonstration)
                face_ratio = w / h
                gender = "Male" if face_ratio > 0.75 else "Female"
                
                # For age, use a random value in a reasonable range (demo only)
                age = random.randint(20, 45)
                
                # Add face coordinates for frontend display
                # Convert pixel values to percentage of image dimensions for responsive display
                face_coords = {
                    "x": float(x) / img_width,
                    "y": float(y) / img_height,
                    "width": float(w) / img_width,
                    "height": float(h) / img_height
                }
                
                results.append({
                    "gender": gender,
                    "age": age,
                    "gender_confidence": 60.0,
                    "age_confidence": 50.0,
                    "face_confidence": 95.0,
                    "face_coords": face_coords
                })
        
        # Return the first face detected (or empty if none)
        return results[0] if results else {"gender": "Unknown", "age": 0, "error": "No face detected"}
    
    except Exception as e:
        print(f"Error in face detection: {str(e)}")
        traceback.print_exc()
        return {"gender": "Unknown", "age": 0, "error": str(e)}

@app.route('/detect-face', methods=['POST'])
def detect_face():
    data = request.json
    image_data = data.get('image', '')
    
    if not image_data:
        return jsonify({'error': 'No image provided'}), 400
        
    try:
        result = detect_face_age_gender(image_data)
        return jsonify(result)
    except Exception as e:
        print(f"Error in face detection: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/save-face-data', methods=['POST'])
def save_face_data():
    data = request.json
    gender = data.get('gender', 'Unknown')
    age = data.get('age', 0)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO face_data (timestamp, gender, age) VALUES (?, ?, ?)", 
        (timestamp, gender, age)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': 'Face data saved'})

@app.route('/fetch-latest', methods=['GET'])
def fetch_latest():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT timestamp, gender, age FROM face_data ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return jsonify({
            'timestamp': result[0],
            'gender': result[1],
            'age': result[2]
        })
    else:
        return jsonify({'message': 'No data found'})

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Python backend is running!'})

# Initialize models before starting the Flask app
if __name__ == '__main__':
    if init_models():
        print("Models initialized successfully!")
        app.run(host='127.0.0.1', port=5000, debug=True)
    else:
        print("Failed to initialize models. Application will not work correctly.")
# python-backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sqlite3
import cv2
import numpy as np
import base64
import datetime

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

# Global variables for the networks
face_net = None
age_net = None
gender_net = None

# Model mean values
MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)

# Age ranges
age_list = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
# Gender list
gender_list = ['Male', 'Female']

def init_models():
    global face_net, age_net, gender_net
    
    # Paths for models
    current_dir = os.path.dirname(os.path.abspath(__file__))
    FACE_PROTO = os.path.join(current_dir, 'models', 'deploy.prototxt.txt')
    FACE_MODEL = os.path.join(current_dir, 'models', 'res10_300x300_ssd_iter_140000_fp16.caffemodel')
    AGE_PROTO = os.path.join(current_dir, 'models', 'deploy_age.prototxt')
    AGE_MODEL = os.path.join(current_dir, 'models', 'age_net.caffemodel')
    GENDER_PROTO = os.path.join(current_dir, 'models', 'deploy_gender.prototxt')
    GENDER_MODEL = os.path.join(current_dir, 'models', 'gender_net.caffemodel')
    
    try:
        print(f"Loading face model from {FACE_PROTO} and {FACE_MODEL}")
        face_net = cv2.dnn.readNet(FACE_MODEL, FACE_PROTO)
        print("Face model loaded successfully")
        
        print(f"Loading age model from {AGE_PROTO} and {AGE_MODEL}")
        age_net = cv2.dnn.readNet(AGE_MODEL, AGE_PROTO)
        print("Age model loaded successfully")
        
        print(f"Loading gender model from {GENDER_PROTO} and {GENDER_MODEL}")
        gender_net = cv2.dnn.readNet(GENDER_MODEL, GENDER_PROTO)
        print("Gender model loaded successfully")
        
        return True
    except Exception as e:
        print(f"Error loading models: {str(e)}")
        # Check if all files exist
        for file_path in [FACE_PROTO, FACE_MODEL, AGE_PROTO, AGE_MODEL, GENDER_PROTO, GENDER_MODEL]:
            if os.path.exists(file_path):
                print(f"File exists: {file_path}")
            else:
                print(f"File DOES NOT exist: {file_path}")
        return False

def detect_face_age_gender(image_data):
    global face_net, age_net, gender_net
    
    # Decode image
    nparr = np.frombuffer(base64.b64decode(image_data.split(',')[1]), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Get original dimensions
    original_h, original_w = img.shape[:2]
    
    # Create a 4D blob from image
    blob = cv2.dnn.blobFromImage(img, 1.0, (300, 300), [104, 117, 123], swapRB=False, crop=False)
    
    # Set input to network and make a pass through the network
    face_net.setInput(blob)
    detections = face_net.forward()
    
    results = []
    
    # Loop over the detections
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        
        # Filter out weak detections
        if confidence > 0.5:
            # Get the coordinates of the face detection
            box = detections[0, 0, i, 3:7] * np.array([original_w, original_h, original_w, original_h])
            (x1, y1, x2, y2) = box.astype("int")
            
            # Ensure coordinates are within the image
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(original_w, x2), min(original_h, y2)
            
            # Extract the face ROI
            face = img[y1:y2, x1:x2]
            
            if face.size == 0:
                continue
                
            # Create a 4D blob for gender detection
            blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
            
            # Gender detection
            gender_net.setInput(blob)
            gender_preds = gender_net.forward()
            gender_idx = gender_preds[0].argmax()
            gender = gender_list[gender_idx]
            gender_confidence = gender_preds[0][gender_idx] * 100
            
            # Age detection
            age_net.setInput(blob)
            age_preds = age_net.forward()
            age_idx = age_preds[0].argmax()
            age = age_list[age_idx]
            age_confidence = age_preds[0][age_idx] * 100
            
            # Extract numeric age from the range
            age_min = int(age.split('-')[0].replace('(', ''))
            age_max = int(age.split('-')[1].replace(')', ''))
            avg_age = (age_min + age_max) // 2
            
            results.append({
                "gender": gender,
                "age": avg_age,
                "gender_confidence": float(gender_confidence),
                "age_confidence": float(age_confidence)
            })
    
    # Return the first face detected (or empty if none)
    return results[0] if results else {"gender": "Unknown", "age": 0, "gender_confidence": 0, "age_confidence": 0}

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
# python-backend/app.py

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import os
import sqlite3
import cv2
import numpy as np
import base64
import datetime
import traceback
import random
import json
from pathlib import Path
import threading
import time

app = Flask(__name__)

# Configure CORS properly
CORS(app, 
     origins='*',
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'OPTIONS'],
     expose_headers=['Content-Range', 'X-Content-Range'])

# Add after_request handler to ensure CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Database and storage paths
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'database.db')
PHOTOS_DIR = os.path.join(BASE_DIR, 'photos')
VIP_MODELS_DIR = os.path.join(BASE_DIR, 'vip_models')

# Ensure required directories exist
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(VIP_MODELS_DIR, exist_ok=True)

# Global variables
face_cascade = None
vip_recognizers = {}  # Will store VIP face recognizers when implemented

def init_db():
    """Initialize the SQLite database with all required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Face detection data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS face_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        gender TEXT,
        age INTEGER,
        vip_id INTEGER DEFAULT NULL,
        detection_confidence REAL DEFAULT 0.0
    )''')
    
    # VIP flow states table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vip_flow_states (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vip_id INTEGER,
        flow_state TEXT,
        selected_box TEXT,
        selected_rating INTEGER,
        timestamp TEXT,
        is_active BOOLEAN DEFAULT 1
    )''')
    
    # Feedback/ratings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vip_id INTEGER,
        rating INTEGER,
        timestamp TEXT,
        photo_taken BOOLEAN DEFAULT 0
    )''')
    
    # Photos table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vip_id INTEGER,
        photo_path TEXT,
        timestamp TEXT,
        rating_id INTEGER,
        FOREIGN KEY (rating_id) REFERENCES ratings (id)
    )''')
    
    # Waste disposal records
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS waste_disposal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vip_id INTEGER,
        waste_type TEXT,
        box_number TEXT,
        timestamp TEXT
    )''')
    
    # VIP profile table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vip_profiles (
        vip_id INTEGER PRIMARY KEY,
        name TEXT,
        gender TEXT,
        age INTEGER,
        registration_date TEXT,
        total_disposals INTEGER DEFAULT 0,
        average_rating REAL DEFAULT 0.0
    )''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def init_models():
    """Initialize computer vision models"""
    global face_cascade
    
    try:
        # Load face detection classifier
        face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(face_cascade_path)
        
        if face_cascade.empty():
            print(f"Error: Couldn't load face cascade from {face_cascade_path}")
            return False
            
        print("Face detection model loaded successfully")
        
        # TODO: Load VIP recognition models if they exist
        # load_vip_models()
        
        return True
    except Exception as e:
        print(f"Error loading models: {str(e)}")
        traceback.print_exc()
        return False

def detect_face_age_gender(image_data):
    """Detect face, estimate age and gender"""
    global face_cascade
    
    try:
        # Decode image
        header, encoded = image_data.split(',', 1)
        nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None or img.size == 0:
            return {"gender": "Unknown", "age": 0, "error": "Invalid image data"}
            
        # Get original dimensions for scaling
        img_height, img_width = img.shape[:2]
            
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        
        results = []
        
        # Process detected faces
        for (x, y, w, h) in faces:
            # Extract face region
            face_roi = img[y:y+h, x:x+w]
            
            if face_roi.size == 0:
                continue
            
            # Simple heuristic for gender (replace with actual model)
            face_ratio = w / h
            gender = "Male" if face_ratio > 0.9 else "Female"
            
            # Simple age estimation (replace with actual model)
            # Using face size and position as rough indicators
            face_area = w * h
            age = 25 + int(face_area / 1000) + random.randint(-5, 5)
            age = max(18, min(65, age))  # Clamp between 18-65
            
            # Calculate face coordinates as percentages
            face_coords = {
                "x": float(x) / img_width,
                "y": float(y) / img_height,
                "width": float(w) / img_width,
                "height": float(h) / img_height
            }
            
            # Check if face is in center detection area
            face_center_x = x + w/2
            face_center_y = y + h/2
            img_center_x = img_width / 2
            img_center_y = img_height / 2
            
            # Calculate if face is in detection circle (300px radius)
            distance_from_center = np.sqrt(
                (face_center_x - img_center_x)**2 + 
                (face_center_y - img_center_y)**2
            )
            
            detection_radius = 150  # Half of 300px circle
            in_detection_area = distance_from_center < detection_radius
            
            result = {
                "gender": gender,
                "age": age,
                "gender_confidence": random.uniform(75, 95),
                "age_confidence": random.uniform(70, 90),
                "face_confidence": 85.0 + random.uniform(0, 10),
                "face_coords": face_coords,
                "in_detection_area": in_detection_area
            }
            
            # Add VIP detection placeholder
            # TODO: Implement actual VIP recognition here
            result["is_vip"] = False
            result["vip_id"] = None
            
            results.append(result)
        
        # Return the first face in detection area, or first face if none in area
        in_area_faces = [r for r in results if r.get("in_detection_area", False)]
        return in_area_faces[0] if in_area_faces else (results[0] if results else {
            "gender": "Unknown", 
            "age": 0, 
            "error": "No face detected"
        })
    
    except Exception as e:
        print(f"Error in face detection: {str(e)}")
        traceback.print_exc()
        return {"gender": "Unknown", "age": 0, "error": str(e)}

@app.route('/test', methods=['GET'])
@cross_origin()
def test():
    """Test endpoint to check backend connectivity"""
    return jsonify({
        'message': 'Python backend is running!',
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'database': 'Connected' if os.path.exists(DB_PATH) else 'Not found'
    })

@app.route('/detect-face', methods=['POST', 'OPTIONS'])
@cross_origin()
def detect_face():
    """Face detection endpoint"""
    if request.method == 'OPTIONS':
        return make_response('', 204)
        
    data = request.json
    image_data = data.get('image', '')
    
    if not image_data:
        return jsonify({'error': 'No image provided'}), 400
        
    try:
        result = detect_face_age_gender(image_data)
        
        # Save detection data if valid
        if not result.get('error'):
            save_face_data(result)
        
        return jsonify(result)
    except Exception as e:
        print(f"Error in face detection endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/save-face-data', methods=['POST'])
@cross_origin()
def save_face_data_endpoint():
    """Save face detection data"""
    data = request.json
    gender = data.get('gender', 'Unknown')
    age = data.get('age', 0)
    vip_id = data.get('vip_id', None)
    confidence = data.get('confidence', 0.0)
    
    save_face_data({
        'gender': gender,
        'age': age,
        'vip_id': vip_id,
        'face_confidence': confidence
    })
    
    return jsonify({'status': 'success', 'message': 'Face data saved'})

def save_face_data(data):
    """Helper function to save face data to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            """INSERT INTO face_data (timestamp, gender, age, vip_id, detection_confidence) 
               VALUES (?, ?, ?, ?, ?)""", 
            (timestamp, 
             data.get('gender', 'Unknown'), 
             data.get('age', 0),
             data.get('vip_id'),
             data.get('face_confidence', 0.0))
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving face data: {str(e)}")

@app.route('/save-vip-state', methods=['POST'])
@cross_origin()
def save_vip_state():
    """Save VIP flow state"""
    try:
        data = request.json
        vip_id = data.get('vip_id')
        flow_state = data.get('flow_state')
        selected_box = data.get('selected_box', '')
        selected_rating = data.get('selected_rating', 0)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Deactivate previous states for this VIP
        cursor.execute(
            "UPDATE vip_flow_states SET is_active = 0 WHERE vip_id = ?",
            (vip_id,)
        )
        
        # Insert new state
        cursor.execute(
            """INSERT INTO vip_flow_states 
               (vip_id, flow_state, selected_box, selected_rating, timestamp, is_active)
               VALUES (?, ?, ?, ?, ?, 1)""",
            (vip_id, flow_state, selected_box, selected_rating, timestamp)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error saving VIP state: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-vip-state', methods=['GET'])
@cross_origin()
def get_vip_state():
    """Get VIP flow state"""
    try:
        vip_id = request.args.get('vip_id')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT flow_state, selected_box, selected_rating, timestamp
               FROM vip_flow_states
               WHERE vip_id = ? AND is_active = 1
               ORDER BY timestamp DESC
               LIMIT 1""",
            (vip_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({
                'flow_state': result[0],
                'selected_box': result[1],
                'selected_rating': result[2],
                'timestamp': result[3]
            })
        else:
            return jsonify({'message': 'No active state found'})
            
    except Exception as e:
        print(f"Error getting VIP state: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/save-rating', methods=['POST'])
@cross_origin()
def save_rating():
    """Save user rating"""
    try:
        data = request.json
        vip_id = data.get('vip_id')
        rating = data.get('rating')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            """INSERT INTO ratings (vip_id, rating, timestamp, photo_taken)
               VALUES (?, ?, ?, 0)""",
            (vip_id, rating, timestamp)
        )
        
        rating_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'rating_id': rating_id
        })
    except Exception as e:
        print(f"Error saving rating: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/save-photo', methods=['POST'])
@cross_origin()
def save_photo():
    """Save VIP photo"""
    try:
        data = request.json
        photo_data = data.get('photo')
        vip_id = data.get('vip_id')
        rating_id = data.get('rating_id')
        
        # Generate unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vip_{vip_id}_{timestamp}.jpg"
        filepath = os.path.join(PHOTOS_DIR, filename)
        
        # Save photo file
        header, encoded = photo_data.split(',', 1)
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(encoded))
        
        # Save photo record
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO photos (vip_id, photo_path, timestamp, rating_id)
               VALUES (?, ?, ?, ?)""",
            (vip_id, filepath, timestamp, rating_id)
        )
        
        # Update rating record
        cursor.execute(
            "UPDATE ratings SET photo_taken = 1 WHERE id = ?",
            (rating_id,)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'photo_path': filepath
        })
    except Exception as e:
        print(f"Error saving photo: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/save-waste-disposal', methods=['POST'])
@cross_origin()
def save_waste_disposal():
    """Record waste disposal"""
    try:
        data = request.json
        vip_id = data.get('vip_id')
        waste_type = data.get('waste_type')
        box_number = data.get('box_number')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            """INSERT INTO waste_disposal (vip_id, waste_type, box_number, timestamp)
               VALUES (?, ?, ?, ?)""",
            (vip_id, waste_type, box_number, timestamp)
        )
        
        # Update VIP profile disposal count
        cursor.execute(
            """UPDATE vip_profiles 
               SET total_disposals = total_disposals + 1
               WHERE vip_id = ?""",
            (vip_id,)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error saving waste disposal: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-vip-stats', methods=['GET'])
@cross_origin()
def get_vip_stats():
    """Get VIP statistics"""
    try:
        vip_id = request.args.get('vip_id')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get VIP profile
        cursor.execute(
            "SELECT * FROM vip_profiles WHERE vip_id = ?",
            (vip_id,)
        )
        profile = cursor.fetchone()
        
        # Get disposal history
        cursor.execute(
            """SELECT waste_type, box_number, timestamp 
               FROM waste_disposal 
               WHERE vip_id = ? 
               ORDER BY timestamp DESC 
               LIMIT 10""",
            (vip_id,)
        )
        disposals = cursor.fetchall()
        
        # Get rating history
        cursor.execute(
            """SELECT rating, timestamp, photo_taken 
               FROM ratings 
               WHERE vip_id = ? 
               ORDER BY timestamp DESC 
               LIMIT 10""",
            (vip_id,)
        )
        ratings = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'profile': profile,
            'recent_disposals': disposals,
            'rating_history': ratings
        })
    except Exception as e:
        print(f"Error getting VIP stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/fetch-latest', methods=['GET'])
@cross_origin()
def fetch_latest():
    """Fetch latest face detection data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT timestamp, gender, age, vip_id 
               FROM face_data 
               ORDER BY id DESC 
               LIMIT 1"""
        )
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return jsonify({
                'timestamp': result[0],
                'gender': result[1],
                'age': result[2],
                'vip_id': result[3]
            })
        else:
            return jsonify({'message': 'No data found'})
    except Exception as e:
        print(f"Error fetching latest: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'services': {
            'database': 'running' if os.path.exists(DB_PATH) else 'error',
            'face_detection': 'running' if face_cascade is not None else 'error',
            'storage': 'running' if os.path.exists(PHOTOS_DIR) else 'error'
        }
    })

# Initialize everything when the app starts
if __name__ == '__main__':
    # Create database and tables
    init_db()
    
    # Load computer vision models
    if init_models():
        print("All models initialized successfully!")
        print(f"Starting server on http://127.0.0.1:5000")
        print("Database path:", DB_PATH)
        print("Photos directory:", PHOTOS_DIR)
        app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
    else:
        print("Failed to initialize models. Some features may not work correctly.")
        print("Starting server anyway...")
        app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
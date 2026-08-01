from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv
import uuid

load_dotenv()

app = Flask(__name__)
CORS(app)

# ==========================================
# FIREBASE CONFIGURATION (DIRECT)
# ==========================================
# Your Firebase config from earlier
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyBcwLsODrVRzw6MlUluBs3U7JaKf1fWm0A",
    "authDomain": "spal-lab-data.firebaseapp.com",
    "databaseURL": "https://spal-lab-data-default-rtdb.firebaseio.com",
    "projectId": "spal-lab-data",
    "storageBucket": "spal-lab-data.firebasestorage.app",
    "messagingSenderId": "899013208966",
    "appId": "1:899013208966:web:0f199c781ea07cd53c9a07"
}

# Initialize Firebase (using service account or direct config)
try:
    # Try using service account first (more secure)
    cred_path = os.getenv('FIREBASE_CREDENTIALS', 'serviceAccountKey.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_CONFIG['databaseURL']
        })
        print('✅ Firebase initialized with service account!')
    else:
        # Fallback: Use project ID (limited access)
        firebase_admin.initialize_app(options={
            'projectId': FIREBASE_CONFIG['projectId'],
            'databaseURL': FIREBASE_CONFIG['databaseURL']
        })
        print('✅ Firebase initialized with project ID!')
except Exception as e:
    print(f'⚠️ Firebase init error: {e}')
    print('⚠️ Running in local-only mode')

# ==========================================
# DATA FUNCTIONS
# ==========================================
def get_data():
    """Get data from Firebase or local"""
    data = {'team': [], 'publications': [], 'news': [], 'awards': []}
    
    try:
        ref = db.reference('spal_data')
        firebase_data = ref.get()
        if firebase_data:
            return firebase_data
    except Exception as e:
        print(f'⚠️ Firebase read error: {e}')
    
    # Fallback to local JSON
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r') as f:
                return json.load(f)
        except:
            pass
    
    return data

def save_data(data):
    """Save data to Firebase and local"""
    try:
        ref = db.reference('spal_data')
        ref.set(data)
        print('✅ Saved to Firebase!')
    except Exception as e:
        print(f'⚠️ Firebase save error: {e}')
    
    # Always save locally as backup
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=2)
    print('✅ Saved to local!')

# ==========================================
# INITIAL DATA
# ==========================================
def init_data():
    """Initialize default data if empty"""
    data = get_data()
    if not data or not data.get('team'):
        default_data = {
            'team': [
                {'id': 1, 'name': 'Md Faruk Hossain', 'role': 'Research Assistant', 
                 'bio': 'AIoT, Smart Farming', 'category': 'current', 'image': 'faruk.jpg'},
                {'id': 2, 'name': 'Kazi Md Mehedi Hasan', 'role': 'Research Assistant', 
                 'bio': 'IoT, Sensor Networks', 'category': 'current', 'image': 'mehedi.jpg'},
                {'id': 3, 'name': 'Rayhan Mahmud', 'role': 'Research Assistant', 
                 'bio': 'Drone Systems, ML', 'category': 'current', 'image': 'rayhan.jpg'},
                {'id': 4, 'name': 'Digonta Chandra Roy', 'role': 'Research Assistant', 
                 'bio': 'AI, Drone Systems', 'category': 'current', 'image': 'digonta.jpg'},
                {'id': 5, 'name': 'Md Mamunur Rashid', 'role': 'MS Student', 
                 'bio': 'CNU, South Korea', 'category': 'alumni', 'image': 'rashid.jpg'},
                {'id': 6, 'name': 'Md Ashikur Rahman', 'role': 'MS Student', 
                 'bio': 'CNU, South Korea', 'category': 'alumni', 'image': 'ashikur.jpg'},
                {'id': 7, 'name': 'Md Sakib Robin', 'role': 'MS Student', 
                 'bio': 'CNU, South Korea', 'category': 'alumni', 'image': 'robin.jpg'}
            ],
            'publications': [
                {'id': 1, 'title': 'Smart Evaporative Cooling Storage System', 
                 'authors': 'Mahmud, M.R., et al.', 'journal': 'IOCAG 2025', 'year': 2025}
            ],
            'news': [
                {'id': 1, 'title': 'SPAL Lab Launch', 
                 'date': '2025-01-15', 'content': 'SPAL officially launched.', 'author': 'Admin'}
            ],
            'awards': [
                {'id': 1, 'title': 'Best Paper Award – IOCAG 2025'}
            ]
        }
        save_data(default_data)
        return default_data
    return data

# ==========================================
# API ROUTES
# ==========================================

@app.route('/')
def index():
    return jsonify({
        'status': 'SPAL Backend Running',
        'version': '1.0',
        'timestamp': datetime.now().isoformat()
    })

# ==========================================
# TEAM CRUD
# ==========================================

@app.route('/api/data', methods=['GET'])
def get_all_data():
    data = get_data()
    return jsonify(data)

@app.route('/api/team', methods=['GET'])
def get_team():
    data = get_data()
    return jsonify(data.get('team', []))

@app.route('/api/team', methods=['POST'])
def add_team_member():
    data = get_data()
    new_member = request.json
    
    if not new_member.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    # Generate ID
    max_id = max([m.get('id', 0) for m in data.get('team', [])]) if data.get('team') else 0
    new_member['id'] = max_id + 1
    new_member['created_at'] = datetime.now().isoformat()
    
    if 'team' not in data:
        data['team'] = []
    data['team'].append(new_member)
    save_data(data)
    
    return jsonify({'success': True, 'data': new_member}), 201

@app.route('/api/team/<int:id>', methods=['PUT'])
def update_team_member(id):
    data = get_data()
    for member in data.get('team', []):
        if member['id'] == id:
            updates = request.json
            member.update(updates)
            member['updated_at'] = datetime.now().isoformat()
            save_data(data)
            return jsonify({'success': True, 'data': member})
    return jsonify({'error': 'Member not found'}), 404

@app.route('/api/team/<int:id>', methods=['DELETE'])
def delete_team_member(id):
    data = get_data()
    original_len = len(data.get('team', []))
    data['team'] = [m for m in data.get('team', []) if m['id'] != id]
    
    if len(data['team']) < original_len:
        save_data(data)
        return jsonify({'success': True, 'message': 'Member deleted'})
    return jsonify({'error': 'Member not found'}), 404

# ==========================================
# PUBLICATIONS CRUD
# ==========================================

@app.route('/api/publications', methods=['GET'])
def get_publications():
    data = get_data()
    return jsonify(data.get('publications', []))

@app.route('/api/publications', methods=['POST'])
def add_publication():
    data = get_data()
    new_pub = request.json
    
    if not new_pub.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    max_id = max([p.get('id', 0) for p in data.get('publications', [])]) if data.get('publications') else 0
    new_pub['id'] = max_id + 1
    new_pub['created_at'] = datetime.now().isoformat()
    
    if 'publications' not in data:
        data['publications'] = []
    data['publications'].append(new_pub)
    save_data(data)
    
    return jsonify({'success': True, 'data': new_pub}), 201

@app.route('/api/publications/<int:id>', methods=['DELETE'])
def delete_publication(id):
    data = get_data()
    original_len = len(data.get('publications', []))
    data['publications'] = [p for p in data.get('publications', []) if p['id'] != id]
    
    if len(data['publications']) < original_len:
        save_data(data)
        return jsonify({'success': True, 'message': 'Publication deleted'})
    return jsonify({'error': 'Publication not found'}), 404

# ==========================================
# NEWS CRUD
# ==========================================

@app.route('/api/news', methods=['GET'])
def get_news():
    data = get_data()
    return jsonify(data.get('news', []))

@app.route('/api/news', methods=['POST'])
def add_news():
    data = get_data()
    new_news = request.json
    
    if not new_news.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    max_id = max([n.get('id', 0) for n in data.get('news', [])]) if data.get('news') else 0
    new_news['id'] = max_id + 1
    new_news['created_at'] = datetime.now().isoformat()
    
    if 'news' not in data:
        data['news'] = []
    data['news'].append(new_news)
    save_data(data)
    
    return jsonify({'success': True, 'data': new_news}), 201

@app.route('/api/news/<int:id>', methods=['DELETE'])
def delete_news(id):
    data = get_data()
    original_len = len(data.get('news', []))
    data['news'] = [n for n in data.get('news', []) if n['id'] != id]
    
    if len(data['news']) < original_len:
        save_data(data)
        return jsonify({'success': True, 'message': 'News deleted'})
    return jsonify({'error': 'News not found'}), 404

# ==========================================
# AWARDS CRUD
# ==========================================

@app.route('/api/awards', methods=['GET'])
def get_awards():
    data = get_data()
    return jsonify(data.get('awards', []))

@app.route('/api/awards', methods=['POST'])
def add_award():
    data = get_data()
    new_award = request.json
    
    if not new_award.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    max_id = max([a.get('id', 0) for a in data.get('awards', [])]) if data.get('awards') else 0
    new_award['id'] = max_id + 1
    new_award['created_at'] = datetime.now().isoformat()
    
    if 'awards' not in data:
        data['awards'] = []
    data['awards'].append(new_award)
    save_data(data)
    
    return jsonify({'success': True, 'data': new_award}), 201

@app.route('/api/awards/<int:id>', methods=['DELETE'])
def delete_award(id):
    data = get_data()
    original_len = len(data.get('awards', []))
    data['awards'] = [a for a in data.get('awards', []) if a['id'] != id]
    
    if len(data['awards']) < original_len:
        save_data(data)
        return jsonify({'success': True, 'message': 'Award deleted'})
    return jsonify({'error': 'Award not found'}), 404

# ==========================================
# INIT DATA
# ==========================================
init_data()

# ==========================================
# RUN
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

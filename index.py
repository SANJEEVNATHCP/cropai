"""
Vercel Serverless Function Entry Point
"""
import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set environment variables for Vercel
os.environ.setdefault('FLASK_ENV', 'production')

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.join(project_root, 'frontend', 'templates'),
            static_folder=os.path.join(project_root, 'frontend', 'static'))

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'crop-yield-secret-key-2025')
app.config['DEBUG'] = False

# Use in-memory SQLite for Vercel (serverless)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CORS configuration
CORS(app, origins=['*'], supports_credentials=True)

# Initialize database
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# Define models inline for Vercel
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    state = db.Column(db.String(50))
    district = db.Column(db.String(50))
    farm_size = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=db.func.now())

class PredictionHistory(db.Model):
    __tablename__ = 'prediction_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    crop = db.Column(db.String(50))
    state = db.Column(db.String(50))
    predicted_yield = db.Column(db.Float)
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=db.func.now())

# Create tables
with app.app_context():
    db.create_all()

# ============= ROUTES =============

# Static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# Page routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/yield')
def yield_page():
    return render_template('yield.html')

@app.route('/recommendation')
def recommendation_page():
    return render_template('recommendation.html')

@app.route('/weather')
def weather_page():
    return render_template('weather.html')

@app.route('/voice-agent')
def voice_agent_page():
    return render_template('voice_agent.html')


# ============= YIELD PREDICTION API =============
import requests as http_requests

CROP_DATA = {
    'rice': {'base_yield': 4500, 'water_need': 'high', 'season': ['Kharif']},
    'wheat': {'base_yield': 3500, 'water_need': 'medium', 'season': ['Rabi']},
    'maize': {'base_yield': 5000, 'water_need': 'medium', 'season': ['Kharif', 'Rabi']},
    'cotton': {'base_yield': 500, 'water_need': 'medium', 'season': ['Kharif']},
    'sugarcane': {'base_yield': 70000, 'water_need': 'high', 'season': ['Kharif']},
    'soybean': {'base_yield': 2000, 'water_need': 'medium', 'season': ['Kharif']},
    'groundnut': {'base_yield': 1800, 'water_need': 'low', 'season': ['Kharif', 'Rabi']},
    'potato': {'base_yield': 25000, 'water_need': 'medium', 'season': ['Rabi']},
    'tomato': {'base_yield': 30000, 'water_need': 'medium', 'season': ['Rabi', 'Zaid']},
    'onion': {'base_yield': 20000, 'water_need': 'low', 'season': ['Rabi', 'Kharif']},
    'mustard': {'base_yield': 1200, 'water_need': 'low', 'season': ['Rabi']},
    'chickpea': {'base_yield': 1000, 'water_need': 'low', 'season': ['Rabi']},
    'bajra': {'base_yield': 1500, 'water_need': 'low', 'season': ['Kharif']},
    'jowar': {'base_yield': 1200, 'water_need': 'low', 'season': ['Kharif', 'Rabi']}
}

STATES = ['Punjab', 'Haryana', 'Uttar Pradesh', 'West Bengal', 'Andhra Pradesh', 
          'Tamil Nadu', 'Karnataka', 'Maharashtra', 'Madhya Pradesh', 'Gujarat', 
          'Rajasthan', 'Bihar', 'Odisha', 'Assam', 'Jharkhand', 'Chhattisgarh', 
          'Kerala', 'Telangana']

STATE_CAPITALS = {
    'Punjab': 'Chandigarh', 'Haryana': 'Chandigarh', 'Uttar Pradesh': 'Lucknow',
    'West Bengal': 'Kolkata', 'Andhra Pradesh': 'Amaravati', 'Tamil Nadu': 'Chennai',
    'Karnataka': 'Bangalore', 'Maharashtra': 'Mumbai', 'Madhya Pradesh': 'Bhopal',
    'Gujarat': 'Ahmedabad', 'Rajasthan': 'Jaipur', 'Bihar': 'Patna',
    'Odisha': 'Bhubaneswar', 'Assam': 'Guwahati', 'Jharkhand': 'Ranchi',
    'Chhattisgarh': 'Raipur', 'Kerala': 'Thiruvananthapuram', 'Telangana': 'Hyderabad'
}

OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', 'b576d8a952bf4c45c7ef5bddb148e76b')

@app.route('/api/yield/crops', methods=['GET'])
def get_crops():
    crops = [{'name': k.title(), 'value': k, 'avg_yield': v['base_yield']} for k, v in CROP_DATA.items()]
    return jsonify({'success': True, 'crops': crops})

@app.route('/api/yield/states', methods=['GET'])
def get_states():
    return jsonify({'success': True, 'states': STATES})

@app.route('/api/yield/predict', methods=['POST'])
def predict_yield():
    try:
        data = request.get_json()
        crop = data.get('crop', '').lower()
        state = data.get('state', '')
        season = data.get('season', 'Kharif')
        area = float(data.get('area', 1))
        
        if crop not in CROP_DATA:
            return jsonify({'success': False, 'error': 'Invalid crop'}), 400
            
        crop_info = CROP_DATA[crop]
        base_yield = crop_info['base_yield']
        
        # Calculate factors
        nitrogen = float(data.get('nitrogen', 80))
        phosphorus = float(data.get('phosphorus', 40))
        potassium = float(data.get('potassium', 40))
        ph = float(data.get('ph', 6.5))
        
        soil_factor = min(1.3, max(0.7, (nitrogen/100 + phosphorus/50 + potassium/50) / 3))
        ph_factor = 1.0 - abs(ph - 6.5) * 0.1
        season_factor = 1.1 if season in crop_info['season'] else 0.85
        weather_factor = 1.0
        
        predicted_yield = int(base_yield * soil_factor * ph_factor * season_factor * weather_factor)
        total_yield = int(predicted_yield * area)
        confidence = min(95, int(75 + (soil_factor * 10) + (ph_factor * 5)))
        
        category = 'Excellent' if predicted_yield > base_yield * 1.1 else 'Good' if predicted_yield > base_yield * 0.9 else 'Average' if predicted_yield > base_yield * 0.7 else 'Below Average'
        
        return jsonify({
            'success': True,
            'prediction': {
                'predicted_yield': predicted_yield,
                'total_yield': total_yield,
                'base_yield': base_yield,
                'confidence': confidence,
                'category': category,
                'factors': {
                    'soil_factor': round(soil_factor, 2),
                    'weather_factor': round(weather_factor, 2),
                    'season_factor': round(season_factor, 2)
                },
                'insights': [f'{crop.title()} grows well in {season} season', f'Soil conditions are {"optimal" if soil_factor > 1 else "fair"}'],
                'recommendations': ['Consider adding organic matter', 'Monitor water levels regularly']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= RECOMMENDATION API =============
@app.route('/api/recommend/states', methods=['GET'])
def recommend_states():
    return jsonify({'success': True, 'states': STATES})

@app.route('/api/recommend/get', methods=['POST'])
def get_recommendations():
    try:
        data = request.get_json()
        state = data.get('state', 'Punjab')
        season = data.get('season', 'Kharif')
        
        recommendations = []
        for crop_name, crop_info in list(CROP_DATA.items())[:5]:
            score = 85 if season in crop_info['season'] else 65
            recommendations.append({
                'crop': crop_name.title(),
                'score': score,
                'suitability': 'Excellent' if score >= 80 else 'Good',
                'reasons': [f'Suitable for {season} season', f'Good yield potential in {state}'],
                'financials': {
                    'investment_per_ha': 25000,
                    'expected_profit_per_ha': 35000,
                    'roi_percent': 140
                },
                'details': {
                    'duration_days': 120,
                    'water_need': crop_info['water_need'],
                    'risk_level': 'Low'
                }
            })
        
        return jsonify({'success': True, 'recommendations': sorted(recommendations, key=lambda x: x['score'], reverse=True)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= WEATHER API =============
@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    city = request.args.get('city', 'Delhi')
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={OPENWEATHER_API_KEY}&units=metric"
        response = http_requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'source': 'live',
                'city': city,
                'weather': {
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'description': data['weather'][0]['description'],
                    'icon': data['weather'][0]['icon']
                }
            })
    except:
        pass
    return jsonify({'success': True, 'source': 'fallback', 'city': city, 'weather': {'temperature': 25, 'humidity': 60, 'description': 'Clear'}})

@app.route('/api/weather/forecast', methods=['GET'])
def get_forecast():
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    forecast = [{'day_short': days[i], 'temp_max': 30+i, 'temp_min': 20+i, 'condition': 'Clear', 'icon': '☀️', 'rain_chance': 10+i*5} for i in range(7)]
    return jsonify({'success': True, 'forecast': forecast})

@app.route('/api/weather/alerts', methods=['GET'])
def get_alerts():
    return jsonify({'success': True, 'alerts': []})

@app.route('/api/weather/advice', methods=['GET'])
def get_advice():
    return jsonify({'success': True, 'advice': [{'category': 'Irrigation', 'message': 'Good day for irrigation', 'priority': 'medium'}]})


# ============= VOICE AGENT API =============
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDLwxWh3Ap9D5MrUI7Pz889HaIk8LEG1JY')
GEMINI_MODEL = 'gemini-2.0-flash'

SUPPORTED_LANGUAGES = {
    'en': 'English', 'hi': 'हिंदी', 'mr': 'मराठी', 'te': 'తెలుగు',
    'ta': 'தமிழ்', 'kn': 'ಕನ್ನಡ', 'bn': 'বাংলা', 'gu': 'ગુજરાતી',
    'pa': 'ਪੰਜਾਬੀ', 'or': 'ଓଡ଼ିଆ', 'ml': 'മലയാളം'
}

@app.route('/api/voice/languages', methods=['GET'])
def get_languages():
    langs = [{'code': k, 'name': v, 'native': v} for k, v in SUPPORTED_LANGUAGES.items()]
    return jsonify({'success': True, 'languages': langs})

@app.route('/api/voice/translations/<lang>', methods=['GET'])
def get_translations(lang):
    translations = {
        'pageTitle': 'AI Voice Agent',
        'quickQuestions': 'Quick Questions',
        'selectLanguage': 'Select Language',
        'typeMessage': 'Type your message...',
        'ready': 'Ready to help you',
        'listening': 'Listening...',
        'speaking': 'Speaking...'
    }
    return jsonify({'success': True, 'translations': translations})

@app.route('/api/voice/topics', methods=['GET'])
def get_topics():
    topics = [
        {'id': 1, 'text': 'How to increase crop yield?'},
        {'id': 2, 'text': 'Best fertilizers for wheat?'},
        {'id': 3, 'text': 'When to plant rice?'}
    ]
    return jsonify({'success': True, 'topics': topics})

@app.route('/api/voice/chat', methods=['POST'])
def voice_chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        language = data.get('language', 'en')
        
        lang_name = SUPPORTED_LANGUAGES.get(language, 'English')
        
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}'
        
        system_prompt = f"""You are Krishi AI, an agricultural expert assistant. 
Respond in {lang_name} language. Be helpful, concise, and practical.
Focus on farming, crops, weather, and agricultural advice for Indian farmers."""
        
        payload = {
            'contents': [
                {'role': 'user', 'parts': [{'text': f'{system_prompt}\n\nUser question: {message}'}]}
            ],
            'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 500}
        }
        
        response = http_requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result:
                text = result['candidates'][0]['content']['parts'][0]['text']
                return jsonify({'success': True, 'response': text, 'source': 'gemini'})
        
        return jsonify({'success': True, 'response': 'I can help with farming questions. Please ask about crops, weather, or agricultural practices.', 'source': 'fallback'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= AUTH API =============
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

users_db = {}

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'error': 'All fields required'}), 400
    
    user_id = f"user_{len(users_db) + 1}"
    users_db[user_id] = {
        'id': user_id, 'username': username, 'email': email,
        'password_hash': generate_password_hash(password)
    }
    
    token = jwt.encode({'user_id': user_id, 'exp': datetime.utcnow() + timedelta(days=7)}, 
                       app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({'success': True, 'token': token, 'user': {'id': user_id, 'username': username, 'email': email}}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = next((u for u in users_db.values() if u['email'] == email), None)
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    token = jwt.encode({'user_id': user['id'], 'exp': datetime.utcnow() + timedelta(days=7)},
                       app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({'success': True, 'token': token, 'user': {'id': user['id'], 'username': user['username'], 'email': user['email']}})


# ============= LIVEKIT API =============
@app.route('/api/livekit/experts', methods=['GET'])
def get_experts():
    experts = [
        {'id': 'exp1', 'name': 'Dr. Sharma', 'specialization': 'Crop Science', 'rating': 4.8, 'experience': '15 years', 'available': True, 'price_per_min': 5},
        {'id': 'exp2', 'name': 'Dr. Patel', 'specialization': 'Soil Science', 'rating': 4.7, 'experience': '12 years', 'available': False, 'price_per_min': 4}
    ]
    return jsonify({'success': True, 'experts': experts})


# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'CropYield AI'})


# Vercel handler
def handler(request):
    return app(request)

# For local testing
if __name__ == '__main__':
    app.run(debug=True, port=5000)

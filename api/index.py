"""
Vercel Serverless Function Entry Point
"""
import os
import sys
from datetime import datetime, timedelta

# Get the parent directory (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add to Python path
sys.path.insert(0, BASE_DIR)

# Set environment variables for Vercel
os.environ.setdefault('FLASK_ENV', 'production')

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests as http_requests
import jwt
from yield_prediction import predict_yield as ml_predict_yield

# Initialize Flask app with templates and static in parent directory
app = Flask(__name__, 
            template_folder=BASE_DIR,
            static_folder=BASE_DIR)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'crop-yield-secret-key-2025')
app.config['DEBUG'] = False

# Use in-memory SQLite for Vercel (serverless)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CORS configuration
CORS(app, origins=['*'], supports_credentials=True)

# Initialize database
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
    return send_from_directory(BASE_DIR, filename)

# Serve app.js
@app.route('/app.js')
def serve_app_js():
    return send_from_directory(BASE_DIR, 'app.js')

# Serve style.css
@app.route('/style.css')
def serve_style_css():
    return send_from_directory(BASE_DIR, 'style.css')

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

# NASA POWER API for satellite soil and weather data
NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
NASA_AGRO_PARAMETERS = [
    "T2M",          # Temperature at 2m (°C)
    "T2M_MAX",      # Max temperature
    "T2M_MIN",      # Min temperature
    "RH2M",         # Relative humidity at 2m (%)
    "PRECTOTCORR", # Precipitation (mm/day)
    "ALLSKY_SFC_SW_DWN",  # Solar radiation (MJ/m²/day)
    "WS2M",         # Wind speed at 2m (m/s)
    "GWETROOT",     # Root zone soil wetness (0-1)
    "GWETPROF",     # Profile soil wetness (0-1)
    "EVPTRNS",      # Evapotranspiration (mm/day)
]

# State coordinates for NASA POWER API
STATE_COORDS = {
    'Punjab': {'lat': 31.1471, 'lon': 75.3412, 'city': 'Ludhiana'},
    'Haryana': {'lat': 29.0588, 'lon': 76.0856, 'city': 'Hisar'},
    'Uttar Pradesh': {'lat': 26.8467, 'lon': 80.9462, 'city': 'Lucknow'},
    'West Bengal': {'lat': 22.5726, 'lon': 88.3639, 'city': 'Kolkata'},
    'Andhra Pradesh': {'lat': 15.9129, 'lon': 79.7400, 'city': 'Guntur'},
    'Tamil Nadu': {'lat': 11.1271, 'lon': 78.6569, 'city': 'Trichy'},
    'Karnataka': {'lat': 15.3173, 'lon': 75.7139, 'city': 'Hubli'},
    'Maharashtra': {'lat': 19.7515, 'lon': 75.7139, 'city': 'Aurangabad'},
    'Madhya Pradesh': {'lat': 23.2599, 'lon': 77.4126, 'city': 'Bhopal'},
    'Gujarat': {'lat': 22.2587, 'lon': 71.1924, 'city': 'Rajkot'},
    'Rajasthan': {'lat': 27.0238, 'lon': 74.2179, 'city': 'Jaipur'},
    'Bihar': {'lat': 25.5941, 'lon': 85.1376, 'city': 'Patna'},
    'Odisha': {'lat': 20.2961, 'lon': 85.8245, 'city': 'Bhubaneswar'},
    'Assam': {'lat': 26.2006, 'lon': 92.9376, 'city': 'Guwahati'},
    'Jharkhand': {'lat': 23.6102, 'lon': 85.2799, 'city': 'Ranchi'},
    'Chhattisgarh': {'lat': 21.2787, 'lon': 81.8661, 'city': 'Raipur'},
    'Kerala': {'lat': 10.8505, 'lon': 76.2711, 'city': 'Thrissur'},
    'Telangana': {'lat': 18.1124, 'lon': 79.0193, 'city': 'Warangal'},
}

def get_nasa_power_data(state, days=30):
    """Fetch NASA POWER satellite data for a state"""
    if state not in STATE_COORDS:
        return None
    
    coords = STATE_COORDS[state]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    try:
        params = {
            'parameters': ','.join(NASA_AGRO_PARAMETERS),
            'community': 'AG',
            'longitude': coords['lon'],
            'latitude': coords['lat'],
            'start': start_date.strftime('%Y%m%d'),
            'end': end_date.strftime('%Y%m%d'),
            'format': 'JSON'
        }
        
        response = http_requests.get(NASA_POWER_BASE_URL, params=params, timeout=15)
        
        if response.status_code == 200:
            raw_data = response.json()
            return process_nasa_data(raw_data, state, coords)
    except Exception as e:
        print(f"NASA POWER error: {e}")
    return None

def process_nasa_data(raw_data, state, coords):
    """Process NASA POWER API response"""
    try:
        properties = raw_data.get('properties', {}).get('parameter', {})
        processed = {
            'state': state,
            'coordinates': {'lat': coords['lat'], 'lon': coords['lon']},
            'source': 'NASA POWER'
        }
        
        for param in NASA_AGRO_PARAMETERS:
            if param in properties:
                values = [v for v in properties[param].values() if v != -999]
                if values:
                    processed[param] = {
                        'average': round(sum(values) / len(values), 2),
                        'min': round(min(values), 2),
                        'max': round(max(values), 2)
                    }
        
        # Calculate soil moisture index
        root_wet = processed.get('GWETROOT', {}).get('average', 0.5)
        prof_wet = processed.get('GWETPROF', {}).get('average', 0.5)
        processed['soil_moisture_index'] = round((root_wet + prof_wet) / 2, 3)
        
        # Soil condition
        smi = processed['soil_moisture_index']
        if smi < 0.2:
            processed['soil_condition'] = 'Very Dry - Critical'
        elif smi < 0.4:
            processed['soil_condition'] = 'Dry - Needs Irrigation'
        elif smi < 0.6:
            processed['soil_condition'] = 'Optimal'
        elif smi < 0.8:
            processed['soil_condition'] = 'Moist'
        else:
            processed['soil_condition'] = 'Wet - Drainage Needed'
        
        return processed
    except Exception as e:
        print(f"NASA process error: {e}")
        return None

def calculate_nasa_yield_factor(nasa_data, crop):
    """Calculate yield factor from NASA data"""
    if not nasa_data:
        return 1.0, []
    
    factors = []
    insights = []
    
    # Soil moisture factor
    soil_moisture = nasa_data.get('soil_moisture_index', 0.5)
    if 0.4 <= soil_moisture <= 0.6:
        soil_factor = 1.15
        insights.append(f"🛰️ NASA: Soil moisture ({soil_moisture:.2f}) is ideal")
    elif soil_moisture < 0.2:
        soil_factor = 0.7
        insights.append(f"🛰️ NASA: Soil very dry - needs irrigation")
    elif soil_moisture > 0.8:
        soil_factor = 0.8
        insights.append(f"🛰️ NASA: Soil waterlogged - needs drainage")
    else:
        soil_factor = 0.95
    factors.append(soil_factor)
    
    # Temperature factor
    temp = nasa_data.get('T2M', {}).get('average', 25)
    if 20 <= temp <= 30:
        factors.append(1.1)
        insights.append(f"🛰️ NASA: Temperature ({temp:.1f}°C) is ideal")
    elif temp < 15 or temp > 38:
        factors.append(0.7)
    else:
        factors.append(0.95)
    
    # Solar radiation factor
    solar = nasa_data.get('ALLSKY_SFC_SW_DWN', {}).get('average', 18)
    if 15 <= solar <= 22:
        factors.append(1.1)
        insights.append(f"🛰️ NASA: Solar radiation ({solar:.1f} MJ/m²) excellent")
    elif solar < 10:
        factors.append(0.8)
    else:
        factors.append(1.0)
    
    combined_factor = sum(factors) / len(factors)
    return round(combined_factor, 3), insights

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

@app.route('/api/yield/weather/<state>', methods=['GET'])
def get_yield_weather(state):
    """Get live weather for yield prediction"""
    city = STATE_CAPITALS.get(state, 'Delhi')
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={OPENWEATHER_API_KEY}&units=metric"
        response = http_requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'weather': {
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'description': data['weather'][0]['description'],
                    'city': city
                }
            })
    except:
        pass
    return jsonify({'success': False, 'error': 'Weather data not available'})

@app.route('/api/yield/predict', methods=['POST'])
def predict_yield():
    try:
        data = request.get_json()
        features = [
            float(data.get('temperature', 25)),
            float(data.get('humidity', 60)),
            float(data.get('precipitation', 5)),
            float(data.get('solar_radiation', 18)),
            float(data.get('soil_moisture', 0.5))
        ]

        # Predict yield using the ML model
        predicted_yield = ml_predict_yield(features)

        return jsonify({
            'success': True,
            'predicted_yield': predicted_yield
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/yield/nasa-data/<state>', methods=['GET'])
def get_nasa_soil_data(state):
    """Get NASA POWER satellite data for a state"""
    data = get_nasa_power_data(state)
    if data:
        return jsonify({
            'success': True,
            'state': state,
            'source': 'NASA POWER Satellite',
            'data': {
                'soil_moisture_index': data.get('soil_moisture_index'),
                'soil_condition': data.get('soil_condition'),
                'root_zone_wetness': data.get('GWETROOT', {}).get('average'),
                'profile_wetness': data.get('GWETPROF', {}).get('average'),
                'temperature': {
                    'average': data.get('T2M', {}).get('average'),
                    'max': data.get('T2M_MAX', {}).get('average'),
                    'min': data.get('T2M_MIN', {}).get('average'),
                    'unit': '°C'
                },
                'humidity': {
                    'average': data.get('RH2M', {}).get('average'),
                    'unit': '%'
                },
                'precipitation': {
                    'average': data.get('PRECTOTCORR', {}).get('average'),
                    'unit': 'mm/day'
                },
                'solar_radiation': {
                    'average': data.get('ALLSKY_SFC_SW_DWN', {}).get('average'),
                    'unit': 'MJ/m²/day'
                },
                'evapotranspiration': {
                    'average': data.get('EVPTRNS', {}).get('average'),
                    'unit': 'mm/day'
                },
                'wind_speed': {
                    'average': data.get('WS2M', {}).get('average'),
                    'unit': 'm/s'
                }
            },
            'coordinates': data.get('coordinates')
        })
    return jsonify({'success': False, 'error': 'NASA POWER data not available for this state'}), 404


# ============= RECOMMENDATION API =============
CROPS_DATABASE = {
    'rice': {'season': ['Kharif'], 'water_need': 'High', 'investment_per_ha': 45000, 'expected_revenue': 75000, 'duration_days': 120, 'risk_level': 'Low'},
    'wheat': {'season': ['Rabi'], 'water_need': 'Medium', 'investment_per_ha': 35000, 'expected_revenue': 65000, 'duration_days': 130, 'risk_level': 'Low'},
    'maize': {'season': ['Kharif', 'Rabi'], 'water_need': 'Medium', 'investment_per_ha': 30000, 'expected_revenue': 55000, 'duration_days': 100, 'risk_level': 'Medium'},
    'cotton': {'season': ['Kharif'], 'water_need': 'Medium', 'investment_per_ha': 50000, 'expected_revenue': 90000, 'duration_days': 180, 'risk_level': 'Medium'},
    'sugarcane': {'season': ['Kharif', 'Rabi'], 'water_need': 'High', 'investment_per_ha': 80000, 'expected_revenue': 180000, 'duration_days': 365, 'risk_level': 'Low'},
    'potato': {'season': ['Rabi'], 'water_need': 'High', 'investment_per_ha': 100000, 'expected_revenue': 200000, 'duration_days': 90, 'risk_level': 'High'},
    'tomato': {'season': ['Kharif', 'Rabi', 'Zaid'], 'water_need': 'High', 'investment_per_ha': 150000, 'expected_revenue': 350000, 'duration_days': 90, 'risk_level': 'High'},
    'onion': {'season': ['Kharif', 'Rabi'], 'water_need': 'Medium', 'investment_per_ha': 80000, 'expected_revenue': 180000, 'duration_days': 120, 'risk_level': 'High'},
}

@app.route('/api/recommend/states', methods=['GET'])
def recommend_states():
    return jsonify({'success': True, 'states': STATES})

@app.route('/api/recommend/weather/<state>', methods=['GET'])
def get_recommend_weather(state):
    """Get live weather for recommendations"""
    city = STATE_CAPITALS.get(state, 'Delhi')
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={OPENWEATHER_API_KEY}&units=metric"
        response = http_requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'weather': {
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'description': data['weather'][0]['description'],
                    'city': city
                }
            })
    except:
        pass
    return jsonify({'success': False, 'error': 'Weather data not available'})

@app.route('/api/recommend/get', methods=['POST'])
def get_recommendations():
    try:
        data = request.get_json()
        state = data.get('state', 'Punjab')
        season = data.get('season', 'Kharif')
        farm_size = float(data.get('farm_size', 1))
        
        recommendations = []
        for crop_name, crop_info in CROPS_DATABASE.items():
            score = 85 if season in crop_info['season'] else 65
            profit = crop_info['expected_revenue'] - crop_info['investment_per_ha']
            roi = round((profit / crop_info['investment_per_ha']) * 100, 1)
            
            recommendations.append({
                'crop': crop_name.title(),
                'score': score,
                'suitability': 'Excellent' if score >= 80 else 'Good',
                'reasons': [f'Suitable for {season} season', f'Good yield potential in {state}'],
                'financials': {
                    'investment_per_ha': crop_info['investment_per_ha'],
                    'expected_profit_per_ha': profit,
                    'roi_percent': roi,
                    'total_investment': int(crop_info['investment_per_ha'] * farm_size),
                    'total_profit': int(profit * farm_size)
                },
                'details': {
                    'duration_days': crop_info['duration_days'],
                    'water_need': crop_info['water_need'],
                    'risk_level': crop_info['risk_level']
                }
            })
        
        return jsonify({'success': True, 'recommendations': sorted(recommendations, key=lambda x: x['score'], reverse=True)[:5]})
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

@app.route('/api/weather/cities', methods=['GET'])
def get_cities():
    cities = [{'name': city, 'state': state} for state, city in STATE_CAPITALS.items()]
    return jsonify({'success': True, 'cities': cities})


# ============= VOICE AGENT API =============
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
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

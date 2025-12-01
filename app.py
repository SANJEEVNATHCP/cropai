#!/usr/bin/env python3
"""
CropYield AI - Crop Yield Prediction & Recommendation System
With LiveKit Integration for Expert Consultations
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'crop-yield-secret-key-2025')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Database configuration
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'cropyield.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CORS configuration
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)

# Initialize database
from backend.models import db
db.init_app(app)

# Create tables
with app.app_context():
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    db.create_all()
    print("✅ Database initialized")

# Register blueprints
from backend.routes.yield_prediction import yield_bp
from backend.routes.crop_recommendation import recommendation_bp
from backend.routes.voice_agent import voice_agent_bp
from backend.routes.auth import auth_bp
from backend.routes.weather import weather_bp

app.register_blueprint(yield_bp, url_prefix='/api/yield')
app.register_blueprint(recommendation_bp, url_prefix='/api/recommend')
app.register_blueprint(voice_agent_bp, url_prefix='/api/voice')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(weather_bp, url_prefix='/api/weather')

print("✅ All routes registered")

# Root route
@app.route('/')
def index():
    return render_template('index.html')

# Yield Prediction Page
@app.route('/yield')
def yield_page():
    return render_template('yield.html')

# Crop Recommendation Page
@app.route('/recommendation')
def recommendation_page():
    return render_template('recommendation.html')

# AI Voice Agent Page
@app.route('/voice-agent')
def voice_agent_page():
    return render_template('voice_agent.html')

# Weather Page
@app.route('/weather')
def weather_page():
    return render_template('weather.html')

# Health check
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'app': 'CropYield AI',
        'version': '1.0.0',
        'features': [
            'crop_yield_prediction',
            'crop_recommendation',
            'ai_voice_agent',
            'ai_powered_insights'
        ]
    }), 200

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("🌾 CropYield AI Starting...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"🎥 LiveKit: Enabled")
    
    app.run(debug=debug, host=host, port=port)

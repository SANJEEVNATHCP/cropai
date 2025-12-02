#!/usr/bin/env python3
"""
CropYield AI - Crop Yield Prediction & Recommendation System
With LiveKit Integration for Expert Consultations
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize Flask app
app = Flask(__name__, 
            template_folder=BASE_DIR,
            static_folder=BASE_DIR)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'crop-yield-secret-key-2025')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Database configuration
db_path = os.path.join(BASE_DIR, 'database', 'cropyield.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CORS configuration
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)

# Initialize database
db = SQLAlchemy(app)

# Create tables
with app.app_context():
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    db.create_all()
    print("✅ Database initialized")

# Import and register blueprints from local files
from yield_prediction import yield_bp
from crop_recommendation import recommendation_bp
from voice_agent import voice_agent_bp
from auth import auth_bp
from weather import weather_bp
from livekit_routes import livekit_bp

app.register_blueprint(yield_bp, url_prefix='/api/yield')
app.register_blueprint(recommendation_bp, url_prefix='/api/recommend')
app.register_blueprint(voice_agent_bp, url_prefix='/api/voice')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(weather_bp, url_prefix='/api/weather')
app.register_blueprint(livekit_bp, url_prefix='/api/livekit')

print("✅ All routes registered")

# Static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(BASE_DIR, filename)

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

# Favicon route
@app.route('/favicon.ico')
def favicon():
    return '', 204

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

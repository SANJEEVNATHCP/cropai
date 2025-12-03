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
            static_folder=os.path.join(BASE_DIR, 'static'),
            static_url_path='/static')

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

# Logo SVG route - direct serve
@app.route('/logo.svg')
def logo():
    from flask import Response
    svg_content = '''<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#10b981"/>
      <stop offset="100%" style="stop-color:#059669"/>
    </linearGradient>
    <linearGradient id="grad2" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#34d399"/>
      <stop offset="100%" style="stop-color:#10b981"/>
    </linearGradient>
    <linearGradient id="grad3" x1="100%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#6ee7b7"/>
      <stop offset="100%" style="stop-color:#34d399"/>
    </linearGradient>
    <linearGradient id="techGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#3b82f6"/>
      <stop offset="100%" style="stop-color:#1d4ed8"/>
    </linearGradient>
  </defs>
  <polygon points="100,10 170,50 170,130 100,170 30,130 30,50" fill="url(#grad1)" stroke="#047857" stroke-width="3"/>
  <polygon points="100,25 155,55 155,125 100,155 45,125 45,55" fill="none" stroke="#ffffff" stroke-width="1" opacity="0.2"/>
  <polygon points="100,70 70,90 80,110 100,120" fill="url(#grad2)"/>
  <polygon points="70,90 60,100 70,115 80,110" fill="#047857" opacity="0.7"/>
  <polygon points="100,70 130,90 120,110 100,120" fill="url(#grad3)"/>
  <polygon points="130,90 140,100 130,115 120,110" fill="#059669" opacity="0.7"/>
  <polygon points="95,120 105,120 103,145 97,145" fill="#047857"/>
  <polygon points="100,50 90,70 100,75 110,70" fill="#34d399"/>
  <g transform="translate(100, 155)">
    <polygon points="0,-8 8,0 0,8 -8,0" fill="url(#techGrad)" stroke="#1e40af" stroke-width="1.5"/>
    <polygon points="0,-5 5,0 0,5 -5,0" fill="#60a5fa" opacity="0.4"/>
    <circle cx="-10" cy="0" r="1.5" fill="#3b82f6"/>
    <circle cx="10" cy="0" r="1.5" fill="#3b82f6"/>
    <line x1="-8" y1="0" x2="-10" y2="0" stroke="#60a5fa" stroke-width="1"/>
    <line x1="8" y1="0" x2="10" y2="0" stroke="#60a5fa" stroke-width="1"/>
  </g>
  <polygon points="30,50 35,48 33,53" fill="#34d399" opacity="0.5"/>
  <polygon points="170,50 165,48 167,53" fill="#34d399" opacity="0.5"/>
  <polygon points="30,130 35,132 33,127" fill="#34d399" opacity="0.5"/>
  <polygon points="170,130 165,132 167,127" fill="#34d399" opacity="0.5"/>
  <g opacity="0.15" stroke="#ffffff" stroke-width="1">
    <line x1="50" y1="60" x2="70" y2="60"/>
    <line x1="130" y1="60" x2="150" y2="60"/>
    <line x1="50" y1="120" x2="70" y2="120"/>
    <line x1="130" y1="120" x2="150" y2="120"/>
  </g>
</svg>'''
    return Response(svg_content, mimetype='image/svg+xml')

# Explicit static files route
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

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

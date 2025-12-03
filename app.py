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
    svg_content = '''<svg width="280" height="60" viewBox="0 0 280 60" xmlns="http://www.w3.org/2000/svg">
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
  
  <!-- Hexagon icon (scaled for horizontal layout) -->
  <g transform="translate(30, 30) scale(0.25)">
    <polygon points="0,-80 70,-40 70,40 0,80 -70,40 -70,-40" fill="url(#grad1)" stroke="#047857" stroke-width="6"/>
    <polygon points="0,-65 55,-35 55,35 0,65 -55,35 -55,-35" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.2"/>
    <polygon points="0,-20 -30,0 -20,30 0,40" fill="url(#grad2)"/>
    <polygon points="-30,0 -40,10 -30,35 -20,30" fill="#047857" opacity="0.7"/>
    <polygon points="0,-20 30,0 20,30 0,40" fill="url(#grad3)"/>
    <polygon points="30,0 40,10 30,35 20,30" fill="#059669" opacity="0.7"/>
    <polygon points="-5,40 5,40 3,65 -3,65" fill="#047857"/>
    <polygon points="0,-40 -10,-20 0,-15 10,-20" fill="#34d399"/>
    <g transform="translate(0, 70)">
      <polygon points="0,-8 8,0 0,8 -8,0" fill="url(#techGrad)" stroke="#1e40af" stroke-width="2"/>
      <polygon points="0,-5 5,0 0,5 -5,0" fill="#60a5fa" opacity="0.4"/>
    </g>
  </g>
  
  <!-- Text: CROPYIELD AI -->
  <text x="70" y="40" fill="#ffffff" font-size="28" font-weight="bold" font-family="'Segoe UI', Arial, sans-serif" letter-spacing="1">
    CROPYIELD <tspan fill="#93c5fd" font-size="32" font-weight="900">AI</tspan>
  </text>
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

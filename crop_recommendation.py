from flask import Blueprint, request, jsonify
import json
import requests
from datetime import datetime
import random

recommendation_bp = Blueprint('recommendation', __name__)

# OpenWeatherMap API key
OPENWEATHER_API_KEY = 'b576d8a952bf4c45c7ef5bddb148e76b'

# State capital cities for weather lookup
STATE_CITIES = {
    'Punjab': {'city': 'Chandigarh', 'lat': 30.7333, 'lon': 76.7794},
    'Haryana': {'city': 'Chandigarh', 'lat': 30.7333, 'lon': 76.7794},
    'Uttar Pradesh': {'city': 'Lucknow', 'lat': 26.8467, 'lon': 80.9462},
    'West Bengal': {'city': 'Kolkata', 'lat': 22.5726, 'lon': 88.3639},
    'Andhra Pradesh': {'city': 'Visakhapatnam', 'lat': 17.6868, 'lon': 83.2185},
    'Tamil Nadu': {'city': 'Chennai', 'lat': 13.0827, 'lon': 80.2707},
    'Karnataka': {'city': 'Bangalore', 'lat': 12.9716, 'lon': 77.5946},
    'Maharashtra': {'city': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},
    'Madhya Pradesh': {'city': 'Bhopal', 'lat': 23.2599, 'lon': 77.4126},
    'Gujarat': {'city': 'Ahmedabad', 'lat': 23.0225, 'lon': 72.5714},
    'Rajasthan': {'city': 'Jaipur', 'lat': 26.9124, 'lon': 75.7873},
    'Bihar': {'city': 'Patna', 'lat': 25.5941, 'lon': 85.1376},
    'Odisha': {'city': 'Bhubaneswar', 'lat': 20.2961, 'lon': 85.8245},
    'Assam': {'city': 'Guwahati', 'lat': 26.1445, 'lon': 91.7362},
    'Jharkhand': {'city': 'Ranchi', 'lat': 23.3441, 'lon': 85.3096},
    'Chhattisgarh': {'city': 'Raipur', 'lat': 21.2514, 'lon': 81.6296},
    'Kerala': {'city': 'Kochi', 'lat': 9.9312, 'lon': 76.2673},
    'Telangana': {'city': 'Hyderabad', 'lat': 17.3850, 'lon': 78.4867},
}

# STATE-SPECIFIC CROP PREFERENCES (Major crops grown in each state)
STATE_CROP_PREFERENCES = {
    'Punjab': {'wheat': 1.4, 'rice': 1.3, 'cotton': 1.2, 'maize': 1.1, 'potato': 1.2, 'sugarcane': 1.1},
    'Haryana': {'wheat': 1.4, 'rice': 1.3, 'cotton': 1.2, 'mustard': 1.3, 'bajra': 1.2, 'sugarcane': 1.1},
    'Uttar Pradesh': {'wheat': 1.3, 'rice': 1.3, 'sugarcane': 1.4, 'potato': 1.3, 'mustard': 1.2, 'maize': 1.1},
    'West Bengal': {'rice': 1.5, 'potato': 1.3, 'jute': 1.4, 'wheat': 1.0, 'maize': 1.1, 'mustard': 1.2},
    'Andhra Pradesh': {'rice': 1.4, 'cotton': 1.3, 'groundnut': 1.3, 'sugarcane': 1.2, 'maize': 1.2, 'chilli': 1.3},
    'Tamil Nadu': {'rice': 1.4, 'sugarcane': 1.3, 'groundnut': 1.3, 'cotton': 1.2, 'maize': 1.1, 'banana': 1.3},
    'Karnataka': {'rice': 1.2, 'maize': 1.3, 'groundnut': 1.2, 'cotton': 1.3, 'sugarcane': 1.3, 'jowar': 1.2},
    'Maharashtra': {'cotton': 1.4, 'sugarcane': 1.4, 'soybean': 1.4, 'groundnut': 1.2, 'jowar': 1.3, 'onion': 1.4},
    'Madhya Pradesh': {'soybean': 1.5, 'wheat': 1.3, 'chickpea': 1.4, 'maize': 1.2, 'cotton': 1.2, 'mustard': 1.1},
    'Gujarat': {'cotton': 1.5, 'groundnut': 1.4, 'wheat': 1.2, 'rice': 1.1, 'bajra': 1.3, 'castor': 1.3},
    'Rajasthan': {'bajra': 1.5, 'wheat': 1.3, 'mustard': 1.4, 'groundnut': 1.2, 'maize': 1.2, 'jowar': 1.3},
    'Bihar': {'rice': 1.4, 'wheat': 1.3, 'maize': 1.3, 'potato': 1.2, 'sugarcane': 1.2, 'onion': 1.1},
    'Odisha': {'rice': 1.5, 'groundnut': 1.2, 'sugarcane': 1.1, 'maize': 1.2, 'cotton': 1.1, 'vegetables': 1.2},
    'Assam': {'rice': 1.5, 'tea': 1.4, 'jute': 1.3, 'potato': 1.2, 'maize': 1.1, 'sugarcane': 1.1},
    'Jharkhand': {'rice': 1.4, 'wheat': 1.2, 'maize': 1.3, 'potato': 1.2, 'vegetables': 1.2, 'pulses': 1.2},
    'Chhattisgarh': {'rice': 1.5, 'maize': 1.2, 'soybean': 1.2, 'groundnut': 1.1, 'sugarcane': 1.1, 'wheat': 1.0},
    'Kerala': {'rice': 1.3, 'coconut': 1.5, 'rubber': 1.4, 'banana': 1.3, 'pepper': 1.4, 'cardamom': 1.3},
    'Telangana': {'rice': 1.4, 'cotton': 1.4, 'maize': 1.3, 'soybean': 1.2, 'groundnut': 1.2, 'sugarcane': 1.2},
}

# Soil type mapping (user input -> database compatible)
SOIL_TYPE_MAPPING = {
    'Loamy': ['Loamy', 'Sandy Loam', 'Alluvial'],
    'Clay': ['Clay', 'Loamy', 'Black'],
    'Sandy': ['Sandy', 'Sandy Loam', 'Red'],
    'Black': ['Black', 'Clay', 'Loamy'],
    'Red': ['Red', 'Sandy', 'Loamy'],
    'Alluvial': ['Alluvial', 'Loamy', 'Clay'],
}

def get_live_weather(state):
    """Fetch live weather data for a state"""
    if state not in STATE_CITIES:
        return None
    
    city_data = STATE_CITIES[state]
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': city_data['lat'],
            'lon': city_data['lon'],
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric'
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'condition': data['weather'][0]['main'],
                'description': data['weather'][0]['description'],
                'city': city_data['city'],
                'source': 'live'
            }
    except Exception as e:
        print(f"Weather API error: {e}")
    return None

# Crop database with requirements and profitability
CROPS_DATABASE = {
    'rice': {
        'season': ['Kharif'],
        'water_need': 'High',
        'soil_types': ['Clay', 'Loamy', 'Alluvial'],
        'ph_range': (5.5, 7.0),
        'investment_per_ha': 45000,
        'expected_revenue': 75000,
        'duration_days': 120,
        'risk_level': 'Low'
    },
    'wheat': {
        'season': ['Rabi'],
        'water_need': 'Medium',
        'soil_types': ['Loamy', 'Clay', 'Alluvial'],
        'ph_range': (6.0, 7.5),
        'investment_per_ha': 35000,
        'expected_revenue': 65000,
        'duration_days': 130,
        'risk_level': 'Low'
    },
    'maize': {
        'season': ['Kharif', 'Rabi'],
        'water_need': 'Medium',
        'soil_types': ['Loamy', 'Sandy Loam', 'Alluvial'],
        'ph_range': (5.8, 7.0),
        'investment_per_ha': 30000,
        'expected_revenue': 55000,
        'duration_days': 100,
        'risk_level': 'Medium'
    },
    'cotton': {
        'season': ['Kharif'],
        'water_need': 'Medium',
        'soil_types': ['Black', 'Alluvial', 'Loamy'],
        'ph_range': (6.0, 8.0),
        'investment_per_ha': 50000,
        'expected_revenue': 90000,
        'duration_days': 180,
        'risk_level': 'Medium'
    },
    'sugarcane': {
        'season': ['Kharif', 'Rabi'],
        'water_need': 'High',
        'soil_types': ['Loamy', 'Clay', 'Alluvial'],
        'ph_range': (6.0, 7.5),
        'investment_per_ha': 80000,
        'expected_revenue': 180000,
        'duration_days': 365,
        'risk_level': 'Low'
    },
    'soybean': {
        'season': ['Kharif'],
        'water_need': 'Medium',
        'soil_types': ['Loamy', 'Clay', 'Black'],
        'ph_range': (6.0, 7.0),
        'investment_per_ha': 25000,
        'expected_revenue': 50000,
        'duration_days': 100,
        'risk_level': 'Medium'
    },
    'groundnut': {
        'season': ['Kharif', 'Rabi'],
        'water_need': 'Low',
        'soil_types': ['Sandy', 'Sandy Loam', 'Red'],
        'ph_range': (6.0, 6.5),
        'investment_per_ha': 35000,
        'expected_revenue': 70000,
        'duration_days': 120,
        'risk_level': 'Medium'
    },
    'potato': {
        'season': ['Rabi'],
        'water_need': 'High',
        'soil_types': ['Sandy Loam', 'Loamy', 'Alluvial'],
        'ph_range': (5.5, 6.5),
        'investment_per_ha': 100000,
        'expected_revenue': 200000,
        'duration_days': 90,
        'risk_level': 'High'
    },
    'tomato': {
        'season': ['Kharif', 'Rabi', 'Zaid'],
        'water_need': 'High',
        'soil_types': ['Loamy', 'Sandy Loam', 'Red'],
        'ph_range': (6.0, 7.0),
        'investment_per_ha': 150000,
        'expected_revenue': 350000,
        'duration_days': 90,
        'risk_level': 'High'
    },
    'onion': {
        'season': ['Kharif', 'Rabi'],
        'water_need': 'Medium',
        'soil_types': ['Loamy', 'Sandy Loam', 'Alluvial'],
        'ph_range': (6.0, 7.0),
        'investment_per_ha': 80000,
        'expected_revenue': 180000,
        'duration_days': 120,
        'risk_level': 'High'
    },
    'mustard': {
        'season': ['Rabi'],
        'water_need': 'Low',
        'soil_types': ['Loamy', 'Sandy Loam', 'Alluvial'],
        'ph_range': (6.0, 7.5),
        'investment_per_ha': 20000,
        'expected_revenue': 45000,
        'duration_days': 120,
        'risk_level': 'Low'
    },
    'chickpea': {
        'season': ['Rabi'],
        'water_need': 'Low',
        'soil_types': ['Loamy', 'Sandy Loam', 'Black'],
        'ph_range': (6.0, 8.0),
        'investment_per_ha': 25000,
        'expected_revenue': 55000,
        'duration_days': 110,
        'risk_level': 'Low'
    },
    'bajra': {
        'season': ['Kharif'],
        'water_need': 'Low',
        'soil_types': ['Sandy', 'Sandy Loam', 'Loamy'],
        'ph_range': (6.5, 7.5),
        'investment_per_ha': 15000,
        'expected_revenue': 35000,
        'duration_days': 80,
        'risk_level': 'Low'
    },
    'jowar': {
        'season': ['Kharif', 'Rabi'],
        'water_need': 'Low',
        'soil_types': ['Black', 'Loamy', 'Red'],
        'ph_range': (6.0, 7.5),
        'investment_per_ha': 18000,
        'expected_revenue': 38000,
        'duration_days': 100,
        'risk_level': 'Low'
    }
}

SOIL_TYPES = ['Clay', 'Loamy', 'Sandy', 'Sandy Loam', 'Alluvial', 'Black', 'Red', 'Laterite']
SEASONS = ['Kharif', 'Rabi', 'Zaid']
WATER_LEVELS = ['Low', 'Medium', 'High']


def calculate_crop_score(crop_name, crop_data, inputs):
    """Calculate suitability score for a crop (0-100) with state-specific preferences"""
    score = 40  # Base score (reduced to allow more variation)
    reasons = []
    state = inputs.get('state', '')
    
    # STATE-SPECIFIC BONUS (Up to 20 points) - THIS MAKES DIFFERENT STATES GET DIFFERENT RECOMMENDATIONS
    state_prefs = STATE_CROP_PREFERENCES.get(state, {})
    state_multiplier = state_prefs.get(crop_name, 0.8)  # Default 0.8 for non-preferred crops
    state_bonus = int((state_multiplier - 0.8) * 50)  # Convert to points
    if state_bonus > 0:
        score += state_bonus
        reasons.append(f"🏆 {crop_name.title()} is a major crop in {state}")
    elif state_multiplier < 1.0:
        score -= 5
        reasons.append(f"📊 {crop_name.title()} is less common in {state}")
    
    # Season match (20 points)
    if inputs['season'] in crop_data['season']:
        score += 20
        reasons.append(f"✅ Ideal for {inputs['season']} season")
    else:
        score -= 20
        reasons.append(f"⚠️ Best grown in {', '.join(crop_data['season'])}")
    
    # Soil match with mapping (15 points)
    user_soil = inputs.get('soil_type', 'Loamy')
    compatible_soils = SOIL_TYPE_MAPPING.get(user_soil, [user_soil])
    soil_match = any(s in crop_data['soil_types'] for s in compatible_soils)
    
    if soil_match:
        score += 15
        reasons.append(f"✅ {user_soil} soil is suitable")
    else:
        score -= 10
        reasons.append(f"⚠️ Preferred: {', '.join(crop_data['soil_types'][:2])}")
    
    # Water availability match (15 points)
    water_map = {'Low': 1, 'Medium': 2, 'High': 3}
    crop_water = water_map.get(crop_data['water_need'], 2)
    user_water = water_map.get(inputs['water_availability'], 2)
    
    if user_water >= crop_water:
        score += 15
        reasons.append(f"✅ Water availability sufficient")
    elif user_water == crop_water - 1:
        score += 5
        reasons.append(f"⚠️ May need extra irrigation")
    else:
        score -= 15
        reasons.append(f"❌ Needs more water ({crop_data['water_need']})")
    
    # pH match (10 points)
    ph = inputs.get('ph', 6.5)
    ph_min, ph_max = crop_data['ph_range']
    if ph_min <= ph <= ph_max:
        score += 10
        reasons.append(f"✅ Soil pH optimal ({ph})")
    elif ph_min - 0.5 <= ph <= ph_max + 0.5:
        score += 3
        reasons.append(f"⚠️ pH needs adjustment ({ph_min}-{ph_max})")
    else:
        score -= 8
        reasons.append(f"❌ pH not suitable")
    
    # Budget match (10 points)
    if inputs.get('budget'):
        budget_per_ha = inputs['budget'] / max(inputs.get('farm_size', 1), 0.1)
        if budget_per_ha >= crop_data['investment_per_ha']:
            score += 10
            reasons.append(f"✅ Budget sufficient")
        elif budget_per_ha >= crop_data['investment_per_ha'] * 0.7:
            score += 5
            reasons.append(f"⚠️ Budget is tight, may need optimization")
        else:
            score -= 5
            reasons.append(f"❌ Budget may be insufficient (needs ₹{crop_data['investment_per_ha']:,}/ha)")
    
    # Risk adjustment
    if inputs.get('risk_preference') == 'low' and crop_data['risk_level'] == 'High':
        score -= 10
        reasons.append(f"⚠️ Higher market price volatility")
    
    # Weather-based adjustments (if live weather available)
    if inputs.get('live_weather'):
        weather = inputs['live_weather']
        temp = weather.get('temperature', 25)
        humidity = weather.get('humidity', 70)
        
        # Temperature suitability
        if crop_data['water_need'] == 'High' and temp > 35:
            score -= 5
            reasons.append(f"🌡️ Current temp ({temp}°C) is hot - needs more irrigation")
        elif crop_data['water_need'] == 'Low' and temp < 15:
            score -= 5
            reasons.append(f"🌡️ Current temp ({temp}°C) is cool - may slow growth")
        elif 20 <= temp <= 30:
            score += 5
            reasons.append(f"🌡️ Current temp ({temp}°C) is ideal")
        
        # Humidity suitability
        if humidity > 85 and crop_data['water_need'] == 'Low':
            score -= 5
            reasons.append(f"💧 High humidity ({humidity}%) - risk of fungal diseases")
        elif humidity < 40 and crop_data['water_need'] == 'High':
            score -= 5
            reasons.append(f"💧 Low humidity ({humidity}%) - needs irrigation")
    
    return min(100, max(0, score)), reasons


def get_recommendations(inputs):
    """Get crop recommendations based on inputs"""
    recommendations = []
    
    for crop_name, crop_data in CROPS_DATABASE.items():
        score, reasons = calculate_crop_score(crop_name, crop_data, inputs)
        
        if score >= 40:  # Only include somewhat suitable crops
            profit = crop_data['expected_revenue'] - crop_data['investment_per_ha']
            roi = (profit / crop_data['investment_per_ha']) * 100
            
            recommendations.append({
                'crop': crop_name.title(),
                'score': score,
                'suitability': 'Excellent' if score >= 80 else 'Good' if score >= 60 else 'Fair',
                'reasons': reasons,
                'financials': {
                    'investment_per_ha': crop_data['investment_per_ha'],
                    'expected_revenue_per_ha': crop_data['expected_revenue'],
                    'expected_profit_per_ha': profit,
                    'roi_percent': round(roi, 1),
                    'total_investment': crop_data['investment_per_ha'] * inputs.get('farm_size', 1),
                    'total_expected_profit': profit * inputs.get('farm_size', 1)
                },
                'details': {
                    'duration_days': crop_data['duration_days'],
                    'water_need': crop_data['water_need'],
                    'risk_level': crop_data['risk_level'],
                    'best_seasons': crop_data['season']
                }
            })
    
    # Sort by score
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    return recommendations[:5]  # Return top 5


@recommendation_bp.route('/get', methods=['POST'])
def get_crop_recommendations():
    """Get personalized crop recommendations"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Request data required'}), 400
    
    # Required fields
    state = data.get('state')
    season = data.get('season')
    
    if not state or not season:
        return jsonify({'success': False, 'error': 'State and season are required'}), 400
    
    # Try to get live weather
    live_weather = get_live_weather(state) if data.get('use_live_weather', True) else None
    
    inputs = {
        'state': state,
        'season': season,
        'soil_type': data.get('soil_type', 'Loamy'),
        'water_availability': data.get('water_availability', 'Medium'),
        'ph': float(data.get('ph', 6.5)),
        'budget': float(data.get('budget', 100000)),
        'farm_size': float(data.get('farm_size', 1)),
        'risk_preference': data.get('risk_preference', 'medium'),
        'live_weather': live_weather
    }
    
    recommendations = get_recommendations(inputs)
    
    if not recommendations:
        return jsonify({
            'success': False,
            'error': 'No suitable crops found for your conditions'
        }), 404
    
    response = {
        'success': True,
        'recommendations': recommendations,
        'inputs': inputs,
        'generated_at': datetime.now().isoformat()
    }
    
    if live_weather:
        response['live_weather'] = live_weather
        response['weather_used'] = True
    
    return jsonify(response), 200


@recommendation_bp.route('/weather/<state>', methods=['GET'])
def get_state_weather(state):
    """Get live weather for a state"""
    weather = get_live_weather(state)
    if weather:
        return jsonify({'success': True, 'weather': weather})
    return jsonify({'success': False, 'error': 'Weather data not available'}), 404


@recommendation_bp.route('/soil-types', methods=['GET'])
def get_soil_types():
    """Get list of soil types"""
    return jsonify({
        'success': True,
        'soil_types': SOIL_TYPES
    }), 200


@recommendation_bp.route('/seasons', methods=['GET'])
def get_seasons():
    """Get list of seasons"""
    return jsonify({
        'success': True,
        'seasons': SEASONS
    }), 200


@recommendation_bp.route('/water-levels', methods=['GET'])
def get_water_levels():
    """Get water availability levels"""
    return jsonify({
        'success': True,
        'water_levels': WATER_LEVELS
    }), 200


@recommendation_bp.route('/states', methods=['GET'])
def get_states():
    """Get list of Indian states"""
    states = ['Punjab', 'Haryana', 'Uttar Pradesh', 'West Bengal', 'Andhra Pradesh', 
              'Tamil Nadu', 'Karnataka', 'Maharashtra', 'Madhya Pradesh', 'Gujarat', 
              'Rajasthan', 'Bihar', 'Odisha', 'Assam', 'Jharkhand', 'Chhattisgarh', 
              'Kerala', 'Telangana']
    return jsonify({
        'success': True,
        'states': states
    }), 200

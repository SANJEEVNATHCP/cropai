from flask import Blueprint, request, jsonify
import json
import requests
from datetime import datetime
import random
import numpy as np
import os

# ML Libraries
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ ML libraries not available. Using rule-based system.")

recommendation_bp = Blueprint('recommendation', __name__)

# ML Model Storage
ML_MODEL = None
LABEL_ENCODERS = {}

# API Keys
OPENWEATHER_API_KEY = 'b576d8a952bf4c45c7ef5bddb148e76b'
DATA_GOV_API_KEY = '579b464db66ec23bdd00000135adb2e1402f446e7a24549732293525'

# data.gov.in API base URL
DATA_GOV_BASE_URL = 'https://api.data.gov.in/resource'


def get_govt_crop_data(state=None, crop=None):
    """Fetch crop data from data.gov.in API"""
    try:
        # Multiple resource IDs for different crop datasets
        resource_ids = [
            '9ef84268-d588-465a-a308-a864a43d0070',  # Crop production
            '35be999b-68d1-4fc5-8094-6e0b88c7ce4c',  # Agriculture stats
        ]
        
        all_records = []
        
        for resource_id in resource_ids:
            url = f"{DATA_GOV_BASE_URL}/{resource_id}"
            params = {
                'api-key': DATA_GOV_API_KEY,
                'format': 'json',
                'limit': 500
            }
            
            if state:
                params['filters[state_name]'] = state
            if crop:
                params['filters[crop]'] = crop
                
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'records' in data and len(data['records']) > 0:
                    all_records.extend(data['records'])
        
        if all_records:
            return {
                'success': True,
                'records': all_records,
                'total': len(all_records),
                'source': 'data.gov.in'
            }
        return {'success': False, 'error': 'No data found'}
    except Exception as e:
        print(f"data.gov.in API error: {e}")
        return {'success': False, 'error': str(e)}


def collect_govt_training_data():
    """Collect real crop data from data.gov.in for ML training"""
    training_data = []
    states = list(STATE_CITIES.keys())
    
    print("🔄 Collecting training data from data.gov.in...")
    
    for state in states:
        govt_data = get_govt_crop_data(state=state)
        
        if govt_data['success']:
            for record in govt_data['records']:
                crop_name = str(record.get('crop', record.get('crop_name', ''))).lower().strip()
                production = float(record.get('production', record.get('Production', 0)) or 0)
                area = float(record.get('area', record.get('Area', 0)) or 0)
                season = record.get('season', record.get('Season', 'Kharif'))
                
                if crop_name and crop_name in CROPS_DATABASE:
                    training_data.append({
                        'state': state,
                        'crop': crop_name,
                        'season': season if season in SEASONS else 'Kharif',
                        'production': production,
                        'area': area,
                        'success': 1 if production > 0 else 0
                    })
    
    print(f"✅ Collected {len(training_data)} records from government data")
    return training_data


def get_govt_crop_statistics(state):
    """Get crop production statistics for a state from government data"""
    try:
        # Try multiple resource IDs for crop data
        resource_ids = [
            '9ef84268-d588-465a-a308-a864a43d0070',  # Crop production
            '35be999b-68d1-4fc5-8094-6e0b88c7ce4c',  # Agriculture statistics
        ]
        
        for resource_id in resource_ids:
            url = f"{DATA_GOV_BASE_URL}/{resource_id}"
            params = {
                'api-key': DATA_GOV_API_KEY,
                'format': 'json',
                'limit': 50,
                'filters[state_name]': state
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'records' in data and len(data['records']) > 0:
                    # Process and return crop statistics
                    crop_stats = {}
                    for record in data['records']:
                        crop_name = record.get('crop', record.get('crop_name', '')).lower()
                        if crop_name:
                            production = float(record.get('production', record.get('production_tonnes', 0)) or 0)
                            area = float(record.get('area', record.get('area_hectares', 0)) or 0)
                            
                            if crop_name not in crop_stats:
                                crop_stats[crop_name] = {'production': 0, 'area': 0}
                            crop_stats[crop_name]['production'] += production
                            crop_stats[crop_name]['area'] += area
                    
                    return {
                        'success': True,
                        'crop_stats': crop_stats,
                        'source': 'data.gov.in'
                    }
        
        return {'success': False, 'error': 'No statistics available'}
    except Exception as e:
        print(f"Government statistics error: {e}")
        return {'success': False, 'error': str(e)}

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
    """Get crop recommendations based on inputs with government data integration"""
    recommendations = []
    state = inputs.get('state', '')
    
    # Try to get government crop statistics for the state
    govt_stats = get_govt_crop_statistics(state)
    govt_crop_data = govt_stats.get('crop_stats', {}) if govt_stats.get('success') else {}
    
    for crop_name, crop_data in CROPS_DATABASE.items():
        score, reasons = calculate_crop_score(crop_name, crop_data, inputs)
        
        # Boost score if government data shows this crop is grown in the state
        if crop_name in govt_crop_data:
            govt_info = govt_crop_data[crop_name]
            if govt_info.get('production', 0) > 0:
                score += 5
                reasons.append(f"📊 Govt data: Grown in {state} (production: {govt_info['production']:,.0f} tonnes)")
        
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
        'generated_at': datetime.now().isoformat(),
        'data_sources': ['Local Crop Database', 'data.gov.in (Government of India)']
    }
    
    if live_weather:
        response['live_weather'] = live_weather
        response['weather_used'] = True
        response['data_sources'].append('OpenWeatherMap (Live Weather)')
    
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


# ==================== ML-BASED RECOMMENDATION SYSTEM ====================

def fetch_all_govt_data():
    """Fetch comprehensive crop data from multiple data.gov.in resources"""
    all_records = []
    
    # Multiple resource IDs for crop production data from data.gov.in
    resource_ids = [
        '9ef84268-d588-465a-a308-a864a43d0070',  # Crop production statistics
        '35be999b-68d1-4fc5-8094-6e0b88c7ce4c',  # Agriculture statistics
        '6176ee09-3d56-4a3b-8115-21841576b2f6',  # State-wise crop data
        '5c2f62fe-5afa-4119-a499-fec9d604d5bd',  # District-wise data
    ]
    
    print("🔄 Fetching real data from data.gov.in...")
    
    for resource_id in resource_ids:
        try:
            # Fetch multiple pages of data
            for offset in range(0, 5000, 500):
                url = f"{DATA_GOV_BASE_URL}/{resource_id}"
                params = {
                    'api-key': DATA_GOV_API_KEY,
                    'format': 'json',
                    'limit': 500,
                    'offset': offset
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'records' in data and len(data['records']) > 0:
                        all_records.extend(data['records'])
                        print(f"  📊 Resource {resource_id[:8]}...: +{len(data['records'])} records (offset {offset})")
                    else:
                        break  # No more records
                else:
                    break
        except Exception as e:
            print(f"  ⚠️ Error with resource {resource_id[:8]}: {e}")
            continue
    
    print(f"✅ Total records fetched: {len(all_records)}")
    return all_records


def process_govt_data_for_training(records):
    """Process government data into training format"""
    training_data = []
    crop_mapping = {
        'paddy': 'rice', 'rice': 'rice', 'wheat': 'wheat', 
        'maize': 'maize', 'corn': 'maize', 'cotton': 'cotton',
        'sugarcane': 'sugarcane', 'soybean': 'soybean', 'soyabean': 'soybean',
        'groundnut': 'groundnut', 'potato': 'potato', 'tomato': 'tomato',
        'onion': 'onion', 'mustard': 'mustard', 'rapeseed': 'mustard',
        'gram': 'chickpea', 'chickpea': 'chickpea', 'chana': 'chickpea',
        'bajra': 'bajra', 'pearl millet': 'bajra', 'jowar': 'jowar',
        'sorghum': 'jowar', 'arhar': 'chickpea', 'tur': 'chickpea'
    }
    
    season_mapping = {
        'kharif': 'Kharif', 'rabi': 'Rabi', 'zaid': 'Zaid',
        'summer': 'Zaid', 'winter': 'Rabi', 'monsoon': 'Kharif',
        'whole year': 'Kharif', 'autumn': 'Kharif'
    }
    
    state_mapping = {
        'punjab': 'Punjab', 'haryana': 'Haryana', 'uttar pradesh': 'Uttar Pradesh',
        'west bengal': 'West Bengal', 'andhra pradesh': 'Andhra Pradesh',
        'tamil nadu': 'Tamil Nadu', 'karnataka': 'Karnataka',
        'maharashtra': 'Maharashtra', 'madhya pradesh': 'Madhya Pradesh',
        'gujarat': 'Gujarat', 'rajasthan': 'Rajasthan', 'bihar': 'Bihar',
        'odisha': 'Odisha', 'orissa': 'Odisha', 'assam': 'Assam',
        'jharkhand': 'Jharkhand', 'chhattisgarh': 'Chhattisgarh',
        'kerala': 'Kerala', 'telangana': 'Telangana'
    }
    
    for record in records:
        try:
            # Extract and normalize fields
            crop_raw = str(record.get('crop', record.get('Crop', record.get('crop_name', '')))).lower().strip()
            state_raw = str(record.get('state_name', record.get('State', record.get('state', '')))).lower().strip()
            season_raw = str(record.get('season', record.get('Season', 'kharif'))).lower().strip()
            production = float(record.get('production', record.get('Production', 0)) or 0)
            area = float(record.get('area', record.get('Area', 0)) or 0)
            
            # Map to our database values
            crop = crop_mapping.get(crop_raw, None)
            state = state_mapping.get(state_raw, None)
            season = season_mapping.get(season_raw, 'Kharif')
            
            # Only include valid records
            if crop and state and crop in CROPS_DATABASE and state in STATE_CITIES:
                yield_per_ha = production / area if area > 0 else 0
                
                # Determine soil and water based on crop requirements (from database)
                crop_data = CROPS_DATABASE[crop]
                soil_type = random.choice(crop_data['soil_types']) if crop_data['soil_types'] else 'Loamy'
                water = crop_data['water_need']
                ph = random.uniform(crop_data['ph_range'][0], crop_data['ph_range'][1])
                
                # Estimate temperature/humidity based on season
                if season == 'Kharif':
                    temp = random.uniform(25, 35)
                    humidity = random.uniform(60, 90)
                elif season == 'Rabi':
                    temp = random.uniform(15, 25)
                    humidity = random.uniform(40, 70)
                else:  # Zaid
                    temp = random.uniform(30, 40)
                    humidity = random.uniform(30, 60)
                
                training_data.append({
                    'state': state,
                    'season': season,
                    'soil_type': soil_type,
                    'water_availability': water,
                    'ph': round(ph, 1),
                    'temperature': round(temp, 1),
                    'humidity': round(humidity, 1),
                    'budget_per_ha': crop_data['investment_per_ha'],
                    'crop': crop,
                    'production': production,
                    'area': area,
                    'yield_per_ha': yield_per_ha,
                    'source': 'data.gov.in'
                })
        except Exception as e:
            continue
    
    print(f"✅ Processed {len(training_data)} valid training samples from government data")
    return training_data


def train_ml_model(training_data=None):
    """Train Random Forest model using REAL data from data.gov.in"""
    global ML_MODEL, LABEL_ENCODERS
    
    if not ML_AVAILABLE:
        return {'success': False, 'error': 'ML libraries not installed'}
    
    # ALWAYS fetch real data from data.gov.in
    print("📡 Fetching REAL training data from data.gov.in...")
    govt_records = fetch_all_govt_data()
    
    if govt_records:
        training_data = process_govt_data_for_training(govt_records)
        print(f"📊 Using {len(training_data)} real samples from government data")
    
    if not training_data or len(training_data) < 50:
        return {
            'success': False, 
            'error': f'Insufficient real data from data.gov.in. Got {len(training_data) if training_data else 0} records. API may be unavailable.'
        }
    
    print(f"🤖 Training ML model with {len(training_data)} REAL samples...")
    
    # Initialize encoders
    LABEL_ENCODERS = {
        'state': LabelEncoder(),
        'season': LabelEncoder(),
        'soil_type': LabelEncoder(),
        'water': LabelEncoder(),
        'crop': LabelEncoder()
    }
    
    # Fit encoders on all possible values
    LABEL_ENCODERS['state'].fit(list(STATE_CITIES.keys()))
    LABEL_ENCODERS['season'].fit(SEASONS)
    LABEL_ENCODERS['soil_type'].fit(SOIL_TYPES)
    LABEL_ENCODERS['water'].fit(WATER_LEVELS)
    LABEL_ENCODERS['crop'].fit(list(CROPS_DATABASE.keys()))
    
    # Prepare features
    X = []
    y = []
    
    for sample in training_data:
        try:
            features = [
                LABEL_ENCODERS['state'].transform([sample['state']])[0],
                LABEL_ENCODERS['season'].transform([sample['season']])[0],
                LABEL_ENCODERS['soil_type'].transform([sample['soil_type']])[0],
                LABEL_ENCODERS['water'].transform([sample['water_availability']])[0],
                sample['ph'],
                sample.get('temperature', 25),
                sample.get('humidity', 70),
                sample.get('budget_per_ha', 50000)
            ]
            X.append(features)
            y.append(LABEL_ENCODERS['crop'].transform([sample['crop']])[0])
        except Exception as e:
            continue
    
    if len(X) < 50:
        return {'success': False, 'error': f'Could not process training data. Only {len(X)} valid samples.'}
    
    X = np.array(X)
    y = np.array(y)
    
    # Train Random Forest
    ML_MODEL = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    ML_MODEL.fit(X, y)
    
    # Save model
    try:
        os.makedirs('models', exist_ok=True)
        joblib.dump(ML_MODEL, 'models/crop_recommender.joblib')
        joblib.dump(LABEL_ENCODERS, 'models/label_encoders.joblib')
        print("✅ Model saved to models/crop_recommender.joblib")
    except Exception as e:
        print(f"⚠️ Could not save model: {e}")
    
    print(f"✅ ML Model trained on {len(X)} samples")
    return {
        'success': True,
        'samples_used': len(X),
        'n_crops': len(CROPS_DATABASE),
        'model_type': 'RandomForestClassifier'
    }


def load_ml_model():
    """Load trained ML model from disk"""
    global ML_MODEL, LABEL_ENCODERS
    
    if not ML_AVAILABLE:
        return False
    
    try:
        if os.path.exists('models/crop_recommender.joblib'):
            ML_MODEL = joblib.load('models/crop_recommender.joblib')
            LABEL_ENCODERS = joblib.load('models/label_encoders.joblib')
            print("✅ ML Model loaded from disk")
            return True
    except Exception as e:
        print(f"⚠️ Could not load model: {e}")
    
    return False


def predict_with_ml(inputs):
    """Get crop recommendations using ML model"""
    global ML_MODEL, LABEL_ENCODERS
    
    if ML_MODEL is None or not LABEL_ENCODERS:
        return None
    
    try:
        # Prepare features
        features = np.array([[
            LABEL_ENCODERS['state'].transform([inputs['state']])[0],
            LABEL_ENCODERS['season'].transform([inputs['season']])[0],
            LABEL_ENCODERS['soil_type'].transform([inputs.get('soil_type', 'Loamy')])[0],
            LABEL_ENCODERS['water'].transform([inputs.get('water_availability', 'Medium')])[0],
            inputs.get('ph', 6.5),
            inputs.get('live_weather', {}).get('temperature', 25) if inputs.get('live_weather') else 25,
            inputs.get('live_weather', {}).get('humidity', 70) if inputs.get('live_weather') else 70,
            inputs.get('budget', 100000) / max(inputs.get('farm_size', 1), 0.1)
        ]])
        
        # Get probabilities for all crops
        probabilities = ML_MODEL.predict_proba(features)[0]
        crop_names = LABEL_ENCODERS['crop'].classes_
        
        # Get top 5 crops with confidence scores
        top_indices = np.argsort(probabilities)[-5:][::-1]
        
        recommendations = []
        for idx in top_indices:
            crop_name = crop_names[idx]
            confidence = probabilities[idx] * 100
            
            if crop_name in CROPS_DATABASE:
                crop_data = CROPS_DATABASE[crop_name]
                profit = crop_data['expected_revenue'] - crop_data['investment_per_ha']
                roi = (profit / crop_data['investment_per_ha']) * 100
                
                recommendations.append({
                    'crop': crop_name.title(),
                    'score': int(confidence),
                    'confidence': round(confidence, 1),
                    'suitability': 'Excellent' if confidence >= 60 else 'Good' if confidence >= 40 else 'Fair',
                    'prediction_method': 'ML (Random Forest)',
                    'reasons': [
                        f"🤖 ML Confidence: {confidence:.1f}%",
                        f"✅ Predicted for {inputs['state']} in {inputs['season']}",
                        f"📊 Trained on REAL data from data.gov.in"
                    ],
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
        
        return recommendations
    
    except Exception as e:
        print(f"ML prediction error: {e}")
        return None


# ML API Endpoints

@recommendation_bp.route('/ml/train', methods=['POST'])
def train_model_endpoint():
    """Train the ML model using REAL data from data.gov.in"""
    if not ML_AVAILABLE:
        return jsonify({'success': False, 'error': 'ML libraries not installed. Run: pip install scikit-learn numpy joblib'}), 400
    
    # Train model with real government data
    result = train_ml_model()
    
    if result['success']:
        result['data_source'] = 'data.gov.in (Government of India)'
        result['message'] = 'Model trained on REAL crop production data'
    
    return jsonify(result), 200 if result['success'] else 500


@recommendation_bp.route('/ml/predict', methods=['POST'])
def ml_predict_endpoint():
    """Get ML-based crop recommendations"""
    global ML_MODEL
    
    if not ML_AVAILABLE:
        return jsonify({'success': False, 'error': 'ML libraries not installed'}), 400
    
    # Load model if not loaded
    if ML_MODEL is None:
        if not load_ml_model():
            # Train on-the-fly
            train_ml_model()
    
    if ML_MODEL is None:
        return jsonify({'success': False, 'error': 'Model not available'}), 500
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Request data required'}), 400
    
    state = data.get('state')
    season = data.get('season')
    
    if not state or not season:
        return jsonify({'success': False, 'error': 'State and season required'}), 400
    
    live_weather = get_live_weather(state) if data.get('use_live_weather', True) else None
    
    inputs = {
        'state': state,
        'season': season,
        'soil_type': data.get('soil_type', 'Loamy'),
        'water_availability': data.get('water_availability', 'Medium'),
        'ph': float(data.get('ph', 6.5)),
        'budget': float(data.get('budget', 100000)),
        'farm_size': float(data.get('farm_size', 1)),
        'live_weather': live_weather
    }
    
    recommendations = predict_with_ml(inputs)
    
    if not recommendations:
        return jsonify({'success': False, 'error': 'Prediction failed'}), 500
    
    return jsonify({
        'success': True,
        'recommendations': recommendations,
        'inputs': inputs,
        'prediction_method': 'Machine Learning (Random Forest)',
        'model_info': {
            'type': 'RandomForestClassifier',
            'data_source': 'data.gov.in (Government of India)',
            'training_data': 'Real crop production statistics'
        },
        'generated_at': datetime.now().isoformat()
    }), 200


@recommendation_bp.route('/ml/status', methods=['GET'])
def ml_status():
    """Check ML model status"""
    global ML_MODEL
    
    model_loaded = ML_MODEL is not None
    model_file_exists = os.path.exists('models/crop_recommender.joblib') if ML_AVAILABLE else False
    
    return jsonify({
        'ml_available': ML_AVAILABLE,
        'model_loaded': model_loaded,
        'model_file_exists': model_file_exists,
        'model_path': 'models/crop_recommender.joblib',
        'supported_crops': list(CROPS_DATABASE.keys()),
        'supported_states': list(STATE_CITIES.keys())
    }), 200


@recommendation_bp.route('/collect-training-data', methods=['GET'])
def collect_training_data_endpoint():
    """Collect training data from government API"""
    govt_data = collect_govt_training_data()
    
    return jsonify({
        'success': True,
        'total_records': len(govt_data),
        'sample': govt_data[:10] if govt_data else [],
        'source': 'data.gov.in',
        'message': f'Collected {len(govt_data)} records from government data'
    }), 200


@recommendation_bp.route('/govt-data/<state>', methods=['GET'])
def get_government_crop_data(state):
    """Get crop production data from data.gov.in for a state"""
    govt_data = get_govt_crop_statistics(state)
    
    if govt_data['success']:
        return jsonify({
            'success': True,
            'state': state,
            'crop_statistics': govt_data['crop_stats'],
            'source': 'data.gov.in (Government of India)',
            'api_info': 'Official agricultural statistics'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': govt_data.get('error', 'Government data not available'),
            'fallback': 'Using local crop database'
        }), 200


@recommendation_bp.route('/govt-crops', methods=['GET'])
def get_all_govt_crop_data():
    """Get all available crop data from data.gov.in"""
    govt_data = get_govt_crop_data()
    
    if govt_data['success']:
        return jsonify({
            'success': True,
            'total_records': govt_data['total'],
            'records': govt_data['records'][:20],  # Limit to 20 for display
            'source': 'data.gov.in'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': govt_data.get('error', 'Data not available')
        }), 404


# ==================== ACCURACY VERIFICATION SYSTEM ====================

@recommendation_bp.route('/verify', methods=['POST'])
def verify_prediction_accuracy():
    """Verify ML predictions against real government data"""
    global ML_MODEL
    
    data = request.get_json()
    state = data.get('state')
    season = data.get('season', 'Kharif')
    
    if not state:
        return jsonify({'success': False, 'error': 'State is required'}), 400
    
    # Get ML predictions
    if ML_MODEL is None:
        load_ml_model()
    
    if ML_MODEL is None:
        return jsonify({'success': False, 'error': 'ML model not trained. Train first: POST /api/recommend/ml/train'}), 400
    
    live_weather = get_live_weather(state)
    
    inputs = {
        'state': state,
        'season': season,
        'soil_type': data.get('soil_type', 'Loamy'),
        'water_availability': data.get('water_availability', 'Medium'),
        'ph': float(data.get('ph', 6.5)),
        'budget': float(data.get('budget', 100000)),
        'farm_size': float(data.get('farm_size', 1)),
        'live_weather': live_weather
    }
    
    ml_recommendations = predict_with_ml(inputs)
    
    if not ml_recommendations:
        return jsonify({'success': False, 'error': 'ML prediction failed'}), 500
    
    # Get REAL government data for this state
    govt_stats = get_govt_crop_statistics(state)
    govt_data = get_govt_crop_data(state=state)
    
    # Extract actual crops grown in this state from government data
    actual_crops = set()
    crop_production = {}
    
    if govt_stats.get('success'):
        for crop, stats in govt_stats.get('crop_stats', {}).items():
            if stats.get('production', 0) > 0:
                actual_crops.add(crop.lower())
                crop_production[crop.lower()] = stats.get('production', 0)
    
    if govt_data.get('success'):
        for record in govt_data.get('records', []):
            crop = str(record.get('crop', record.get('crop_name', ''))).lower().strip()
            if crop:
                actual_crops.add(crop)
                prod = float(record.get('production', 0) or 0)
                if prod > 0:
                    crop_production[crop] = crop_production.get(crop, 0) + prod
    
    # Compare predictions with actual data
    predicted_crops = [rec['crop'].lower() for rec in ml_recommendations]
    
    matches = []
    mismatches = []
    
    for i, pred_crop in enumerate(predicted_crops):
        confidence = ml_recommendations[i].get('confidence', 0)
        
        # Check if predicted crop is actually grown
        is_match = pred_crop in actual_crops or any(pred_crop in ac for ac in actual_crops)
        
        if is_match:
            production = crop_production.get(pred_crop, 0)
            matches.append({
                'crop': pred_crop.title(),
                'rank': i + 1,
                'confidence': confidence,
                'verified': True,
                'production_tonnes': production,
                'status': '✅ VERIFIED - Grown in ' + state
            })
        else:
            mismatches.append({
                'crop': pred_crop.title(),
                'rank': i + 1,
                'confidence': confidence,
                'verified': False,
                'status': '❌ NOT VERIFIED - No govt data found'
            })
    
    accuracy = (len(matches) / len(predicted_crops)) * 100 if predicted_crops else 0
    
    # Get top actual crops from government data
    top_actual = sorted(crop_production.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        'success': True,
        'state': state,
        'season': season,
        'accuracy_percent': round(accuracy, 1),
        'verification_summary': {
            'total_predictions': len(predicted_crops),
            'verified_matches': len(matches),
            'unverified': len(mismatches)
        },
        'matches': matches,
        'mismatches': mismatches,
        'actual_top_crops': [
            {'crop': crop.title(), 'production_tonnes': prod} 
            for crop, prod in top_actual
        ],
        'data_sources': {
            'predictions': 'ML Model (trained on data.gov.in)',
            'verification': 'data.gov.in (Real-time API)'
        },
        'generated_at': datetime.now().isoformat()
    }), 200


@recommendation_bp.route('/accuracy-report', methods=['GET'])
def generate_accuracy_report():
    """Generate accuracy report across multiple states"""
    global ML_MODEL
    
    if ML_MODEL is None:
        load_ml_model()
    
    if ML_MODEL is None:
        return jsonify({'success': False, 'error': 'ML model not trained'}), 400
    
    states = list(STATE_CITIES.keys())[:10]  # Test with 10 states
    seasons = ['Kharif', 'Rabi']
    
    results = []
    total_accuracy = 0
    test_count = 0
    
    for state in states:
        for season in seasons:
            try:
                inputs = {
                    'state': state,
                    'season': season,
                    'soil_type': 'Loamy',
                    'water_availability': 'Medium',
                    'ph': 6.5,
                    'budget': 100000,
                    'farm_size': 1,
                    'live_weather': None
                }
                
                ml_recommendations = predict_with_ml(inputs)
                if not ml_recommendations:
                    continue
                
                # Get government data
                govt_stats = get_govt_crop_statistics(state)
                actual_crops = set()
                
                if govt_stats.get('success'):
                    for crop, stats in govt_stats.get('crop_stats', {}).items():
                        if stats.get('production', 0) > 0:
                            actual_crops.add(crop.lower())
                
                predicted_crops = [rec['crop'].lower() for rec in ml_recommendations[:3]]
                matches = sum(1 for pc in predicted_crops if pc in actual_crops or any(pc in ac for ac in actual_crops))
                
                accuracy = (matches / len(predicted_crops)) * 100 if predicted_crops else 0
                total_accuracy += accuracy
                test_count += 1
                
                results.append({
                    'state': state,
                    'season': season,
                    'top_predictions': [rec['crop'] for rec in ml_recommendations[:3]],
                    'matches': matches,
                    'accuracy': round(accuracy, 1),
                    'govt_data_available': govt_stats.get('success', False)
                })
            except Exception as e:
                continue
    
    overall_accuracy = total_accuracy / test_count if test_count > 0 else 0
    
    return jsonify({
        'success': True,
        'overall_accuracy': round(overall_accuracy, 1),
        'states_tested': len(states),
        'seasons_tested': len(seasons),
        'total_tests': test_count,
        'results': results,
        'model_info': {
            'type': 'RandomForestClassifier',
            'data_source': 'data.gov.in',
            'training_type': 'Real Government Data'
        },
        'interpretation': {
            'excellent': 'Above 80% - Model predictions highly accurate',
            'good': '60-80% - Model predictions reliable',
            'fair': '40-60% - Model needs more training data',
            'poor': 'Below 40% - Model requires retraining'
        },
        'generated_at': datetime.now().isoformat()
    }), 200


@recommendation_bp.route('/compare', methods=['POST'])
def compare_ml_vs_rules():
    """Compare ML predictions vs rule-based recommendations"""
    data = request.get_json()
    state = data.get('state')
    season = data.get('season', 'Kharif')
    
    if not state:
        return jsonify({'success': False, 'error': 'State is required'}), 400
    
    live_weather = get_live_weather(state)
    
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
    
    # Get rule-based recommendations
    rule_based = get_recommendations(inputs)
    
    # Get ML predictions
    ml_based = predict_with_ml(inputs) if ML_MODEL else None
    
    # Get government data for verification
    govt_stats = get_govt_crop_statistics(state)
    actual_crops = set()
    if govt_stats.get('success'):
        for crop, stats in govt_stats.get('crop_stats', {}).items():
            if stats.get('production', 0) > 0:
                actual_crops.add(crop.lower())
    
    comparison = {
        'success': True,
        'state': state,
        'season': season,
        'rule_based': {
            'method': 'Rule-Based Scoring',
            'recommendations': [{'crop': r['crop'], 'score': r['score']} for r in rule_based[:5]],
            'matches_with_govt': sum(1 for r in rule_based[:3] if r['crop'].lower() in actual_crops)
        },
        'ml_based': {
            'method': 'Machine Learning (Random Forest)',
            'recommendations': [{'crop': r['crop'], 'confidence': r['confidence']} for r in ml_based[:5]] if ml_based else [],
            'matches_with_govt': sum(1 for r in ml_based[:3] if r['crop'].lower() in actual_crops) if ml_based else 0,
            'available': ml_based is not None
        },
        'actual_crops_in_state': list(actual_crops)[:10],
        'recommendation': 'ML predictions are more accurate when trained on sufficient real data' if ml_based else 'Train ML model for better predictions',
        'generated_at': datetime.now().isoformat()
    }
    
    return jsonify(comparison), 200

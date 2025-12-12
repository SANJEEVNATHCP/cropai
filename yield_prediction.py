from flask import Blueprint, request, jsonify
import json
import os
import requests
from datetime import datetime, timedelta
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import pickle

yield_bp = Blueprint('yield', __name__)

# OpenWeatherMap API key
OPENWEATHER_API_KEY = 'b576d8a952bf4c45c7ef5bddb148e76b'

# NASA POWER API Base URL (FREE - No API key needed!)
NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# NASA POWER Parameters for Agriculture
NASA_AGRO_PARAMETERS = [
    'T2M',              # Temperature at 2 meters (°C)
    'T2M_MAX',          # Maximum Temperature (°C)
    'T2M_MIN',          # Minimum Temperature (°C)
    'RH2M',             # Relative Humidity (%)
    'PRECTOTCORR',      # Precipitation (mm/day)
    'ALLSKY_SFC_SW_DWN', # Solar Radiation (MJ/m²/day)
    'GWETROOT',         # Root Zone Soil Wetness (0-1)
    'GWETPROF',         # Profile Soil Wetness (0-1)
    'EVPTRNS',          # Evapotranspiration (mm/day)
    'WS2M',             # Wind Speed (m/s)
]

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


# ============= NASA POWER FUNCTIONS =============

def get_nasa_power_data(state, days=14):
    """Fetch agricultural data from NASA POWER API (FREE - No API key needed)"""
    if state not in STATE_CITIES:
        return None
    
    coords = STATE_CITIES[state]
    end_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days+7)).strftime('%Y%m%d')
    
    params = {
        'parameters': ','.join(NASA_AGRO_PARAMETERS),
        'community': 'AG',
        'longitude': coords['lon'],
        'latitude': coords['lat'],
        'start': start_date,
        'end': end_date,
        'format': 'JSON'
    }
    
    try:
        print(f"[NASA POWER] Fetching data for {state}...")
        response = requests.get(NASA_POWER_BASE_URL, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            raw_data = data.get('properties', {}).get('parameter', {})
            processed = process_nasa_data(raw_data, state, coords)
            print(f"[NASA POWER] Success! Got data for {state}")
            return processed
    except Exception as e:
        print(f"[NASA POWER] Error: {e}")
    return None


def process_nasa_data(raw_data, state, coords):
    """Process NASA POWER data into usable format"""
    processed = {
        'state': state,
        'coordinates': coords,
        'source': 'NASA POWER'
    }
    
    for param, values in raw_data.items():
        if isinstance(values, dict):
            valid = [v for v in values.values() if v != -999 and v is not None]
            if valid:
                processed[param] = {
                    'average': round(sum(valid) / len(valid), 2),
                    'min': round(min(valid), 2),
                    'max': round(max(valid), 2)
                }
    
    # Calculate soil moisture index (0-1 scale)
    root_wet = processed.get('GWETROOT', {}).get('average', 0.5)
    prof_wet = processed.get('GWETPROF', {}).get('average', 0.5)
    soil_moisture = round(root_wet * 0.6 + prof_wet * 0.4, 3)
    processed['soil_moisture_index'] = soil_moisture
    
    # Determine soil condition
    if soil_moisture >= 0.8:
        processed['soil_condition'] = 'Waterlogged'
    elif soil_moisture >= 0.6:
        processed['soil_condition'] = 'Adequate'
    elif soil_moisture >= 0.4:
        processed['soil_condition'] = 'Moderate'
    elif soil_moisture >= 0.2:
        processed['soil_condition'] = 'Dry'
    else:
        processed['soil_condition'] = 'Very Dry'
    
    return processed


def calculate_nasa_yield_factor(nasa_data, crop):
    """Calculate yield adjustment factor based on NASA data"""
    if not nasa_data:
        return 1.0, []
    
    insights = []
    factors = []
    
    # Soil moisture factor
    soil_moisture = nasa_data.get('soil_moisture_index', 0.5)
    if 0.4 <= soil_moisture <= 0.7:
        soil_factor = 1.1
        insights.append(f"🛰️ NASA: Soil moisture ({soil_moisture:.2f}) is optimal")
    elif soil_moisture < 0.2:
        soil_factor = 0.7
        insights.append(f"🛰️ NASA: Soil very dry ({soil_moisture:.2f}) - needs irrigation")
    elif soil_moisture > 0.8:
        soil_factor = 0.8
        insights.append(f"🛰️ NASA: Soil waterlogged ({soil_moisture:.2f}) - needs drainage")
    else:
        soil_factor = 0.9
    factors.append(soil_factor)
    
    # Temperature factor
    temp = nasa_data.get('T2M', {}).get('average', 25)
    if 20 <= temp <= 30:
        temp_factor = 1.1
        insights.append(f"🛰️ NASA: Temperature ({temp:.1f}°C) is ideal")
    elif temp < 15 or temp > 38:
        temp_factor = 0.7
    else:
        temp_factor = 0.95
    factors.append(temp_factor)
    
    # Solar radiation factor
    solar = nasa_data.get('ALLSKY_SFC_SW_DWN', {}).get('average', 18)
    if 15 <= solar <= 22:
        solar_factor = 1.1
        insights.append(f"🛰️ NASA: Solar radiation ({solar:.1f} MJ/m²) excellent")
    elif solar < 10:
        solar_factor = 0.8
    else:
        solar_factor = 1.0
    factors.append(solar_factor)
    
    combined_factor = sum(factors) / len(factors)
    return round(combined_factor, 3), insights

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

# Crop yield data (average yields in kg/hectare for India)
CROP_YIELD_DATA = {
    'rice': {'avg_yield': 2500, 'optimal_n': 120, 'optimal_p': 60, 'optimal_k': 40, 'optimal_ph': (5.5, 7.0), 'water_need': 'High'},
    'wheat': {'avg_yield': 3200, 'optimal_n': 120, 'optimal_p': 60, 'optimal_k': 40, 'optimal_ph': (6.0, 7.5), 'water_need': 'Medium'},
    'maize': {'avg_yield': 2800, 'optimal_n': 150, 'optimal_p': 75, 'optimal_k': 50, 'optimal_ph': (5.8, 7.0), 'water_need': 'Medium'},
    'cotton': {'avg_yield': 500, 'optimal_n': 100, 'optimal_p': 50, 'optimal_k': 50, 'optimal_ph': (6.0, 8.0), 'water_need': 'Medium'},
    'sugarcane': {'avg_yield': 70000, 'optimal_n': 250, 'optimal_p': 100, 'optimal_k': 120, 'optimal_ph': (6.0, 7.5), 'water_need': 'High'},
    'soybean': {'avg_yield': 1200, 'optimal_n': 25, 'optimal_p': 60, 'optimal_k': 40, 'optimal_ph': (6.0, 7.0), 'water_need': 'Medium'},
    'groundnut': {'avg_yield': 1500, 'optimal_n': 20, 'optimal_p': 40, 'optimal_k': 50, 'optimal_ph': (6.0, 6.5), 'water_need': 'Low'},
    'potato': {'avg_yield': 22000, 'optimal_n': 180, 'optimal_p': 100, 'optimal_k': 150, 'optimal_ph': (5.5, 6.5), 'water_need': 'High'},
    'tomato': {'avg_yield': 25000, 'optimal_n': 150, 'optimal_p': 80, 'optimal_k': 100, 'optimal_ph': (6.0, 7.0), 'water_need': 'High'},
    'onion': {'avg_yield': 18000, 'optimal_n': 100, 'optimal_p': 50, 'optimal_k': 80, 'optimal_ph': (6.0, 7.0), 'water_need': 'Medium'},
    'mustard': {'avg_yield': 1200, 'optimal_n': 80, 'optimal_p': 40, 'optimal_k': 40, 'optimal_ph': (6.0, 7.5), 'water_need': 'Low'},
    'chickpea': {'avg_yield': 1000, 'optimal_n': 20, 'optimal_p': 50, 'optimal_k': 20, 'optimal_ph': (6.0, 8.0), 'water_need': 'Low'},
    'bajra': {'avg_yield': 1200, 'optimal_n': 60, 'optimal_p': 30, 'optimal_k': 30, 'optimal_ph': (6.5, 7.5), 'water_need': 'Low'},
    'jowar': {'avg_yield': 1100, 'optimal_n': 80, 'optimal_p': 40, 'optimal_k': 40, 'optimal_ph': (6.0, 7.5), 'water_need': 'Low'},
}

# State-wise yield adjustment factors
STATE_FACTORS = {
    'Punjab': 1.25, 'Haryana': 1.20, 'Uttar Pradesh': 1.10,
    'West Bengal': 1.15, 'Andhra Pradesh': 1.10, 'Tamil Nadu': 1.05,
    'Karnataka': 1.00, 'Maharashtra': 0.95, 'Madhya Pradesh': 0.95,
    'Gujarat': 1.05, 'Rajasthan': 0.85, 'Bihar': 1.00,
    'Odisha': 0.95, 'Assam': 0.90, 'Jharkhand': 0.85,
    'Chhattisgarh': 0.90, 'Kerala': 1.00, 'Telangana': 1.05,
}


def calculate_soil_factor(crop, n, p, k, ph):
    """Calculate yield factor based on soil nutrients"""
    if crop not in CROP_YIELD_DATA:
        return 1.0
    
    crop_data = CROP_YIELD_DATA[crop]
    
    # NPK factor (0.5 to 1.2)
    n_ratio = min(n / crop_data['optimal_n'], 1.2) if crop_data['optimal_n'] > 0 else 1.0
    p_ratio = min(p / crop_data['optimal_p'], 1.2) if crop_data['optimal_p'] > 0 else 1.0
    k_ratio = min(k / crop_data['optimal_k'], 1.2) if crop_data['optimal_k'] > 0 else 1.0
    
    npk_factor = (n_ratio * 0.4 + p_ratio * 0.3 + k_ratio * 0.3)
    
    # pH factor
    optimal_ph_min, optimal_ph_max = crop_data['optimal_ph']
    if optimal_ph_min <= ph <= optimal_ph_max:
        ph_factor = 1.0
    elif ph < optimal_ph_min:
        ph_factor = max(0.7, 1 - (optimal_ph_min - ph) * 0.1)
    else:
        ph_factor = max(0.7, 1 - (ph - optimal_ph_max) * 0.1)
    
    return npk_factor * ph_factor


def calculate_weather_factor(crop, rainfall, temperature, humidity):
    """Calculate yield factor based on weather conditions"""
    if crop not in CROP_YIELD_DATA:
        return 1.0
    
    crop_data = CROP_YIELD_DATA[crop]
    water_need = crop_data['water_need']
    
    # Rainfall factor
    if water_need == 'High':
        optimal_rainfall = 1200
    elif water_need == 'Medium':
        optimal_rainfall = 800
    else:
        optimal_rainfall = 400
    
    rainfall_ratio = rainfall / optimal_rainfall if optimal_rainfall > 0 else 1.0
    if rainfall_ratio > 1.5:
        rainfall_factor = max(0.6, 1.5 - (rainfall_ratio - 1.5) * 0.5)
    elif rainfall_ratio < 0.5:
        rainfall_factor = max(0.5, rainfall_ratio * 1.5)
    else:
        rainfall_factor = min(1.2, 0.8 + rainfall_ratio * 0.3)
    
    # Temperature factor (optimal 20-30°C for most crops)
    if 20 <= temperature <= 30:
        temp_factor = 1.0
    elif temperature < 20:
        temp_factor = max(0.6, 1 - (20 - temperature) * 0.03)
    else:
        temp_factor = max(0.6, 1 - (temperature - 30) * 0.03)
    
    # Humidity factor
    if 60 <= humidity <= 80:
        humidity_factor = 1.0
    else:
        humidity_factor = max(0.8, 1 - abs(humidity - 70) * 0.005)
    
    return rainfall_factor * 0.4 + temp_factor * 0.35 + humidity_factor * 0.25


def predict_yield(crop, state, n, p, k, ph, rainfall, temperature, humidity, area=1, nasa_factor=1.0):
    """Main yield prediction function with NASA satellite data support"""
    crop = crop.lower()
    
    if crop not in CROP_YIELD_DATA:
        return None, "Crop not found in database"
    
    base_yield = CROP_YIELD_DATA[crop]['avg_yield']
    
    # Apply factors
    soil_factor = calculate_soil_factor(crop, n, p, k, ph)
    weather_factor = calculate_weather_factor(crop, rainfall, temperature, humidity)
    state_factor = STATE_FACTORS.get(state, 1.0)
    
    # Calculate predicted yield with NASA satellite factor
    predicted_yield = base_yield * soil_factor * weather_factor * state_factor * nasa_factor
    
    # Confidence calculation (higher with NASA data)
    base_confidence = 70 + soil_factor * 10 + weather_factor * 10
    if nasa_factor != 1.0:
        base_confidence += 5  # Higher confidence with satellite data
    confidence = min(95, base_confidence)
    
    # Category
    yield_ratio = predicted_yield / base_yield
    if yield_ratio >= 1.1:
        category = 'High'
    elif yield_ratio >= 0.9:
        category = 'Medium'
    else:
        category = 'Low'
    
    # Generate insights
    insights = generate_insights(crop, soil_factor, weather_factor, state_factor, n, p, k, ph, rainfall)
    recommendations = generate_recommendations(crop, n, p, k, ph, rainfall, category)
    
    return {
        'crop': crop.title(),
        'predicted_yield': round(predicted_yield, 2),
        'total_yield': round(predicted_yield * area, 2),
        'unit': 'kg/hectare',
        'confidence': round(confidence, 1),
        'category': category,
        'base_yield': base_yield,
        'factors': {
            'soil_factor': round(soil_factor, 2),
            'weather_factor': round(weather_factor, 2),
            'state_factor': round(state_factor, 2)
        },
        'insights': insights,
        'recommendations': recommendations
    }, None


def generate_insights(crop, soil_factor, weather_factor, state_factor, n, p, k, ph, rainfall):
    """Generate AI-like insights"""
    insights = []
    
    if soil_factor < 0.9:
        insights.append("⚠️ Soil nutrients are below optimal levels. Consider soil testing and fertilizer application.")
    elif soil_factor > 1.1:
        insights.append("✅ Excellent soil nutrient levels for this crop.")
    
    if weather_factor < 0.9:
        insights.append("⚠️ Weather conditions may impact yield. Consider irrigation or protective measures.")
    elif weather_factor > 1.05:
        insights.append("✅ Weather conditions are favorable for high yield.")
    
    if state_factor > 1.1:
        insights.append(f"✅ Your state has historically higher yields for {crop}.")
    elif state_factor < 0.9:
        insights.append(f"📊 Average yields for {crop} in your state are typically lower. Focus on best practices.")
    
    crop_data = CROP_YIELD_DATA.get(crop.lower(), {})
    if crop_data:
        if n < crop_data.get('optimal_n', 0) * 0.7:
            insights.append(f"💡 Nitrogen levels are low. Recommended: {crop_data['optimal_n']} kg/ha")
        if p < crop_data.get('optimal_p', 0) * 0.7:
            insights.append(f"💡 Phosphorus levels are low. Recommended: {crop_data['optimal_p']} kg/ha")
        if k < crop_data.get('optimal_k', 0) * 0.7:
            insights.append(f"💡 Potassium levels are low. Recommended: {crop_data['optimal_k']} kg/ha")
    
    return insights


def generate_recommendations(crop, n, p, k, ph, rainfall, category):
    """Generate actionable recommendations"""
    recommendations = []
    crop_data = CROP_YIELD_DATA.get(crop.lower(), {})
    
    if category == 'Low':
        recommendations.append("🔴 Consider soil amendment and improved irrigation")
        recommendations.append("🔴 Consult with an agricultural expert via LiveKit call")
    elif category == 'Medium':
        recommendations.append("🟡 Minor improvements in fertilizer management can boost yield")
    else:
        recommendations.append("🟢 Maintain current practices for optimal results")
    
    if crop_data:
        if crop_data.get('water_need') == 'High' and rainfall < 800:
            recommendations.append("💧 This crop needs high water. Ensure adequate irrigation.")
        
        optimal_ph = crop_data.get('optimal_ph', (6.0, 7.0))
        if ph < optimal_ph[0]:
            recommendations.append("🧪 Soil is too acidic. Consider lime application.")
        elif ph > optimal_ph[1]:
            recommendations.append("🧪 Soil is too alkaline. Consider sulfur or organic matter.")
    
    recommendations.append("📅 Schedule a call with our agricultural expert for personalized advice")
    
    return recommendations


# Placeholder for data collection from APIs
def collect_data():
    # Simulate data collection from NASA POWER and OpenWeather APIs
    data = {
        'temperature': [25, 30, 28, 22, 27],
        'humidity': [60, 65, 70, 55, 68],
        'precipitation': [5, 10, 0, 2, 8],
        'solar_radiation': [18, 20, 19, 17, 21],
        'soil_moisture': [0.5, 0.6, 0.4, 0.3, 0.7],
        'yield': [4000, 4500, 4200, 3800, 4600]
    }
    return pd.DataFrame(data)

# Train the ML model
def train_model():
    data = collect_data()
    X = data.drop(columns=['yield'])
    y = data['yield']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    print(f"Model trained. Mean Squared Error: {mse}")

    # Save the model
    with open('yield_model.pkl', 'wb') as f:
        pickle.dump(model, f)

# Predict yield using the trained model
def predict_yield_model(features):
    print("[DEBUG] ML MODEL: Predicting yield with features:", features)
    with open('yield_model.pkl', 'rb') as f:
        model = pickle.load(f)
    
    prediction = model.predict([features])
    print("[DEBUG] ML MODEL: Prediction result:", prediction[0])
    return prediction[0]

@yield_bp.route('/predict', methods=['POST'])
def predict():
    """Predict crop yield based on inputs"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Request data required'}), 400
    
    # Required fields
    crop = data.get('crop')
    state = data.get('state')
    
    if not crop or not state:
        return jsonify({'success': False, 'error': 'Crop and state are required'}), 400
    
    # Get parameters with defaults
    n = float(data.get('nitrogen', 80))
    p = float(data.get('phosphorus', 40))
    k = float(data.get('potassium', 40))
    ph = float(data.get('ph', 6.5))
    rainfall = float(data.get('rainfall', 800))
    area = float(data.get('area', 1))
    
    # Try to get NASA POWER satellite data
    nasa_data = None
    nasa_factor = 1.0
    nasa_insights = []
    if data.get('use_nasa_data', True):
        nasa_data = get_nasa_power_data(state)
        if nasa_data:
            nasa_factor, nasa_insights = calculate_nasa_yield_factor(nasa_data, crop)
    
    # Try to get live weather data
    live_weather = get_live_weather(state)
    weather_source = 'live' if live_weather else 'user_input'
    
    if live_weather and data.get('use_live_weather', True):
        temperature = live_weather['temperature']
        humidity = live_weather['humidity']
    else:
        temperature = float(data.get('temperature', 25))
        humidity = float(data.get('humidity', 70))
    
    result, error = predict_yield(crop, state, n, p, k, ph, rainfall, temperature, humidity, area, nasa_factor)
    
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    # Add NASA insights to result
    if nasa_insights:
        result['insights'] = nasa_insights + result['insights']
    
    # Add NASA factor to result
    if nasa_data:
        result['factors']['nasa_satellite_factor'] = nasa_factor
    
    response_data = {
        'success': True,
        'prediction': result,
        'inputs': {
            'crop': crop,
            'state': state,
            'area': area,
            'soil': {'n': n, 'p': p, 'k': k, 'ph': ph},
            'weather': {'rainfall': rainfall, 'temperature': temperature, 'humidity': humidity}
        },
        'weather_source': weather_source,
        'data_sources': ['user_input']
    }
    
    if live_weather:
        response_data['live_weather'] = live_weather
        response_data['data_sources'].append('OpenWeatherMap')
    
    if nasa_data:
        response_data['nasa_data'] = {
            'soil_moisture_index': nasa_data.get('soil_moisture_index'),
            'soil_condition': nasa_data.get('soil_condition'),
            'temperature': nasa_data.get('T2M', {}).get('average'),
            'humidity': nasa_data.get('RH2M', {}).get('average'),
            'solar_radiation': nasa_data.get('ALLSKY_SFC_SW_DWN', {}).get('average'),
            'precipitation': nasa_data.get('PRECTOTCORR', {}).get('average')
        }
        response_data['data_sources'].append('NASA POWER')
    
    return jsonify(response_data), 200


@yield_bp.route('/nasa-data/<state>', methods=['GET'])
def get_nasa_soil_data(state):
    """Get NASA POWER satellite data for a state - soil moisture, temperature, etc."""
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


@yield_bp.route('/weather/<state>', methods=['GET'])
def get_state_weather(state):
    """Get live weather for a state"""
    weather = get_live_weather(state)
    if weather:
        return jsonify({'success': True, 'weather': weather})
    return jsonify({'success': False, 'error': 'Weather data not available'}), 404


@yield_bp.route('/crops', methods=['GET'])
def get_crops():
    """Get list of supported crops"""
    crops = []
    for crop, data in CROP_YIELD_DATA.items():
        crops.append({
            'name': crop.title(),
            'value': crop,
            'avg_yield': data['avg_yield'],
            'water_need': data['water_need'],
            'unit': 'kg/hectare'
        })
    
    return jsonify({
        'success': True,
        'crops': crops,
        'total': len(crops)
    }), 200


@yield_bp.route('/states', methods=['GET'])
def get_states():
    """Get list of Indian states"""
    states = list(STATE_FACTORS.keys())
    return jsonify({
        'success': True,
        'states': states
    }), 200

def collect_data():
    # Simulate data collection from NASA POWER and OpenWeather APIs
    data = {
        'temperature': [25, 30, 28, 22, 27],
        'humidity': [60, 65, 70, 55, 68],
        'precipitation': [5, 10, 0, 2, 8],
        'solar_radiation': [18, 20, 19, 17, 21],
        'soil_moisture': [0.5, 0.6, 0.4, 0.3, 0.7],
        'yield': [4000, 4500, 4200, 3800, 4600]
    }
    return pd.DataFrame(data)

# Train the ML model
def train_model():
    data = collect_data()
    X = data.drop(columns=['yield'])
    y = data['yield']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    # Save the model
    with open('yield_model.pkl', 'wb') as f:
        pickle.dump(model, f)

# Predict yield using the trained model
def predict_yield_model(features):
    with open('yield_model.pkl', 'rb') as f:
        model = pickle.load(f)
    
    prediction = model.predict([features])
    return prediction[0]

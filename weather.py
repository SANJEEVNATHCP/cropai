"""
Real-Time Weather API Routes
Uses OpenWeatherMap API for live weather data with simulated fallback
"""
from flask import Blueprint, request, jsonify
import os
import random
from datetime import datetime, timedelta

weather_bp = Blueprint('weather', __name__)

# OpenWeatherMap API key
OPENWEATHER_API_KEY = 'b576d8a952bf4c45c7ef5bddb148e76b'

# Major Indian cities with coordinates
INDIAN_CITIES = {
    'Delhi': {'lat': 28.6139, 'lon': 77.2090, 'state': 'Delhi'},
    'Mumbai': {'lat': 19.0760, 'lon': 72.8777, 'state': 'Maharashtra'},
    'Bangalore': {'lat': 12.9716, 'lon': 77.5946, 'state': 'Karnataka'},
    'Chennai': {'lat': 13.0827, 'lon': 80.2707, 'state': 'Tamil Nadu'},
    'Kolkata': {'lat': 22.5726, 'lon': 88.3639, 'state': 'West Bengal'},
    'Hyderabad': {'lat': 17.3850, 'lon': 78.4867, 'state': 'Telangana'},
    'Ahmedabad': {'lat': 23.0225, 'lon': 72.5714, 'state': 'Gujarat'},
    'Pune': {'lat': 18.5204, 'lon': 73.8567, 'state': 'Maharashtra'},
    'Jaipur': {'lat': 26.9124, 'lon': 75.7873, 'state': 'Rajasthan'},
    'Lucknow': {'lat': 26.8467, 'lon': 80.9462, 'state': 'Uttar Pradesh'},
    'Kanpur': {'lat': 26.4499, 'lon': 80.3319, 'state': 'Uttar Pradesh'},
    'Nagpur': {'lat': 21.1458, 'lon': 79.0882, 'state': 'Maharashtra'},
    'Indore': {'lat': 22.7196, 'lon': 75.8577, 'state': 'Madhya Pradesh'},
    'Bhopal': {'lat': 23.2599, 'lon': 77.4126, 'state': 'Madhya Pradesh'},
    'Patna': {'lat': 25.5941, 'lon': 85.1376, 'state': 'Bihar'},
    'Chandigarh': {'lat': 30.7333, 'lon': 76.7794, 'state': 'Punjab'},
    'Amritsar': {'lat': 31.6340, 'lon': 74.8723, 'state': 'Punjab'},
    'Ludhiana': {'lat': 30.9010, 'lon': 75.8573, 'state': 'Punjab'},
    'Coimbatore': {'lat': 11.0168, 'lon': 76.9558, 'state': 'Tamil Nadu'},
    'Kochi': {'lat': 9.9312, 'lon': 76.2673, 'state': 'Kerala'},
    'Thiruvananthapuram': {'lat': 8.5241, 'lon': 76.9366, 'state': 'Kerala'},
    'Visakhapatnam': {'lat': 17.6868, 'lon': 83.2185, 'state': 'Andhra Pradesh'},
    'Surat': {'lat': 21.1702, 'lon': 72.8311, 'state': 'Gujarat'},
    'Ranchi': {'lat': 23.3441, 'lon': 85.3096, 'state': 'Jharkhand'},
    'Guwahati': {'lat': 26.1445, 'lon': 91.7362, 'state': 'Assam'},
    'Bhubaneswar': {'lat': 20.2961, 'lon': 85.8245, 'state': 'Odisha'},
    'Raipur': {'lat': 21.2514, 'lon': 81.6296, 'state': 'Chhattisgarh'},
}


def get_weather_icon(condition):
    """Get emoji icon for weather condition"""
    icons = {
        'Clear': '☀️', 'Sunny': '☀️',
        'Clouds': '☁️', 'Cloudy': '☁️', 'Partly Cloudy': '⛅',
        'Rain': '🌧️', 'Light Rain': '🌦️', 'Heavy Rain': '⛈️',
        'Drizzle': '🌦️', 'Thunderstorm': '⛈️',
        'Mist': '🌫️', 'Fog': '🌫️', 'Haze': '🌫️',
        'Snow': '❄️', 'Cold': '🥶', 'Hot': '🔥',
    }
    return icons.get(condition, '🌤️')


def get_simulated_weather(city):
    """Generate realistic weather based on location and season"""
    city_data = INDIAN_CITIES.get(city, INDIAN_CITIES['Delhi'])
    
    # Base temp varies by latitude
    base_temp = 28 - (city_data['lat'] - 20) * 0.4
    
    # Seasonal adjustment (December = winter)
    month = datetime.now().month
    if month in [12, 1, 2]:  # Winter
        seasonal_adj = -8
        conditions = ['Clear', 'Mist', 'Fog', 'Clouds']
        humidity_base = 60
    elif month in [3, 4, 5]:  # Summer
        seasonal_adj = 12
        conditions = ['Clear', 'Hot', 'Haze', 'Clouds']
        humidity_base = 35
    elif month in [6, 7, 8, 9]:  # Monsoon
        seasonal_adj = 3
        conditions = ['Rain', 'Heavy Rain', 'Thunderstorm', 'Clouds', 'Light Rain']
        humidity_base = 85
    else:  # Post-monsoon
        seasonal_adj = 0
        conditions = ['Clear', 'Clouds', 'Mist']
        humidity_base = 55
    
    # Regional adjustments
    if city_data['state'] in ['Kerala', 'West Bengal', 'Assam', 'Odisha']:
        humidity_base += 15
    elif city_data['state'] in ['Rajasthan', 'Gujarat']:
        humidity_base -= 15
    
    temp = base_temp + seasonal_adj + random.uniform(-2, 2)
    humidity = max(30, min(95, humidity_base + random.uniform(-10, 10)))
    condition = random.choice(conditions)
    
    return {
        'temperature': round(temp, 1),
        'feels_like': round(temp + random.uniform(-2, 3), 1),
        'humidity': round(humidity),
        'pressure': random.randint(1005, 1020),
        'wind_speed': round(random.uniform(5, 25), 1),
        'wind_direction': random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']),
        'condition': condition,
        'description': condition.lower(),
        'icon': get_weather_icon(condition),
        'visibility': round(random.uniform(3, 10), 1),
        'clouds': random.randint(10, 90),
        'rain_chance': random.randint(60, 95) if 'Rain' in condition else random.randint(5, 30),
        'uv_index': round(random.uniform(3, 11), 1),
    }


def get_farming_advice(weather):
    """Generate farming advice based on weather"""
    advice = []
    temp = weather['temperature']
    humidity = weather['humidity']
    condition = weather['condition']
    rain_chance = weather.get('rain_chance', 0)
    
    # Temperature advice
    if temp > 40:
        advice.append({
            'icon': '🔥',
            'type': 'danger',
            'title': 'Extreme Heat Warning',
            'message': 'Avoid fieldwork 11 AM - 4 PM. Irrigate early morning/evening. Provide shade to nurseries.'
        })
    elif temp > 35:
        advice.append({
            'icon': '☀️',
            'type': 'warning',
            'title': 'Hot Weather',
            'message': 'Increase irrigation frequency. Apply mulch to retain soil moisture.'
        })
    elif temp < 10:
        advice.append({
            'icon': '❄️',
            'type': 'warning',
            'title': 'Frost Risk',
            'message': 'Protect frost-sensitive crops. Cover seedlings at night.'
        })
    elif 20 <= temp <= 30:
        advice.append({
            'icon': '✅',
            'type': 'success',
            'title': 'Ideal Temperature',
            'message': 'Good conditions for most farming activities.'
        })
    
    # Rain/Weather advice
    if 'Rain' in condition or rain_chance > 60:
        advice.append({
            'icon': '🌧️',
            'type': 'info',
            'title': 'Rain Expected',
            'message': 'Postpone pesticide/fertilizer spraying. Check field drainage. Good time for transplanting.'
        })
    elif condition == 'Clear':
        advice.append({
            'icon': '☀️',
            'type': 'success',
            'title': 'Clear Weather',
            'message': 'Ideal for spraying pesticides. Good for harvesting and drying crops.'
        })
    
    # Humidity advice
    if humidity > 85:
        advice.append({
            'icon': '💧',
            'type': 'warning',
            'title': 'High Humidity',
            'message': 'Watch for fungal diseases. Ensure proper plant spacing for air circulation.'
        })
    
    # Wind advice
    if weather['wind_speed'] > 30:
        advice.append({
            'icon': '💨',
            'type': 'warning',
            'title': 'Strong Winds',
            'message': 'Avoid spraying operations. Secure poly houses and support tall crops.'
        })
    
    # Season-based advice
    month = datetime.now().month
    if month in [6, 7]:
        advice.append({
            'icon': '🌱',
            'type': 'info',
            'title': 'Kharif Season',
            'message': 'Ideal time for sowing paddy, maize, cotton, soybean.'
        })
    elif month in [10, 11]:
        advice.append({
            'icon': '🌾',
            'type': 'info',
            'title': 'Rabi Season',
            'message': 'Best time for wheat, mustard, chickpea sowing.'
        })
    
    return advice[:5]


def get_7day_forecast(city):
    """Generate 7-day forecast"""
    forecast = []
    base_weather = get_simulated_weather(city)
    
    for i in range(7):
        day_date = datetime.now() + timedelta(days=i)
        temp_var = random.uniform(-4, 4)
        
        conditions = ['Clear', 'Clouds', 'Light Rain', 'Partly Cloudy']
        condition = random.choice(conditions)
        
        forecast.append({
            'date': day_date.strftime('%Y-%m-%d'),
            'day': day_date.strftime('%A'),
            'day_short': day_date.strftime('%a'),
            'temp_max': round(base_weather['temperature'] + temp_var + 3, 1),
            'temp_min': round(base_weather['temperature'] + temp_var - 5, 1),
            'humidity': random.randint(45, 85),
            'condition': condition,
            'icon': get_weather_icon(condition),
            'rain_chance': random.randint(60, 90) if 'Rain' in condition else random.randint(5, 25),
            'wind_speed': round(random.uniform(5, 20), 1),
        })
    
    return forecast


@weather_bp.route('/current', methods=['GET'])
def get_current_weather():
    """Get current weather for a city"""
    city = request.args.get('city', 'Delhi')
    
    if city not in INDIAN_CITIES:
        return jsonify({
            'success': False,
            'error': f'City not found. Available cities: {", ".join(list(INDIAN_CITIES.keys())[:10])}...'
        }), 404
    
    city_data = INDIAN_CITIES[city]
    
    # Try real API if key available
    if OPENWEATHER_API_KEY:
        try:
            import requests
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
                weather = {
                    'temperature': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'wind_speed': round(data['wind']['speed'] * 3.6, 1),
                    'condition': data['weather'][0]['main'],
                    'description': data['weather'][0]['description'],
                    'icon': get_weather_icon(data['weather'][0]['main']),
                    'clouds': data['clouds']['all'],
                    'visibility': data.get('visibility', 10000) / 1000,
                }
                
                return jsonify({
                    'success': True,
                    'city': city,
                    'state': city_data['state'],
                    'weather': weather,
                    'farming_advice': get_farming_advice(weather),
                    'updated_at': datetime.now().strftime('%I:%M %p'),
                    'source': 'live'
                })
        except Exception as e:
            print(f"Weather API error: {e}")
    
    # Fallback to simulated data
    weather = get_simulated_weather(city)
    
    return jsonify({
        'success': True,
        'city': city,
        'state': city_data['state'],
        'weather': weather,
        'farming_advice': get_farming_advice(weather),
        'updated_at': datetime.now().strftime('%I:%M %p'),
        'source': 'simulated'
    })


@weather_bp.route('/forecast', methods=['GET'])
def get_forecast():
    """Get 7-day weather forecast"""
    city = request.args.get('city', 'Delhi')
    
    if city not in INDIAN_CITIES:
        return jsonify({'success': False, 'error': 'City not found'}), 404
    
    return jsonify({
        'success': True,
        'city': city,
        'state': INDIAN_CITIES[city]['state'],
        'forecast': get_7day_forecast(city),
        'source': 'simulated'
    })


@weather_bp.route('/cities', methods=['GET'])
def get_cities():
    """Get list of available cities"""
    cities = []
    for city, data in INDIAN_CITIES.items():
        cities.append({
            'name': city,
            'state': data['state']
        })
    
    cities.sort(key=lambda x: x['name'])
    
    return jsonify({
        'success': True,
        'cities': cities,
        'total': len(cities)
    })


@weather_bp.route('/alerts', methods=['GET'])
def get_weather_alerts():
    """Get weather alerts for farming"""
    city = request.args.get('city', 'Delhi')
    
    if city not in INDIAN_CITIES:
        return jsonify({'success': False, 'error': 'City not found'}), 404
    
    weather = get_simulated_weather(city)
    alerts = []
    
    # Generate alerts
    if weather['temperature'] > 40:
        alerts.append({
            'severity': 'danger',
            'icon': '🔥',
            'title': 'Heat Wave Alert',
            'message': f"Extreme heat ({weather['temperature']}°C). Protect crops and avoid outdoor work.",
        })
    
    if 'Rain' in weather['condition'] or weather['rain_chance'] > 70:
        alerts.append({
            'severity': 'warning',
            'icon': '🌧️',
            'title': 'Rain Alert',
            'message': 'Heavy rain expected. Secure harvested crops and check drainage.',
        })
    
    if weather['humidity'] > 90:
        alerts.append({
            'severity': 'info',
            'icon': '💦',
            'title': 'High Humidity',
            'message': 'Fungal disease risk is high. Monitor crops closely.',
        })
    
    if weather['wind_speed'] > 35:
        alerts.append({
            'severity': 'warning',
            'icon': '💨',
            'title': 'Strong Wind Alert',
            'message': 'Winds may damage crops. Support tall plants.',
        })
    
    if not alerts:
        alerts.append({
            'severity': 'success',
            'icon': '✅',
            'title': 'Good Conditions',
            'message': 'Weather is favorable for farming activities.',
        })
    
    return jsonify({
        'success': True,
        'city': city,
        'alerts': alerts,
        'current': {
            'temp': weather['temperature'],
            'condition': weather['condition'],
            'humidity': weather['humidity']
        }
    })

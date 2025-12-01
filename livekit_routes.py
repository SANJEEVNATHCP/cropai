from flask import Blueprint, request, jsonify
import os
import time
import jwt
from datetime import datetime, timedelta

livekit_bp = Blueprint('livekit', __name__)

# LiveKit configuration
LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY', '')
LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET', '')
LIVEKIT_URL = os.getenv('LIVEKIT_URL', 'wss://your-livekit-server.livekit.cloud')

# Expert database
EXPERTS = [
    {
        'id': 'expert_1',
        'name': 'Dr. Rajesh Kumar',
        'specialization': 'Crop Science & Yield Optimization',
        'experience': '15 years',
        'rating': 4.8,
        'languages': ['Hindi', 'English'],
        'available': True,
        'price_per_min': 5
    },
    {
        'id': 'expert_2',
        'name': 'Dr. Priya Sharma',
        'specialization': 'Soil Health & Fertilizer Management',
        'experience': '12 years',
        'rating': 4.9,
        'languages': ['Hindi', 'English', 'Punjabi'],
        'available': True,
        'price_per_min': 6
    },
    {
        'id': 'expert_3',
        'name': 'Dr. Amit Patel',
        'specialization': 'Irrigation & Water Management',
        'experience': '10 years',
        'rating': 4.7,
        'languages': ['Hindi', 'English', 'Gujarati'],
        'available': False,
        'price_per_min': 5
    },
    {
        'id': 'expert_4',
        'name': 'Dr. Sunita Devi',
        'specialization': 'Organic Farming & Pest Control',
        'experience': '18 years',
        'rating': 4.9,
        'languages': ['Hindi', 'English', 'Tamil'],
        'available': True,
        'price_per_min': 7
    },
    {
        'id': 'expert_5',
        'name': 'Dr. Vikram Singh',
        'specialization': 'Market Analysis & Crop Planning',
        'experience': '20 years',
        'rating': 4.6,
        'languages': ['Hindi', 'English'],
        'available': True,
        'price_per_min': 8
    }
]


def generate_livekit_token(room_name, participant_name, is_publisher=True):
    """Generate LiveKit access token"""
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        return None, "LiveKit credentials not configured"
    
    try:
        # Token payload
        now = datetime.utcnow()
        exp = now + timedelta(hours=2)
        
        payload = {
            'iss': LIVEKIT_API_KEY,
            'sub': participant_name,
            'nbf': int(now.timestamp()),
            'exp': int(exp.timestamp()),
            'video': {
                'room': room_name,
                'roomJoin': True,
                'canPublish': is_publisher,
                'canSubscribe': True,
                'canPublishData': True
            },
            'name': participant_name
        }
        
        token = jwt.encode(payload, LIVEKIT_API_SECRET, algorithm='HS256')
        return token, None
        
    except Exception as e:
        return None, str(e)


@livekit_bp.route('/token', methods=['POST'])
def get_token():
    """Generate LiveKit token for joining a room"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Request data required'}), 400
    
    room_name = data.get('room_name')
    participant_name = data.get('participant_name')
    
    if not room_name or not participant_name:
        return jsonify({'success': False, 'error': 'Room name and participant name required'}), 400
    
    token, error = generate_livekit_token(room_name, participant_name)
    
    if error:
        return jsonify({'success': False, 'error': error}), 500
    
    return jsonify({
        'success': True,
        'token': token,
        'room_name': room_name,
        'livekit_url': LIVEKIT_URL
    }), 200


@livekit_bp.route('/experts', methods=['GET'])
def get_experts():
    """Get list of available experts"""
    available_only = request.args.get('available', 'false').lower() == 'true'
    specialization = request.args.get('specialization')
    
    filtered_experts = EXPERTS
    
    if available_only:
        filtered_experts = [e for e in filtered_experts if e['available']]
    
    if specialization:
        filtered_experts = [e for e in filtered_experts if specialization.lower() in e['specialization'].lower()]
    
    return jsonify({
        'success': True,
        'experts': filtered_experts,
        'total': len(filtered_experts)
    }), 200


@livekit_bp.route('/create-room', methods=['POST'])
def create_room():
    """Create a new consultation room"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Request data required'}), 400
    
    expert_id = data.get('expert_id')
    user_name = data.get('user_name', 'Farmer')
    call_type = data.get('call_type', 'video')  # video or audio
    
    if not expert_id:
        return jsonify({'success': False, 'error': 'Expert ID required'}), 400
    
    # Find expert
    expert = next((e for e in EXPERTS if e['id'] == expert_id), None)
    
    if not expert:
        return jsonify({'success': False, 'error': 'Expert not found'}), 404
    
    if not expert['available']:
        return jsonify({'success': False, 'error': 'Expert is not available'}), 400
    
    # Generate unique room name
    room_name = f"consult_{expert_id}_{int(time.time())}"
    
    # Generate tokens for both participants
    user_token, user_error = generate_livekit_token(room_name, user_name, is_publisher=True)
    expert_token, expert_error = generate_livekit_token(room_name, expert['name'], is_publisher=True)
    
    if user_error or expert_error:
        # Fallback without real tokens for demo
        user_token = f"demo_token_{room_name}_{user_name}"
        expert_token = f"demo_token_{room_name}_{expert['name']}"
    
    return jsonify({
        'success': True,
        'room': {
            'name': room_name,
            'call_type': call_type,
            'livekit_url': LIVEKIT_URL
        },
        'user_token': user_token,
        'expert': {
            'id': expert['id'],
            'name': expert['name'],
            'specialization': expert['specialization']
        },
        'pricing': {
            'rate_per_min': expert['price_per_min'],
            'currency': 'INR'
        }
    }), 200


@livekit_bp.route('/end-call', methods=['POST'])
def end_call():
    """End a consultation call and calculate billing"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Request data required'}), 400
    
    room_name = data.get('room_name')
    duration_seconds = data.get('duration', 0)
    expert_id = data.get('expert_id')
    rating = data.get('rating')
    notes = data.get('notes')
    
    # Find expert for pricing
    expert = next((e for e in EXPERTS if e['id'] == expert_id), None)
    rate_per_min = expert['price_per_min'] if expert else 5
    
    # Calculate billing
    duration_minutes = max(1, duration_seconds // 60)  # Minimum 1 minute
    total_cost = duration_minutes * rate_per_min
    
    return jsonify({
        'success': True,
        'summary': {
            'room_name': room_name,
            'duration_seconds': duration_seconds,
            'duration_minutes': duration_minutes,
            'rate_per_min': rate_per_min,
            'total_cost': total_cost,
            'currency': 'INR',
            'rating': rating,
            'notes': notes
        }
    }), 200


@livekit_bp.route('/schedule', methods=['POST'])
def schedule_call():
    """Schedule a future consultation"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Request data required'}), 400
    
    expert_id = data.get('expert_id')
    scheduled_time = data.get('scheduled_time')  # ISO format
    user_name = data.get('user_name')
    topic = data.get('topic')
    
    if not all([expert_id, scheduled_time, user_name]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Find expert
    expert = next((e for e in EXPERTS if e['id'] == expert_id), None)
    
    if not expert:
        return jsonify({'success': False, 'error': 'Expert not found'}), 404
    
    # Generate booking ID
    booking_id = f"booking_{int(time.time())}"
    
    return jsonify({
        'success': True,
        'booking': {
            'id': booking_id,
            'expert': {
                'id': expert['id'],
                'name': expert['name'],
                'specialization': expert['specialization']
            },
            'scheduled_time': scheduled_time,
            'topic': topic,
            'status': 'confirmed',
            'meeting_link': f"/call/{booking_id}"
        }
    }), 200

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# In-memory user storage (replace with database in production)
users_db = {}

SECRET_KEY = os.getenv('SECRET_KEY', 'crop-yield-secret-key-2025')


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'success': False, 'error': 'Token is missing'}), 401
        
        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = users_db.get(data['user_id'])
            
            if not current_user:
                return jsonify({'success': False, 'error': 'User not found'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Request data required'}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    state = data.get('state')
    district = data.get('district')
    farm_size = data.get('farm_size')
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'error': 'Username, email and password required'}), 400
    
    # Check if user exists
    if any(u['email'] == email for u in users_db.values()):
        return jsonify({'success': False, 'error': 'Email already registered'}), 400
    
    if any(u['username'] == username for u in users_db.values()):
        return jsonify({'success': False, 'error': 'Username already taken'}), 400
    
    # Create user
    user_id = f"user_{len(users_db) + 1}"
    users_db[user_id] = {
        'id': user_id,
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'phone': phone,
        'state': state,
        'district': district,
        'farm_size': farm_size,
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Generate token
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, SECRET_KEY, algorithm='HS256')
    
    return jsonify({
        'success': True,
        'message': 'Registration successful',
        'token': token,
        'user': {
            'id': user_id,
            'username': username,
            'email': email,
            'state': state,
            'district': district
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Request data required'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({'success': False, 'error': 'Email and password required'}), 400
    
    # Find user
    user = None
    user_id = None
    for uid, u in users_db.items():
        if u['email'] == email:
            user = u
            user_id = uid
            break
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    # Generate token
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, SECRET_KEY, algorithm='HS256')
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user_id,
            'username': user['username'],
            'email': user['email'],
            'state': user.get('state'),
            'district': user.get('district'),
            'farm_size': user.get('farm_size')
        }
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get user profile"""
    return jsonify({
        'success': True,
        'user': {
            'id': current_user['id'],
            'username': current_user['username'],
            'email': current_user['email'],
            'phone': current_user.get('phone'),
            'state': current_user.get('state'),
            'district': current_user.get('district'),
            'farm_size': current_user.get('farm_size'),
            'created_at': current_user.get('created_at')
        }
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Update user profile"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Request data required'}), 400
    
    # Update allowed fields
    allowed_fields = ['phone', 'state', 'district', 'farm_size']
    for field in allowed_fields:
        if field in data:
            current_user[field] = data[field]
    
    return jsonify({
        'success': True,
        'message': 'Profile updated',
        'user': {
            'id': current_user['id'],
            'username': current_user['username'],
            'email': current_user['email'],
            'phone': current_user.get('phone'),
            'state': current_user.get('state'),
            'district': current_user.get('district'),
            'farm_size': current_user.get('farm_size')
        }
    }), 200

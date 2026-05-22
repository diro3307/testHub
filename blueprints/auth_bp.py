"""
TestHUB QE Portal - Authentication Blueprint
Handles login, logout, user management, and site configuration
"""
import os
import json
import hashlib
import secrets
from datetime import datetime
from flask import Blueprint, request, session, jsonify, current_app
from models import db, UserManagement

bp = Blueprint('auth', __name__, url_prefix='/api')


def hash_password(password):
    """Hash password with salt: salt$hash format"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${password_hash}"


def verify_password(stored_hash, password):
    """Verify password against stored hash"""
    try:
        salt, password_hash = stored_hash.split('$')
        return password_hash == hashlib.sha256((salt + password).encode()).hexdigest()
    except:
        return False


def require_login(f):
    """Decorator to require authentication"""
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated


def require_admin(f):
    """Decorator to require admin role"""
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        user = UserManagement.query.filter_by(user_id=session['user_id']).first()
        if not user or user.assigned_role != 'testhub_admin':
            return jsonify({'success': False, 'message': 'Forbidden - Admin access required'}), 403
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated


@bp.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    user = UserManagement.query.filter_by(user_id=username).first()
    
    if not user or not verify_password(user.password_hash, password):
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    
    if user.account_status != 'active':
        return jsonify({'success': False, 'message': 'Account is inactive'}), 403
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Set session
    session.permanent = True
    session['user_id'] = user.user_id
    session['role'] = user.assigned_role
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user_id': user.user_id,
        'role': user.assigned_role
    })


@bp.route('/logout', methods=['POST'])
@require_login
def logout():
    """Logout endpoint"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})


@bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user = UserManagement.query.filter_by(user_id=session['user_id']).first()
    
    if not user:
        session.clear()
        return jsonify({'success': False, 'message': 'User not found'}), 401
    
    return jsonify({
        'success': True,
        'user_id': user.user_id,
        'role': user.assigned_role,
        'last_login': user.last_login.isoformat() if user.last_login else None
    })


# ========== USER MANAGEMENT ==========

@bp.route('/users', methods=['GET'])
@require_admin
def list_users():
    """List all users"""
    users = UserManagement.query.all()
    return jsonify({
        'success': True,
        'users': [
            {
                'id': u.id,
                'user_id': u.user_id,
                'assigned_role': u.assigned_role,
                'account_status': u.account_status,
                'last_login': u.last_login.isoformat() if u.last_login else None,
                'created_at': u.created_at.isoformat()
            }
            for u in users
        ]
    })


@bp.route('/users', methods=['POST'])
@require_admin
def create_user():
    """Create new user"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'testhub_QA')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    if UserManagement.query.filter_by(user_id=username).first():
        return jsonify({'success': False, 'message': 'User already exists'}), 409
    
    if role not in ['testhub_admin', 'testhub_QA', 'testhub_dashboard_user']:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400
    
    user = UserManagement(
        user_id=username,
        password_hash=hash_password(password),
        assigned_role=role,
        account_status='active'
    )
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'User {username} created',
        'user_id': user.user_id
    }), 201


@bp.route('/users/<int:user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    """Update user (password, role, status)"""
    user = UserManagement.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    data = request.get_json() or {}
    
    if 'password' in data and data['password']:
        user.password_hash = hash_password(data['password'])
    
    if 'role' in data and data['role'] in ['testhub_admin', 'testhub_QA', 'testhub_dashboard_user']:
        user.assigned_role = data['role']
    
    if 'account_status' in data and data['account_status'] in ['active', 'inactive']:
        user.account_status = data['account_status']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'User {user.user_id} updated'
    })


@bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """Delete user"""
    user = UserManagement.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    username = user.user_id
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'User {username} deleted'
    })


# ========== SITE CONFIGURATION ==========

@bp.route('/site-config', methods=['GET'])
def get_site_config():
    """Get site configuration"""
    config_file = 'site_config.json'
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            return jsonify({'success': True, 'config': config})
        except:
            pass
    
    # Return defaults
    defaults = {
        'session_idle_warn_minutes': 8,
        'session_idle_logout_minutes': 10,
        'announcement_enabled': False,
        'announcement_type': 'info',
        'announcement_message': '',
        'github_org': 'diro3307'
    }
    return jsonify({'success': True, 'config': defaults})


@bp.route('/site-config', methods=['POST'])
@require_admin
def update_site_config():
    """Update site configuration"""
    data = request.get_json() or {}
    config_file = 'site_config.json'
    
    # Validate
    warn_min = data.get('session_idle_warn_minutes', 8)
    logout_min = data.get('session_idle_logout_minutes', 10)
    
    if warn_min >= logout_min:
        return jsonify({
            'success': False,
            'message': 'Warning timeout must be less than logout timeout'
        }), 400
    
    announcement_msg = data.get('announcement_message', '')
    if len(announcement_msg) > 500:
        return jsonify({
            'success': False,
            'message': 'Announcement message max 500 characters'
        }), 400
    
    config = {
        'session_idle_warn_minutes': warn_min,
        'session_idle_logout_minutes': logout_min,
        'announcement_enabled': data.get('announcement_enabled', False),
        'announcement_type': data.get('announcement_type', 'info'),
        'announcement_message': announcement_msg,
        'github_org': data.get('github_org', 'diro3307')
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return jsonify({'success': True, 'message': 'Configuration updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

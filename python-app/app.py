#!/usr/bin/env python3
"""
NeerOps v9 Test Application - Python Flask REST API
Simple microservice for testing CI/CD pipeline
"""

import os
import json
import logging
import time
from datetime import datetime
from flask import Flask, jsonify, request
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Metrics
metrics = {
    'requests_total': 0,
    'requests_success': 0,
    'requests_error': 0,
    'avg_response_time': 0,
    'response_times': []
}

# Sample data
users_db = [
    {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
    {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'},
    {'id': 3, 'name': 'Charlie', 'email': 'charlie@example.com'},
]


def track_metrics(f):
    """Decorator to track request metrics"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        metrics['requests_total'] += 1
        
        try:
            result = f(*args, **kwargs)
            metrics['requests_success'] += 1
            return result
        except Exception as e:
            metrics['requests_error'] += 1
            raise e
        finally:
            elapsed = (time.time() - start_time) * 1000  # ms
            metrics['response_times'].append(elapsed)
            
            # Keep last 100 response times for avg calculation
            if len(metrics['response_times']) > 100:
                metrics['response_times'] = metrics['response_times'][-100:]
            
            if metrics['response_times']:
                metrics['avg_response_time'] = sum(metrics['response_times']) / len(metrics['response_times'])
            
            logger.info(f"{f.__name__} completed in {elapsed:.2f}ms")
    
    return decorated_function


@app.route('/', methods=['GET'])
@track_metrics
def index():
    """Root endpoint - HTML page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NeerOps v9 Python Test App</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .endpoint { margin: 10px 0; padding: 10px; background: #f0f0f0; }
            code { background: #e0e0e0; padding: 2px 5px; }
        </style>
    </head>
    <body>
        <h1>🐍 NeerOps v9 Python Test Application</h1>
        <p>Simple Flask REST API for validating CI/CD pipeline</p>
        
        <h2>Available Endpoints:</h2>
        <div class="endpoint">
            <p><strong>GET /health</strong> - Health check</p>
            <code>curl http://localhost:5000/health</code>
        </div>
        
        <div class="endpoint">
            <p><strong>GET /ready</strong> - Readiness check</p>
            <code>curl http://localhost:5000/ready</code>
        </div>
        
        <div class="endpoint">
            <p><strong>GET /metrics</strong> - Application metrics</p>
            <code>curl http://localhost:5000/metrics</code>
        </div>
        
        <div class="endpoint">
            <p><strong>GET /api/users</strong> - List all users</p>
            <code>curl http://localhost:5000/api/users</code>
        </div>
        
        <div class="endpoint">
            <p><strong>GET /api/users/&lt;id&gt;</strong> - Get user by ID</p>
            <code>curl http://localhost:5000/api/users/1</code>
        </div>
        
        <div class="endpoint">
            <p><strong>POST /api/users</strong> - Create new user</p>
            <code>curl -X POST http://localhost:5000/api/users -H "Content-Type: application/json" -d '{"name":"Dave","email":"dave@example.com"}'</code>
        </div>
        
        <h2>Monitoring:</h2>
        <p>Application logs and metrics are available for review.</p>
        <p>Test pipeline validates: security gates, docker build, canary metrics, and manual approval flow.</p>
        
        <footer style="margin-top: 40px; border-top: 1px solid #ccc; padding-top: 20px; color: #666;">
            <p>NeerOps v9 Test Application | Version 1.0 | Python Flask</p>
        </footer>
    </body>
    </html>
    """
    return html, 200, {'Content-Type': 'text/html'}


@app.route('/health', methods=['GET'])
@track_metrics
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime': 'running'
    }), 200


@app.route('/ready', methods=['GET'])
@track_metrics
def readiness():
    """Readiness check endpoint"""
    return jsonify({
        'ready': True,
        'version': '1.0',
        'service': 'neerops-python-app'
    }), 200


@app.route('/metrics', methods=['GET'])
@track_metrics
def get_metrics():
    """Get application metrics"""
    error_rate = 0
    if metrics['requests_total'] > 0:
        error_rate = (metrics['requests_error'] / metrics['requests_total']) * 100
    
    return jsonify({
        'application': 'neerops-python-app',
        'version': '1.0',
        'timestamp': datetime.utcnow().isoformat(),
        'metrics': {
            'requests': {
                'total': metrics['requests_total'],
                'successful': metrics['requests_success'],
                'errors': metrics['requests_error'],
                'error_rate_percent': round(error_rate, 2)
            },
            'response_time': {
                'avg_ms': round(metrics['avg_response_time'], 2),
                'samples': len(metrics['response_times'])
            },
            'performance': {
                'requests_per_minute': round(metrics['requests_total'] / (time.time() / 60), 2) if time.time() > 60 else 0
            }
        }
    }), 200


@app.route('/api/users', methods=['GET', 'POST'])
@track_metrics
def users():
    """Get all users or create new user"""
    if request.method == 'GET':
        return jsonify(users_db), 200
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            if not data or 'name' not in data or 'email' not in data:
                return jsonify({'error': 'Missing required fields: name, email'}), 400
            
            new_user = {
                'id': max([u['id'] for u in users_db]) + 1 if users_db else 1,
                'name': data['name'],
                'email': data['email']
            }
            users_db.append(new_user)
            logger.info(f"Created new user: {new_user}")
            
            return jsonify(new_user), 201
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return jsonify({'error': str(e)}), 400


@app.route('/api/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@track_metrics
def user_detail(user_id):
    """Get, update, or delete specific user"""
    user = next((u for u in users_db if u['id'] == user_id), None)
    
    if not user:
        return jsonify({'error': f'User {user_id} not found'}), 404
    
    if request.method == 'GET':
        return jsonify(user), 200
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            if 'name' in data:
                user['name'] = data['name']
            if 'email' in data:
                user['email'] = data['email']
            logger.info(f"Updated user {user_id}: {user}")
            return jsonify(user), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    elif request.method == 'DELETE':
        users_db.remove(user)
        logger.info(f"Deleted user {user_id}")
        return jsonify({'message': f'User {user_id} deleted'}), 200


@app.route('/api/status', methods=['GET'])
@track_metrics
def status():
    """Application status endpoint"""
    return jsonify({
        'service': 'neerops-python-app',
        'version': '1.0',
        'status': 'running',
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'timestamp': datetime.utcnow().isoformat(),
        'users_count': len(users_db)
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting NeerOps Python Flask application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

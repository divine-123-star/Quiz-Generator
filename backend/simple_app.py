

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os

# Create Flask app directly (like your original)
app = Flask(__name__, template_folder='../app/templates', static_folder='../app/static')

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = '../uploads'

# Simple routes (like your original style)
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/test')
def test():
    """Test route to verify Flask is working"""
    return '''
    <h1>✅ Flask is Working!</h1>
    <p><a href="/">Home</a></p>
    <p><a href="/login">Login</a></p>
    <p><a href="/register">Register</a></p>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'GET':
        return render_template('login.html')
    return jsonify({'message': 'Login functionality coming soon!'})

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if request.method == 'GET':
        return render_template('register.html')
    return jsonify({'message': 'Registration functionality coming soon!'})

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html')

@app.route('/create-quiz', methods=['GET', 'POST'])
def create_quiz():
    """Create quiz page"""
    if request.method == 'GET':
        return render_template('create-quiz.html')
    return jsonify({'message': 'Quiz creation functionality coming soon!'})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return '<h1>404 - Page Not Found</h1><p><a href="/">Go Home</a></p>', 404

if __name__ == '__main__':
    print("🚀 Simple AI Quiz Generator Starting!")
    print("📍 Server: http://localhost:5000")
    print("✅ Open your browser and navigate to the URL above!")
    app.run(host='0.0.0.0', port=5000, debug=True)
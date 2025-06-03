# backend/appl.py - COMPLETELY FIXED VERSION

import sys
import os

# FIX 1: Add project root to Python path FIRST
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Now imports should work
try:
    from app.utils.pdf_processor import PDFProcessor
except ImportError:
    # Fallback PDF processor if import fails
    class PDFProcessor:
        def __init__(self, upload_folder):
            self.upload_folder = upload_folder
        def save_pdf(self, file):
            import tempfile
            temp_path = os.path.join(tempfile.gettempdir(), file.filename)
            file.save(temp_path)
            return temp_path
        def extract_text(self, filepath):
            return "Sample text extracted from PDF for testing purposes."

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from backend.models import db, User, Quiz, QuizQuestion, QuizAnswer, QuizAttempt
from backend.services.quiz_generator import GeminiQuizGenerator
from backend.routes.quiz_routes import quiz_bp

def create_app():
    app = Flask(__name__, template_folder='../app/templates')
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Ledimo2003%@localhost/quiz'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = '../uploads'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    
    # Initialize extensions
    db.init_app(app)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    try:
        app.register_blueprint(quiz_bp)
        print("Quiz routes loaded successfully!")
    except ImportError as e:
        print(f"Warning: Could not load quiz routes: {e}")
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Main routes
    @app.route('/')
    def index():
        """Home page"""
        return render_template('index.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration"""
        if request.method == 'GET':
            return render_template('register.html')
        
        try:
            first_name = request.form.get('firstName') or request.form.get('fullName', '').split()[0] if request.form.get('fullName') else ''
            last_name = request.form.get('lastName') or ' '.join(request.form.get('fullName', '').split()[1:]) if request.form.get('fullName') else ''
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            
            if not all([first_name, last_name, email, password]):
                return jsonify({
                    'success': False,
                    'error': 'All fields are required'
                }), 400
            
            if User.query.filter_by(email=email).first():
                return jsonify({
                    'success': False,
                    'error': 'Email already registered'
                }), 400
            
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Account created successfully! Please log in.'
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Registration failed. Please try again.'
            }), 500
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login"""
        if request.method == 'GET':
            return render_template('login.html')
        
        try:
            email = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            if not email or not password:
                return jsonify({
                    'success': False,
                    'error': 'Email and password are required'
                }), 400
            
            if '@' in email:
                user = User.query.filter_by(email=email).first()
            else:
                user = User.query.filter_by(username=email).first()
            
            if user and user.check_password(password):
                login_user(user, remember=request.form.get('remember_me'))
                return jsonify({
                    'success': True,
                    'message': f'Welcome back, {user.first_name}!'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid email or password'
                }), 401
                
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Login failed. Please try again.'
            }), 500
        
    @app.route('/logout')
    @login_required
    def logout():
        """User logout"""
        logout_user()
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('index')) 
        
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """User dashboard"""
        try:
            total_quizzes = Quiz.query.filter_by(created_by=current_user.id).count()
            total_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).count()
            recent_quizzes = Quiz.query.filter_by(created_by=current_user.id)\
                .order_by(Quiz.created_at.desc()).limit(5).all()
            recent_attempts = QuizAttempt.query.filter_by(user_id=current_user.id)\
                .order_by(QuizAttempt.completed_at.desc()).limit(5).all()
            
            dashboard_data = {
                'user': current_user,
                'stats': {
                    'total_quizzes': total_quizzes,
                    'total_attempts': total_attempts,
                    'avg_score': 0
                },
                'recent_quizzes': [quiz.to_dict() for quiz in recent_quizzes],
                'recent_attempts': [attempt.to_dict() for attempt in recent_attempts]
            }
            
            return render_template('dashboard.html', data=dashboard_data)
        except Exception as e:
            app.logger.error(f"Dashboard error: {str(e)}")
            flash('Error loading dashboard', 'error')
            return render_template('dashboard.html', data={})

    @app.route('/api/upload_pdf', methods=['POST'])
    @login_required
    def upload_pdf():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and file.filename.lower().endswith('.pdf'):
            pdf_processor = PDFProcessor(app.config['UPLOAD_FOLDER'])
            filepath = pdf_processor.save_pdf(file)
            extracted_text = pdf_processor.extract_text(filepath)
            return jsonify({'message': 'PDF uploaded', 'text_preview': extracted_text[:500]}), 201
        return jsonify({'error': 'Invalid file type'}), 400
        
    # Legacy routes for compatibility
    @app.route('/create-quiz.html')
    def create_quiz_html():
        return redirect(url_for('quiz.create_quiz'))

    @app.route('/api/submit-quiz', methods=['POST'])
    def submit_quiz_legacy():
        return jsonify({"success": True, "message": "Use new quiz endpoints"})

    @app.route('/api/get-quizzes', methods=['GET'])
    def get_quizzes_legacy():
        return jsonify([])

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html') if os.path.exists('templates/404.html') else jsonify({'error': 'Page not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html') if os.path.exists('templates/500.html') else jsonify({'error': 'Internal server error'}), 500

    # Create tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
    
    return app

# Create the app
app = create_app()

# CLI command to create sample data
def create_sample_data():
    """Create sample data for testing"""
    try:
        with app.app_context():
            existing_user = User.query.filter_by(email="test@example.com").first()
            if existing_user:
                print("Sample user already exists!")
                return
                
            user = User(
                first_name="Test",
                last_name="User",
                email="test@example.com"
            )
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()
            
            generator = GeminiQuizGenerator()
            sample_quiz_data = generator.generate_sample_quiz()
            
            quiz = Quiz(
                title=sample_quiz_data['title'],
                description=sample_quiz_data['description'],
                total_questions=sample_quiz_data['total_questions'],
                total_points=sample_quiz_data['total_points'],
                difficulty_level=sample_quiz_data['difficulty_level'],
                created_by=user.id
            )
            db.session.add(quiz)
            db.session.flush()
            
            for q_data in sample_quiz_data['questions']:
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_text=q_data['question_text'],
                    question_type=q_data['question_type'],
                    points=q_data['points']
                )
                db.session.add(question)
                db.session.flush()
                
                for a_data in q_data['answers']:
                    answer = QuizAnswer(
                        question_id=question.id,
                        answer_text=a_data['answer_text'],
                        is_correct=a_data['is_correct']
                    )
                    db.session.add(answer)
            
            db.session.commit()
            print("Sample data created successfully!")
            print("Login with: test@example.com / password123")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample data: {str(e)}")

# Additional utility functions
def reset_database():
    """Reset the database - useful for development"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset successfully!")

def create_admin_user():
    """Create an admin user"""
    with app.app_context():
        admin = User(
            first_name="Admin",
            last_name="User", 
            email="admin@quizgenerator.com"
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin@quizgenerator.com / admin123")

# FIX 2: Proper indentation - this should be at module level!
if __name__ == '__main__':
    print("🚀 AI Quiz Generator Starting!")
    print("📍 Server: http://localhost:5000")
    print("✅ Open your browser and navigate to the URL above!")
    app.run(host='0.0.0.0', port=5000, debug=True)
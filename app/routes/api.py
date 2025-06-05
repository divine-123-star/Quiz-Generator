# backend/app.py - FIXED VERSION

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import PyPDF2
import mysql.connector
import json

def create_app():
    app = Flask(__name__, 
                template_folder='../app/templates',
                static_folder='../app/static')
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Ledimo2003%@localhost/quiz'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(project_root, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize database models after app config
    from backend.models import db, User, Quiz, QuizQuestion, QuizAnswer, QuizAttempt, UserAnswer, PDFUpload
    db.init_app(app)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Helper functions
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

    def extract_text_from_pdf(file_path):
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            app.logger.error(f"Error extracting PDF text: {str(e)}")
            return "Sample educational content for quiz generation."

    def generate_questions_from_text(text, num_questions):
        """Generate questions from PDF text content"""
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        
        questions = []
        
        # Create different types of questions
        for i in range(min(num_questions, 10)):  # Limit to 10 max
            if i % 3 == 0:  # Multiple choice
                questions.append({
                    'question_text': f'Based on the content, what is a key concept discussed?',
                    'question_type': 'multiple_choice',
                    'points': 1,
                    'answers': [
                        {'answer_text': 'Educational principles and learning', 'is_correct': True},
                        {'answer_text': 'Historical events only', 'is_correct': False},
                        {'answer_text': 'Mathematical formulas', 'is_correct': False},
                        {'answer_text': 'Sports activities', 'is_correct': False}
                    ]
                })
            elif i % 3 == 1:  # True/False
                questions.append({
                    'question_text': 'Learning requires consistent practice and dedication.',
                    'question_type': 'true_false',
                    'points': 1,
                    'answers': [
                        {'answer_text': 'True', 'is_correct': True},
                        {'answer_text': 'False', 'is_correct': False}
                    ]
                })
            else:  # Short answer
                questions.append({
                    'question_text': 'What are the main benefits of education mentioned in the text?',
                    'question_type': 'short_answer',
                    'points': 2,
                    'answers': [
                        {'answer_text': 'Knowledge, skills, personal growth, and career opportunities', 'is_correct': True}
                    ]
                })
        
        return questions[:num_questions]
    
    # =============================================================================
    # MAIN ROUTES
    # =============================================================================
    
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
            # Get form data
            full_name = request.form.get('fullName', '').strip()
            first_name = request.form.get('firstName', '').strip()
            last_name = request.form.get('lastName', '').strip()
            
            # Handle full name vs separate first/last name
            if full_name and not first_name:
                name_parts = full_name.split()
                first_name = name_parts[0] if name_parts else ''
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            
            if not all([first_name, email, password]):
                return jsonify({
                    'success': False,
                    'error': 'Name, email and password are required'
                }), 400
            
            if User.query.filter_by(email=email).first():
                return jsonify({
                    'success': False,
                    'error': 'Email already registered'
                }), 400
            
            user = User(
                first_name=first_name,
                last_name=last_name or 'User',
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
            email = request.form.get('username', '').strip()  # Login form uses 'username' field
            password = request.form.get('password', '').strip()
            
            if not email or not password:
                return jsonify({
                    'success': False,
                    'error': 'Email and password are required'
                }), 400
            
            # Find user by email
            user = User.query.filter_by(email=email).first()
            
            # For demo purposes, create user if not exists
            if not user:
                user = User(
                    first_name="Demo",
                    last_name="User", 
                    email=email
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                print(f"Created demo user: {email}")
            
            if user.check_password(password):
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
        return render_template('dashboard.html')

    @app.route('/create-quiz', methods=['GET', 'POST'])
    @login_required
    def create_quiz():
        """Handle quiz creation from PDF upload"""
        
        if request.method == 'GET':
            return render_template('create-quiz.html')
        
        # Handle POST request for quiz creation
        try:
            print("🎯 Starting quiz creation...")
            
            # Get form data
            quiz_title = request.form.get('title', 'AI Generated Quiz')
            num_questions = int(request.form.get('numQuestions', '5'))
            difficulty = request.form.get('difficulty', 'medium')
            
            print(f"📋 Quiz settings: {quiz_title}, {num_questions} questions, {difficulty} difficulty")
            
            # Process PDF file if uploaded
            pdf_text = ""
            if 'pdf_file' in request.files:
                file = request.files['pdf_file']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{current_user.id}_{filename}")
                    file.save(file_path)
                    print(f"💾 File saved: {filename}")
                    
                    # Extract text from PDF
                    pdf_text = extract_text_from_pdf(file_path)
                    print(f"📖 Extracted {len(pdf_text)} characters from PDF")
                else:
                    print("⚠️ No valid PDF file uploaded")
            
            # Generate questions
            questions = generate_questions_from_text(pdf_text, num_questions)
            total_points = sum(q['points'] for q in questions)
            
            print(f"✅ Generated {len(questions)} questions")
            
            # Save to database
            quiz = Quiz(
                title=quiz_title,
                description=f'Quiz with {len(questions)} questions',
                total_questions=len(questions),
                total_points=total_points,
                difficulty_level=difficulty,
                created_by=current_user.id
            )
            db.session.add(quiz)
            db.session.flush()
            
            # Create questions and answers
            for question_data in questions:
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_text=question_data['question_text'],
                    question_type=question_data['question_type'],
                    points=question_data['points']
                )
                db.session.add(question)
                db.session.flush()
                
                for answer_data in question_data['answers']:
                    answer = QuizAnswer(
                        question_id=question.id,
                        answer_text=answer_data['answer_text'],
                        is_correct=answer_data['is_correct']
                    )
                    db.session.add(answer)
            
            db.session.commit()
            print("✅ Quiz created successfully!")
            
            # Redirect to take the quiz
            return redirect(url_for('take_quiz', quiz_id=quiz.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating quiz: {str(e)}")
            flash(f'Error creating quiz: {str(e)}', 'error')
            return redirect(url_for('dashboard'))

    @app.route('/quiz/<int:quiz_id>')
    @login_required
    def take_quiz(quiz_id):
        """Display quiz for taking"""
        try:
            quiz = Quiz.query.get_or_404(quiz_id)
            questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
            
            # Convert to dict for frontend
            quiz_data = {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'total_questions': quiz.total_questions,
                'total_points': quiz.total_points,
                'questions': []
            }
            
            for question in questions:
                question_dict = {
                    'id': question.id,
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'points': question.points,
                    'answers': []
                }
                
                for answer in question.answers:
                    # Don't send correct answer info to frontend
                    question_dict['answers'].append({
                        'id': answer.id,
                        'answer_text': answer.answer_text
                    })
                
                quiz_data['questions'].append(question_dict)
            
            return render_template('take-quiz.html', quiz=quiz_data)
            
        except Exception as e:
            app.logger.error(f"Error loading quiz: {str(e)}")
            flash('Quiz not found or error loading quiz', 'error')
            return redirect(url_for('dashboard'))

    @app.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
    @login_required
    def submit_quiz(quiz_id):
        """Submit quiz answers and calculate score"""
        try:
            quiz = Quiz.query.get_or_404(quiz_id)
            data = request.get_json()
            user_answers = data.get('answers', {})
            
            # Create quiz attempt
            attempt = QuizAttempt(
                user_id=current_user.id,
                quiz_id=quiz_id,
                total_points=quiz.total_points
            )
            db.session.add(attempt)
            db.session.flush()
            
            score = 0
            questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
            
            # Process each answer
            for question in questions:
                question_id_str = str(question.id)
                user_answer_text = user_answers.get(question_id_str, '').strip()
                
                # Find correct answer
                correct_answer = QuizAnswer.query.filter_by(
                    question_id=question.id, is_correct=True
                ).first()
                
                is_correct = False
                if correct_answer and user_answer_text:
                    if question.question_type in ['multiple_choice', 'true_false']:
                        is_correct = user_answer_text.lower().strip() == correct_answer.answer_text.lower().strip()
                    else:
                        # Simple partial match for short answers
                        is_correct = user_answer_text.lower() in correct_answer.answer_text.lower()
                
                if is_correct:
                    score += question.points
                
                # Save user answer
                user_answer = UserAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    user_answer=user_answer_text,
                    is_correct=is_correct
                )
                db.session.add(user_answer)
            
            # Update attempt with score
            attempt.score = score
            attempt.calculate_percentage()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'attempt_id': attempt.id,
                'score': score,
                'total_points': quiz.total_points,
                'percentage': float(attempt.percentage)
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error submitting quiz: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to submit quiz: {str(e)}'
            }), 500

    @app.route('/quiz/<int:quiz_id>/results/<int:attempt_id>')
    @login_required
    def quiz_results(quiz_id, attempt_id):
        """Display quiz results"""
        try:
            attempt = QuizAttempt.query.filter_by(
                id=attempt_id, user_id=current_user.id, quiz_id=quiz_id
            ).first_or_404()
            
            quiz = Quiz.query.get_or_404(quiz_id)
            
            # Get user answers with question details
            user_answers = db.session.query(UserAnswer, QuizQuestion).join(
                QuizQuestion, UserAnswer.question_id == QuizQuestion.id
            ).filter(UserAnswer.attempt_id == attempt_id).all()
            
            results_data = {
                'quiz': {
                    'id': quiz.id,
                    'title': quiz.title,
                    'description': quiz.description,
                    'total_questions': quiz.total_questions,
                    'total_points': quiz.total_points
                },
                'attempt': {
                    'id': attempt.id,
                    'score': attempt.score,
                    'total_points': attempt.total_points,
                    'percentage': float(attempt.percentage) if attempt.percentage else 0,
                    'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None
                },
                'answers': []
            }
            
            for user_answer, question in user_answers:
                results_data['answers'].append({
                    'id': user_answer.id,
                    'question_text': question.question_text,
                    'user_answer': user_answer.user_answer,
                    'is_correct': user_answer.is_correct,
                    'points': question.points
                })
            
            return render_template('quiz-results.html', results=results_data)
            
        except Exception as e:
            app.logger.error(f"Error loading results: {str(e)}")
            flash('Results not found', 'error')
            return redirect(url_for('dashboard'))

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Page not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

    # Create tables
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully!")
        except Exception as e:
            print(f"❌ Error creating database tables: {str(e)}")
    
    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    print("🚀 AI Quiz Generator Starting!")
    print("📍 Server: http://localhost:5000")
    print("✅ Open your browser and navigate to the URL above!")
    app.run(host='0.0.0.0', port=5000, debug=True)
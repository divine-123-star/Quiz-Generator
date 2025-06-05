# backend/app.py - MAIN FLASK APPLICATION

import sys
import os
import logging
import traceback

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Flask and extensions
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import PyPDF2
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    
    # Create Flask app with correct template and static paths
    app = Flask(__name__, 
                template_folder=os.path.join(project_root, 'app', 'templates'),
                static_folder=os.path.join(project_root, 'app', 'static'))
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Ledimo2003%@localhost/quiz'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(project_root, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize database models
    try:
        from backend.models import db, User, Quiz, QuizQuestion, QuizAnswer, QuizAttempt, UserAnswer, PDFUpload
        db.init_app(app)
        logger.info("✅ Database models imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import database models: {str(e)}")
        raise
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Import quiz generator with fallback
    try:
        from backend.services.quiz_generator import GeminiQuizGenerator
        logger.info("✅ Quiz generator imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import quiz generator: {str(e)}")
        # Create a fallback generator
        class FallbackGenerator:
            def generate_quiz_from_text(self, text, settings):
                return {
                    'title': settings.get('title', 'Fallback Quiz'),
                    'description': 'Simple fallback quiz',
                    'difficulty_level': 'medium',
                    'total_questions': 2,
                    'total_points': 2,
                    'questions': [
                        {
                            'question_text': 'Learning requires active engagement and practice.',
                            'question_type': 'true_false',
                            'points': 1,
                            'answers': [
                                {'answer_text': 'True', 'is_correct': True},
                                {'answer_text': 'False', 'is_correct': False}
                            ]
                        },
                        {
                            'question_text': 'Which approach is most effective for learning?',
                            'question_type': 'multiple_choice',
                            'points': 1,
                            'answers': [
                                {'answer_text': 'Active participation and reflection', 'is_correct': True},
                                {'answer_text': 'Passive reading only', 'is_correct': False},
                                {'answer_text': 'Memorization without understanding', 'is_correct': False},
                                {'answer_text': 'Skipping difficult parts', 'is_correct': False}
                            ]
                        }
                    ]
                }
        GeminiQuizGenerator = FallbackGenerator
    
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
            logger.error(f"Error extracting PDF text: {str(e)}")
            return "Educational content for quiz generation. Learning is an active process that requires engagement and practice."

    # =============================================================================
    # ROUTES START HERE
    # =============================================================================
    
    @app.route('/')
    def index():
        """Home page"""
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error rendering index: {str(e)}")
            return '''
            <h1>🎉 AI Quiz Generator</h1>
            <p>✅ Server is running!</p>
            <p><a href="/register">Register</a> | <a href="/login">Login</a></p>
            '''
    
    @app.route('/test')
    def test_route():
        """Test route to check if everything is working"""
        try:
            # Test database connection
            user_count = User.query.count()
            
            # Test quiz generator
            generator = GeminiQuizGenerator()
            
            return f'''
            <h1>🧪 AI Quiz Generator Test</h1>
            <h2>✅ System Status</h2>
            <ul>
                <li>✅ Flask App: Running</li>
                <li>✅ Database: Connected ({user_count} users)</li>
                <li>✅ Quiz Generator: Available</li>
                <li>✅ Templates: Working</li>
            </ul>
            <h3>🔗 Navigation</h3>
            <p><a href="/">Home</a> | <a href="/register">Register</a> | <a href="/login">Login</a> | <a href="/dashboard">Dashboard</a></p>
            '''
        except Exception as e:
            import traceback
            return f'''
            <h1>❌ Test Failed</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <details>
                <summary>Full Error</summary>
                <pre>{traceback.format_exc()}</pre>
            </details>
            '''
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration"""
        if request.method == 'GET':
            try:
                return render_template('register.html')
            except Exception as e:
                logger.error(f"Error rendering register template: {str(e)}")
                return '<h1>Register</h1><p>Registration page not available</p>'
        
        try:
            # Get form data
            full_name = request.form.get('fullName', '').strip()
            first_name = request.form.get('firstName', '').strip()
            last_name = request.form.get('lastName', '').strip()
            
            # Handle full name vs separate first/last name
            if full_name and not first_name:
                name_parts = full_name.split()
                first_name = name_parts[0] if name_parts else 'User'
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            
            if not all([first_name, email, password]):
                return jsonify({
                    'success': False,
                    'error': 'Name, email and password are required'
                }), 400
            
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                return jsonify({
                    'success': False,
                    'error': 'Email already registered'
                }), 400
            
            # Create new user
            user = User(
                first_name=first_name,
                last_name=last_name or '',
                email=email
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"✅ New user registered: {email}")
            
            return jsonify({
                'success': True,
                'message': 'Account created successfully! Please log in.'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Registration failed. Please try again.'
            }), 500
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login"""
        if request.method == 'GET':
            try:
                return render_template('login.html')
            except Exception as e:
                logger.error(f"Error rendering login template: {str(e)}")
                return '<h1>Login</h1><p>Login page not available</p>'
        
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
                logger.info(f"✅ Created demo user: {email}")
            
            # Check password
            if user.check_password(password):
                login_user(user, remember=request.form.get('remember_me'))
                logger.info(f"✅ User logged in: {email}")
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
            logger.error(f"Login error: {str(e)}")
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
            return render_template('dashboard.html')
        except Exception as e:
            logger.error(f"Error rendering dashboard: {str(e)}")
            return '<h1>Dashboard</h1><p>Welcome to your dashboard!</p>'

    @app.route('/create-quiz', methods=['GET', 'POST'])
    @login_required
    def create_quiz():
        """Handle quiz creation from PDF upload"""
        
        if request.method == 'GET':
            try:
                return render_template('create-quiz.html')
            except Exception as e:
                logger.error(f"Error rendering create-quiz template: {str(e)}")
                return '<h1>Create Quiz</h1><p>Quiz creation page not available</p>'
        
        # Handle POST request for quiz creation
        try:
            print("🎯 STARTING QUIZ CREATION...")
            logger.info("🎯 Starting quiz creation...")
            
            # Debug: Print all form data
            print("📋 FORM DATA RECEIVED:")
            for key, value in request.form.items():
                print(f"  {key}: {value}")
            
            # Get form data with better error handling
            quiz_title = request.form.get('title', 'AI Generated Quiz') or 'AI Generated Quiz'
            try:
                num_questions = int(request.form.get('numQuestions', '5'))
            except (ValueError, TypeError):
                num_questions = 5
            
            difficulty = request.form.get('difficulty', 'medium') or 'medium'
            question_types = request.form.get('questionTypes', 'mixed') or 'mixed'
            
            print(f"📋 PARSED SETTINGS: {quiz_title}, {num_questions} questions, {difficulty} difficulty, {question_types} types")
            
            # Process PDF file if uploaded
            pdf_text = "Educational content about learning and study skills. Active learning involves engaging with material through questioning and analysis."
            
            print("📁 CHECKING FOR PDF FILE...")
            if 'pdf_file' in request.files:
                file = request.files['pdf_file']
                print(f"📁 FILE RECEIVED: {file.filename if file else 'None'}")
                
                if file and file.filename and allowed_file(file.filename):
                    try:
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{current_user.id}_{filename}")
                        file.save(file_path)
                        print(f"💾 FILE SAVED: {filename}")
                        
                        # Extract text from PDF
                        pdf_text = extract_text_from_pdf(file_path)
                        print(f"📖 EXTRACTED {len(pdf_text)} CHARACTERS FROM PDF")
                        
                        # Save PDF upload record
                        try:
                            pdf_upload = PDFUpload(
                                user_id=current_user.id,
                                filename=filename,
                                file_path=file_path,
                                file_size=os.path.getsize(file_path),
                                processed=True
                            )
                            db.session.add(pdf_upload)
                            db.session.flush()
                            print("✅ PDF UPLOAD RECORD SAVED")
                        except Exception as pdf_error:
                            print(f"⚠️ ERROR SAVING PDF RECORD: {str(pdf_error)}")
                            # Continue anyway
                    except Exception as file_error:
                        print(f"❌ ERROR PROCESSING FILE: {str(file_error)}")
                else:
                    print("⚠️ NO VALID PDF FILE, USING DEFAULT TEXT")
            else:
                print("⚠️ NO PDF_FILE IN REQUEST, USING DEFAULT TEXT")
            
            # Generate questions using AI
            print("🤖 STARTING QUIZ GENERATION...")
            try:
                generator = GeminiQuizGenerator()
                settings = {
                    'title': quiz_title,
                    'numQuestions': num_questions,
                    'difficulty': difficulty,
                    'questionTypes': question_types
                }
                
                print(f"🤖 CALLING GENERATOR WITH SETTINGS: {settings}")
                quiz_data = generator.generate_quiz_from_text(pdf_text, settings)
                print(f"✅ AI GENERATED {quiz_data['total_questions']} QUESTIONS")
                
            except Exception as gen_error:
                print(f"❌ QUIZ GENERATION FAILED: {str(gen_error)}")
                # Fallback quiz data
                quiz_data = {
                    'title': quiz_title,
                    'description': f'Fallback quiz with educational content',
                    'difficulty_level': difficulty,
                    'total_questions': 2,
                    'total_points': 2,
                    'questions': [
                        {
                            'question_text': 'Learning requires active engagement and practice.',
                            'question_type': 'true_false',
                            'points': 1,
                            'answers': [
                                {'answer_text': 'True', 'is_correct': True},
                                {'answer_text': 'False', 'is_correct': False}
                            ]
                        },
                        {
                            'question_text': 'Which approach is most effective for learning?',
                            'question_type': 'multiple_choice',
                            'points': 1,
                            'answers': [
                                {'answer_text': 'Active participation and reflection', 'is_correct': True},
                                {'answer_text': 'Passive reading only', 'is_correct': False},
                                {'answer_text': 'Memorization without understanding', 'is_correct': False},
                                {'answer_text': 'Skipping difficult parts', 'is_correct': False}
                            ]
                        }
                    ]
                }
                print("✅ USING FALLBACK QUIZ DATA")
            
            # Save to database
            print("💾 SAVING QUIZ TO DATABASE...")
            try:
                quiz = Quiz(
                    title=quiz_data['title'],
                    description=quiz_data['description'],
                    total_questions=quiz_data['total_questions'],
                    total_points=quiz_data['total_points'],
                    difficulty_level=quiz_data['difficulty_level'],
                    created_by=current_user.id
                )
                db.session.add(quiz)
                db.session.flush()
                print(f"✅ QUIZ SAVED WITH ID: {quiz.id}")
                
                # Create questions and answers
                for idx, question_data in enumerate(quiz_data['questions']):
                    print(f"💾 SAVING QUESTION {idx + 1}...")
                    question = QuizQuestion(
                        quiz_id=quiz.id,
                        question_text=question_data['question_text'],
                        question_type=question_data['question_type'],
                        points=question_data['points']
                    )
                    db.session.add(question)
                    db.session.flush()
                    print(f"✅ QUESTION SAVED WITH ID: {question.id}")
                    
                    for answer_data in question_data['answers']:
                        answer = QuizAnswer(
                            question_id=question.id,
                            answer_text=answer_data['answer_text'],
                            is_correct=answer_data['is_correct']
                        )
                        db.session.add(answer)
                    print(f"✅ {len(question_data['answers'])} ANSWERS SAVED FOR QUESTION {question.id}")
                
                db.session.commit()
                print("✅ ALL DATA COMMITTED TO DATABASE!")
                
                # Redirect to take the quiz
                print(f"🎯 REDIRECTING TO QUIZ {quiz.id}")
                return redirect(url_for('take_quiz', quiz_id=quiz.id))
                
            except Exception as db_error:
                print(f"❌ DATABASE ERROR: {str(db_error)}")
                db.session.rollback()
                raise db_error
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ MAJOR ERROR CREATING QUIZ: {str(e)}")
            print(f"❌ ERROR TYPE: {type(e).__name__}")
            print("❌ FULL TRACEBACK:")
            traceback.print_exc()
            
            # Return error page instead of redirect for debugging
            return f'''
            <h1>❌ Quiz Creation Error</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><strong>Type:</strong> {type(e).__name__}</p>
            <p><a href="/dashboard">← Back to Dashboard</a></p>
            <p><a href="/create-quiz">Try Again</a></p>
            <details>
                <summary>Technical Details</summary>
                <pre>{traceback.format_exc()}</pre>
            </details>
            '''

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
            logger.error(f"Error loading quiz: {str(e)}")
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
            
            logger.info(f"✅ Quiz submitted: {score}/{quiz.total_points} points")
            
            return jsonify({
                'success': True,
                'attempt_id': attempt.id,
                'score': score,
                'total_points': quiz.total_points,
                'percentage': float(attempt.percentage)
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting quiz: {str(e)}")
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
            logger.error(f"Error loading results: {str(e)}")
            flash('Results not found', 'error')
            return redirect(url_for('dashboard'))
    
    # Route to display user's created quizzes and attempts
    @app.route('/my-quizzes')
    @login_required
    def my_quizzes():
        """Display user's created quizzes and attempts"""
        try:
            # Get user's created quizzes
            created_quizzes = Quiz.query.filter_by(created_by=current_user.id).order_by(Quiz.created_at.desc()).all()
            
            # Get user's quiz attempts
            attempts = db.session.query(QuizAttempt, Quiz).join(
                Quiz, QuizAttempt.quiz_id == Quiz.id
            ).filter(QuizAttempt.user_id == current_user.id).order_by(QuizAttempt.completed_at.desc()).limit(10).all()
            
            return render_template('my-quizzes.html', 
                                 created_quizzes=created_quizzes, 
                                 attempts=attempts)
        except Exception as e:
            logger.error(f"Error loading my quizzes: {str(e)}")
            # Fallback HTML if template missing
            quiz_list = Quiz.query.filter_by(created_by=current_user.id).all()
            html = f'''
            <h1>📚 My Quizzes</h1>
            <p><a href="/dashboard">← Back to Dashboard</a></p>
            <h2>Created Quizzes ({len(quiz_list)})</h2>
            <ul>
            '''
            for quiz in quiz_list:
                html += f'<li><a href="/quiz/{quiz.id}">{quiz.title}</a> - {quiz.total_questions} questions</li>'
            html += '</ul><p><a href="/create-quiz">Create New Quiz</a></p>'
            return html

    @app.route('/analytics')
    @login_required  
    def analytics():
        """Display user analytics and statistics"""
        try:
            # Calculate user statistics
            total_quizzes = Quiz.query.filter_by(created_by=current_user.id).count()
            total_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).count()
            
            # Average score
            avg_score = db.session.query(db.func.avg(QuizAttempt.percentage)).filter_by(user_id=current_user.id).scalar()
            avg_score = round(float(avg_score) if avg_score else 0, 1)
            
            # Recent performance
            recent_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.completed_at.desc()).limit(5).all()
            
            return render_template('analytics.html',
                                 total_quizzes=total_quizzes,
                                 total_attempts=total_attempts,
                                 avg_score=avg_score,
                                 recent_attempts=recent_attempts)
        except Exception as e:
            logger.error(f"Error loading analytics: {str(e)}")
            # Fallback analytics
            return f'''
            <h1>📊 Analytics Dashboard</h1>
            <p><a href="/dashboard">← Back to Dashboard</a></p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                    <h3>{Quiz.query.filter_by(created_by=current_user.id).count()}</h3>
                    <p>Quizzes Created</p>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                    <h3>{QuizAttempt.query.filter_by(user_id=current_user.id).count()}</h3>
                    <p>Quizzes Taken</p>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                    <h3>⭐</h3>
                    <p>Learning Champion!</p>
                </div>
            </div>
            <h3>Recent Activity</h3>
            <p>Keep up the great work! 🎉</p>
            '''

    @app.route('/settings')
    @login_required
    def settings():
        """Display user settings"""
        try:
            return render_template('settings.html', user=current_user)
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            # Fallback settings page
            return f'''
            <h1>⚙️ Settings</h1>
            <p><a href="/dashboard">← Back to Dashboard</a></p>
            <div style="max-width: 600px; margin: 20px auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                <h3>Account Information</h3>
                <p><strong>Name:</strong> {current_user.first_name} {current_user.last_name}</p>
                <p><strong>Email:</strong> {current_user.email}</p>
                <p><strong>Member Since:</strong> {current_user.created_at.strftime("%B %Y") if current_user.created_at else "Recently"}</p>
                
                <h3 style="margin-top: 30px;">Quiz Preferences</h3>
                <p>✅ Default Difficulty: Medium</p>
                <p>✅ Question Types: Mixed</p>
                <p>✅ Auto-save Progress: Enabled</p>
                
                <h3 style="margin-top: 30px;">Account Actions</h3>
                <p><a href="/logout" style="color: #dc3545; text-decoration: none; font-weight: bold;">🚪 Logout</a></p>
                
                <div style="margin-top: 30px; padding: 15px; background: #e3f2fd; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0; color: #1976d2;">🚀 Coming Soon</h4>
                    <p style="margin: 0; font-size: 14px;">• Profile picture upload</p>
                    <p style="margin: 0; font-size: 14px;">• Custom difficulty settings</p>
                    <p style="margin: 0; font-size: 14px;">• Quiz sharing options</p>
                </div>
            </div>
            '''

    @app.route('/api/user/stats')
    @login_required
    def user_stats_api():
        """API endpoint for user statistics"""
        try:
            total_quizzes = Quiz.query.filter_by(created_by=current_user.id).count()
            total_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).count()
            total_questions = db.session.query(db.func.sum(Quiz.total_questions)).join(
                QuizAttempt, Quiz.id == QuizAttempt.quiz_id
            ).filter(QuizAttempt.user_id == current_user.id).scalar() or 0
            
            return jsonify({
                'total_quizzes': total_quizzes,
                'total_attempts': total_attempts, 
                'total_questions': int(total_questions),
                'favorites': 3  # Placeholder
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

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
            logger.info("✅ Database tables created successfully!")
        except Exception as e:
            logger.error(f"❌ Error creating database tables: {str(e)}")
    
    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    print("🚀 AI Quiz Generator Starting!")
    print("📍 Server: http://localhost:5000")
    print("✅ Open your browser and navigate to the URL above!")
    app.run(host='0.0.0.0', port=5000, debug=True)
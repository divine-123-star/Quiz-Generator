# app/routes/quiz_routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import PyPDF2
from backend.models import db, Quiz, QuizQuestion, QuizAnswer, QuizAttempt, UserAnswer, PDFUpload
from backend.services.quiz_generator import GeminiQuizGenerator

# Create blueprint
quiz_bp = Blueprint('quiz', __name__)

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        current_app.logger.error(f"Error extracting PDF text: {str(e)}")
        raise Exception("Failed to extract text from PDF")

@quiz_bp.route('/create-quiz', methods=['GET', 'POST'])
@login_required
def create_quiz():
    """Handle quiz creation from PDF upload"""
    
    if request.method == 'GET':
        # Show the create quiz page
        return render_template('create-quiz.html')
    
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'pdf_file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No PDF file was uploaded'
                }), 400
            
            file = request.files['pdf_file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'No file selected'
                }), 400
            
            # Validate file
            if not allowed_file(file.filename):
                return jsonify({
                    'success': False,
                    'error': 'Only PDF files are allowed'
                }), 400
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)     # Reset to beginning
            
            if file_size > MAX_FILE_SIZE:
                return jsonify({
                    'success': False,
                    'error': 'File too large. Maximum size is 50MB'
                }), 400
            
            # Save the uploaded file
            filename = secure_filename(file.filename)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            
            # Create upload directory if it doesn't exist
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, f"{current_user.id}_{filename}")
            file.save(file_path)
            
            # Extract text from PDF
            current_app.logger.info(f"Extracting text from: {file_path}")
            pdf_text = extract_text_from_pdf(file_path)
            
            if not pdf_text.strip():
                return jsonify({
                    'success': False,
                    'error': 'Could not extract text from PDF. Please ensure the PDF contains readable text.'
                }), 400
            
            # Get quiz settings from form
            quiz_settings = {
                'title': request.form.get('title', 'AI Generated Quiz'),
                'numQuestions': request.form.get('numQuestions', '10'),
                'questionTypes': request.form.get('questionTypes', 'mixed'),
                'difficulty': request.form.get('difficulty', 'medium')
            }
            
            # Generate quiz using Gemini AI
            current_app.logger.info("Generating quiz with Gemini AI...")
            quiz_generator = GeminiQuizGenerator()
            quiz_data = quiz_generator.generate_quiz_from_text(pdf_text, quiz_settings)
            
            # Save PDF upload record
            pdf_upload = PDFUpload(
                user_id=current_user.id,
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                processed=True
            )
            db.session.add(pdf_upload)
            db.session.flush()  # Get the ID
            
            # Create quiz in database
            quiz = Quiz(
                title=quiz_data['title'],
                description=quiz_data['description'],
                total_questions=quiz_data['total_questions'],
                total_points=quiz_data['total_points'],
                difficulty_level=quiz_data['difficulty_level'],
                created_by=current_user.id
            )
            db.session.add(quiz)
            db.session.flush()  # Get quiz ID
            
            # Create questions and answers
            for question_data in quiz_data['questions']:
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_text=question_data['question_text'],
                    question_type=question_data['question_type'],
                    points=question_data['points']
                )
                db.session.add(question)
                db.session.flush()  # Get question ID
                
                # Create answers
                for answer_data in question_data['answers']:
                    answer = QuizAnswer(
                        question_id=question.id,
                        answer_text=answer_data['answer_text'],
                        is_correct=answer_data['is_correct']
                    )
                    db.session.add(answer)
            
            # Commit all changes
            db.session.commit()
            
            current_app.logger.info(f"Quiz created successfully with ID: {quiz.id}")
            
            return jsonify({
                'success': True,
                'quiz_id': quiz.id,
                'questions_count': quiz.total_questions,
                'message': f'Quiz "{quiz.title}" created successfully!'
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating quiz: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to create quiz: {str(e)}'
            }), 500

@quiz_bp.route('/quiz/<int:quiz_id>')
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
        current_app.logger.error(f"Error loading quiz: {str(e)}")
        flash('Quiz not found or error loading quiz', 'error')
        return redirect(url_for('main.dashboard'))

@quiz_bp.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
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
        db.session.flush()  # Get attempt ID
        
        score = 0
        results = []
        
        # Process each answer
        for question_id_str, user_answer_text in user_answers.items():
            question_id = int(question_id_str)
            question = QuizQuestion.query.get(question_id)
            
            if not question:
                continue
            
            # Find correct answer
            correct_answer = QuizAnswer.query.filter_by(
                question_id=question_id, 
                is_correct=True
            ).first()
            
            is_correct = False
            if correct_answer:
                if question.question_type in ['multiple_choice', 'true_false']:
                    # Exact match for MC and T/F
                    is_correct = user_answer_text.strip() == correct_answer.answer_text.strip()
                else:
                    # Partial match for short answer (you can improve this)
                    is_correct = user_answer_text.lower().strip() in correct_answer.answer_text.lower()
            
            if is_correct:
                score += question.points
            
            # Save user answer
            user_answer = UserAnswer(
                attempt_id=attempt.id,
                question_id=question_id,
                user_answer=user_answer_text,
                is_correct=is_correct
            )
            db.session.add(user_answer)
            
            # Add to results
            results.append({
                'question_id': question_id,
                'question_text': question.question_text,
                'user_answer': user_answer_text,
                'correct_answer': correct_answer.answer_text if correct_answer else '',
                'is_correct': is_correct,
                'points_earned': question.points if is_correct else 0,
                'points_possible': question.points
            })
        
        # Update attempt with score
        attempt.score = score
        attempt.calculate_percentage()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'attempt_id': attempt.id,
            'score': score,
            'total_points': quiz.total_points,
            'percentage': float(attempt.percentage),
            'results': results
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting quiz: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to submit quiz: {str(e)}'
        }), 500

@quiz_bp.route('/quiz/<int:quiz_id>/results/<int:attempt_id>')
@login_required
def quiz_results(quiz_id, attempt_id):
    """Display quiz results"""
    try:
        attempt = QuizAttempt.query.filter_by(
            id=attempt_id, 
            user_id=current_user.id, 
            quiz_id=quiz_id
        ).first_or_404()
        
        quiz = Quiz.query.get_or_404(quiz_id)
        user_answers = UserAnswer.query.filter_by(attempt_id=attempt_id).all()
        
        results_data = {
            'quiz': quiz.to_dict(),
            'attempt': attempt.to_dict(),
            'answers': [answer.to_dict() for answer in user_answers]
        }
        
        return render_template('quiz-results.html', results=results_data)
        
    except Exception as e:
        current_app.logger.error(f"Error loading results: {str(e)}")
        flash('Results not found', 'error')
        return redirect(url_for('main.dashboard'))

@quiz_bp.route('/my-quizzes')
@login_required
def my_quizzes():
    """Display user's created quizzes"""
    try:
        quizzes = Quiz.query.filter_by(created_by=current_user.id).order_by(Quiz.created_at.desc()).all()
        attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.completed_at.desc()).all()
        
        quiz_data = [quiz.to_dict() for quiz in quizzes]
        attempt_data = [attempt.to_dict() for attempt in attempts]
        
        return render_template('my-quizzes.html', quizzes=quiz_data, attempts=attempt_data)
        
    except Exception as e:
        current_app.logger.error(f"Error loading quizzes: {str(e)}")
        flash('Error loading quizzes', 'error')
        return redirect(url_for('main.dashboard'))
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.utils.pdf_processor import PDFProcessor
from app.utils.quiz_generator import QuizGenerator

api = Blueprint('api', __name__)

@api.route('/quiz/create', methods=['POST'])
@login_required
def create_quiz():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No PDF file provided'}), 400
    
    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Process PDF and generate quiz
    processor = PDFProcessor(current_app.config['UPLOAD_FOLDER'])
    generator = QuizGenerator()
    
    try:
        filepath = processor.save_pdf(file)
        text = processor.extract_text(filepath)
        quiz_data = generator.generate_quiz(text, request.form)
        
        # Save to database
        quiz = Quiz(
            title=request.form.get('title'),
            created_by=current_user.id,
            # ... other fields
        )
        db.session.add(quiz)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'quiz_id': quiz.id,
            'message': 'Quiz created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# app/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# backend/models.py - REPLACE THE USER CLASS WITH THIS
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    # NO username field - REMOVED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quizzes = db.relationship('Quiz', backref='creator', lazy=True)
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True)
    pdf_uploads = db.relationship('PDFUpload', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    total_questions = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Integer, default=0)
    difficulty_level = db.Column(db.Enum('easy', 'medium', 'hard'), default='medium')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'total_questions': self.total_questions,
            'total_points': self.total_points,
            'difficulty_level': self.difficulty_level,
            'created_at': self.created_at.isoformat(),
            'creator_name': f"{self.creator.first_name} {self.creator.last_name}"
        }
    
    def __repr__(self):
        return f'<Quiz {self.title}>'

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.Enum('multiple_choice', 'true_false', 'short_answer'), default='multiple_choice')
    points = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    answers = db.relationship('QuizAnswer', backref='question', lazy=True, cascade='all, delete-orphan')
    user_answers = db.relationship('UserAnswer', backref='question', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'points': self.points,
            'answers': [answer.to_dict() for answer in self.answers]
        }
    
    def __repr__(self):
        return f'<QuizQuestion {self.id}>'

class QuizAnswer(db.Model):
    __tablename__ = 'quiz_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'answer_text': self.answer_text,
            'is_correct': self.is_correct
        }
    
    def __repr__(self):
        return f'<QuizAnswer {self.id}>'

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Numeric(5, 2))
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_answers = db.relationship('UserAnswer', backref='attempt', lazy=True)
    
    def calculate_percentage(self):
        if self.total_points > 0:
            self.percentage = (self.score / self.total_points) * 100
        else:
            self.percentage = 0
        return self.percentage
    
    def to_dict(self):
        return {
            'id': self.id,
            'score': self.score,
            'total_points': self.total_points,
            'percentage': float(self.percentage) if self.percentage else 0,
            'completed_at': self.completed_at.isoformat()
        }
    
    def __repr__(self):
        return f'<QuizAttempt {self.id}>'

class UserAnswer(db.Model):
    __tablename__ = 'user_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    user_answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_answer': self.user_answer,
            'is_correct': self.is_correct,
            'question_text': self.question.question_text
        }
    
    def __repr__(self):
        return f'<UserAnswer {self.id}>'

class PDFUpload(db.Model):
    __tablename__ = 'pdf_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger)
    pages = db.Column(db.Integer)
    processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_size': self.file_size,
            'pages': self.pages,
            'processed': self.processed,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<PDFUpload {self.filename}>'
    
    # Create a simple hello world function to test the database connection
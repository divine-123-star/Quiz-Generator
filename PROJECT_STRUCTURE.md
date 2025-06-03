# AI Quiz Generator Project Structure

Based on actual folder structure in VS Code.

## Main Application Files
- `backend/app.py` - Main Flask application entry point
- `app/app.py` - Secondary Flask app file
- `app/models.py` - Database models (Users, Quizzes, Questions, etc.)
- `app/utils/database.py` - Database connection and utilities
- `app/utils/pdf_processor.py` - PDF text extraction logic

## Routes & APIs
- `app/routes/api.py` - API endpoints for AJAX calls
- `app/routes/quiz_routes.py` - Quiz-related routes

## Services
- `app/services/quiz_generator.py` - AI quiz generation logic

## Frontend Templates
- `app/templates/index.html` - Landing page
- `app/templates/login.html` - User login
- `app/templates/register.html` - User registration  
- `app/templates/dashboard.html` - User dashboard
- `app/templates/create-quiz.html` - Quiz creation interface
- `app/templates/base.html` - Base template
- `app/templates/auth/` - Authentication templates
- `app/templates/quiz/` - Quiz-specific templates

## Static Files
- `app/static/css/style.css` - Main stylesheet
- `app/static/js/main.js` - Frontend JavaScript
- `app/static/uploads/` - PDF upload storage

## Frontend Assets
- `frontend/assets/css/` - Additional CSS files
- `frontend/assets/js/` - Additional JavaScript files
- `frontend/assets/uploads/` - Additional upload storage

## Database & Configuration
- `schema.sql` - Database schema
- `migrations/` - Database migration files
- `requirements.txt` - Python dependencies
- `.env` - Environment variables
- `.gitignore` - Git ignore file

## Virtual Environment
- `venv/` - Python virtual environment with all packages

## Cache & Temp Files
- `__pycache__/` folders - Python bytecode cache
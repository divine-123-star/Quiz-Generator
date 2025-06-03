from backend.appl import create_app
from backend.models import db

# Create the Flask app
app = create_app()

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database tables reset successfully!")
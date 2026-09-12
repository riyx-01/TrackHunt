import os

# Load environment variables from .env file if present
from dotenv import load_dotenv
load_dotenv()

class Config:
    """Base configuration class."""
    # SECRET_KEY is used by Flask-WTF to protect against CSRF attacks
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key'
    
    # Configure SQLAlchemy database URI. We use SQLite for simplicity.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///job_tracker.db'
    
    # Disable tracking modifications to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False

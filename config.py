import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'food_nutrition_analyzer_default_secret_key')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'food_nutrition_db')
    PORT = int(os.getenv('PORT', 5000))

    # Email / SMTP Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', '')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '') or os.getenv('MAIL_USERNAME', '')

    # Password Reset Security Configuration
    RESET_TOKEN_EXPIRY_MINUTES = int(os.getenv('RESET_TOKEN_EXPIRY_MINUTES', 30))

import os

class Config:
    """Configuration class for Study Tracker App"""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # Password protection settings
    ENABLE_PASSWORD_PROTECTION = os.getenv('ENABLE_PASSWORD_PROTECTION', 'true').lower() == 'true'
    PASSWORD = os.getenv('APP_PASSWORD', 'admin')  # Default password for development

    # Database settings
    # SQLite (default): sqlite:///study_tracker.db
    # PostgreSQL: postgresql://user:password@localhost:5432/dbname
    # MySQL: mysql+pymysql://user:password@localhost:3306/dbname
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///study_tracker.db')
    DATABASE_TRACK_MODIFICATIONS = os.getenv('DATABASE_TRACK_MODIFICATIONS','False').lower() == 'true'

    # App settings
    APP_NAME = 'Study Tracker'

    # UI settings
    DEFAULT_THEME = os.getenv('DEFAULT_THEME', 'light')  # 'light' or 'dark'

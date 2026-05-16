import os

class Config:
    """Base configuration class for Connect-X application."""
    
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'connect-x-super-secret-key-change-in-production'
    
    # ==========================================================
    # DATABASE CONFIGURATION
    # ==========================================================
    # DEFAULT: SQLite for demo (works out of the box)
    # To switch to MySQL, uncomment the MySQL line and comment the SQLite line
    #
    # MySQL connection:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+mysqlconnector://ig_db:igdb2004@localhost/ig_db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'images', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Pagination
    POSTS_PER_PAGE = 10


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Config dictionary for easy switching
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

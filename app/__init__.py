import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app(config_name='default'):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure upload directory exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'app/static/images/uploads'), exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # User loader for Flask-Login
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.posts import posts_bp
    from app.routes.profile import profile_bp
    from app.routes.messages import messages_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(messages_bp)
    
    # Create all database tables
    with app.app_context():
        db.create_all()
    
    return app

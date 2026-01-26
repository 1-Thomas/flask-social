from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from .config import Config
from app.main import bp as main_bp



db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(User, int(user_id))
        except ValueError:
            return None

 
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app import models

    return app

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from .config import Config
from app.main import bp as main_bp
from app import models

_USERS = {
    1: {"id": 1, "username": "demo"},
}

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
        data = _USERS.get(int(user_id))
        if data is None:
            return None
        return User(data["id"], data["username"])
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app import models

    return app

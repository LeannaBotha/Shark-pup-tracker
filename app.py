import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "shark_pup_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize the database
db = SQLAlchemy(app, model_class=Base)

# Initialize Flask-Login - require login to access the application
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message_category = 'warning'
login_manager.login_message = "Please log in to access the Shark Pup Logger."

@login_manager.user_loader
def load_user(user_id):
    from models import SharkPupUser
    return SharkPupUser.query.get(int(user_id))
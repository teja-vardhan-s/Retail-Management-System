from flask import Flask, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager


app = Flask(__name__)
app.config['SECRET_KEY'] = '50fa3a60abc2fdbd409a9565'
app.config['SESSION_TYPE'] = 'filesystem'

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message_category = 'info'

from pos_system.routes import *
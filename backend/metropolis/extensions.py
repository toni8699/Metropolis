from apifairy import APIFairy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_marshmallow import Marshmallow
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

ma = Marshmallow()
apifairy = APIFairy()
sqldb = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
socketio = SocketIO()

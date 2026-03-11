from flask import Flask
from flask_login import LoginManager
from models import db, User
from config import Config
from socketio_events import socketio  

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth
    from routes.quiz import quiz
    from routes.game import game

    app.register_blueprint(auth)
    app.register_blueprint(quiz)
    app.register_blueprint(game)

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, port=5001)
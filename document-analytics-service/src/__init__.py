import os
from flask import Flask
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.document import document_bp

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    CORS(app)

    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(document_bp, url_prefix='/api')

    # Add route for document interface
    @app.route('/')
    def index():
        return app.send_static_file('documents.html')

    with app.app_context():
        db.create_all()

    return app

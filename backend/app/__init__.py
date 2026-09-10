from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from .config import Config
from flask_mail import Mail


db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()

def create_app():
    import os
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,https://smart-internship-system-eight.vercel.app"
    ).split(",")

    allowed_origins = [origin.strip() for origin in allowed_origins]

    allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,https://smart-internship-system-eight.vercel.app"
    ).split(",")

    allowed_origins = [origin.strip() for origin in allowed_origins]

    CORS(
    app,
    resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": [
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
                "OPTIONS"
            ],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "ngrok-skip-browser-warning"
            ],
            "supports_credentials": True
        }
    }
)

    from .routes.auth import auth_bp
    from .routes.students import students_bp
    from .routes.internships import internships_bp
    from .routes.matching import matching_bp
    from .routes.chat import chat_bp
    from .routes.notifications import notifications_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(students_bp, url_prefix="/api/students")
    app.register_blueprint(internships_bp, url_prefix="/api/internships")
    app.register_blueprint(matching_bp, url_prefix="/api/matching")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")

    import os
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Import models so SQLAlchemy knows about them
    from .models import User, Student, Employer, Internship, Application, Certificate, Notification

    with app.app_context():
        db.create_all()

    return app
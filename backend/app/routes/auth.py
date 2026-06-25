from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from flask_mail import Message
from app import db, mail
from app.models import User, Student, Employer
from app.schemas import RegisterSchema, LoginSchema, ForgotPasswordSchema, ResetPasswordSchema
from app.utils.validation import validate_request
import secrets

auth_bp = Blueprint('auth', __name__)


@auth_bp.post('/register')
def register():
    data, error = validate_request(RegisterSchema(), request.get_json() or {})
    if error:
        return jsonify(error), 400

    if data['role'] not in ['student', 'employer']:
        return jsonify({"error": "Role must be 'student' or 'employer'"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        email=data['email'],
        password=generate_password_hash(data['password']),
        role=data['role']
    )
    db.session.add(user)
    db.session.flush()

    if data['role'] == 'student':
        profile = Student(
            user_id=user.id,
            full_name=data.get('full_name', ''),
        )
        db.session.add(profile)
    elif data['role'] == 'employer':
        profile = Employer(
            user_id=user.id,
            company_name=data.get('company_name', ''),
        )
        db.session.add(profile)

    db.session.commit()

    return jsonify({
        "message": "Registration successful",
        "user": user.to_dict()
    }), 201


@auth_bp.post('/login')
def login():
    data, error = validate_request(LoginSchema(), request.get_json() or {})
    if error:
        return jsonify(error), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "role": user.role
        }
    )

    return jsonify({
        "access_token": access_token,
        "user": user.to_dict()
    }), 200


@auth_bp.post('/forgot-password')
def forgot_password():
    data, error = validate_request(ForgotPasswordSchema(), request.get_json() or {})
    if error:
        return jsonify(error), 400

    email = data['email']
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No account found with that email"}), 404

    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    db.session.commit()

    reset_link = f"http://localhost:5173/reset-password?token={reset_token}"

    try:
        msg = Message(
            subject="Smart Internship — Password Reset",
            recipients=[email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; padding: 30px; border-radius: 10px; background: #f0f4ff;">
                <h2 style="color: #3b82f6; text-align: center;">🔑 Password Reset</h2>
                <p style="color: #555;">Hello,</p>
                <p style="color: #555;">You requested a password reset for your Smart Internship account.</p>
                <p style="color: #555;">Click the button below to reset your password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}"
                       style="background: #3b82f6; color: white; padding: 12px 30px;
                              border-radius: 8px; text-decoration: none; font-weight: bold;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #999; font-size: 12px;">
                    If you didn't request this, ignore this email.<br/>
                    This link expires in 1 hour.
                </p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    Smart Internship System
                </p>
            </div>
            """
        )
        mail.send(msg)
        return jsonify({"message": "Password reset email sent successfully"}), 200

    except Exception as e:
        print("Mail error:", e)
        return jsonify({"error": "Failed to send email. Check mail configuration."}), 500


@auth_bp.post('/reset-password')
def reset_password():
    data, error = validate_request(ResetPasswordSchema(), request.get_json() or {})
    if error:
        return jsonify(error), 400

    user = User.query.filter_by(reset_token=data['reset_token']).first()
    if not user:
        return jsonify({"error": "Invalid or expired reset token"}), 400

    user.password = generate_password_hash(data['new_password'])
    user.reset_token = None
    db.session.commit()

    return jsonify({"message": "Password reset successful"}), 200
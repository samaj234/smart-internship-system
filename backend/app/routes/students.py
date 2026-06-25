from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from app import db
from app.models import Student
from app.services.cv_parser import parse_cv
from app.services.embedder import embed_text
from app.schemas import UpdateProfileSchema
from app.utils.validation import validate_request

students_bp = Blueprint('students', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@students_bp.get('/profile')
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"error": "Student profile not found"}), 404
    return jsonify(student.to_dict()), 200


@students_bp.put('/profile')
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    data, error = validate_request(UpdateProfileSchema(), request.get_json() or {})
    if error:
        return jsonify(error), 400

    student.full_name = data.get('full_name', student.full_name)
    student.phone = data.get('phone', student.phone)
    student.university = data.get('university', student.university)
    student.degree = data.get('degree', student.degree)
    student.gpa = data.get('gpa', student.gpa)
    student.skills = data.get('skills', student.skills)

    if student.skills:
        skills_text = " ".join(student.skills)
        student.profile_embedding = embed_text(skills_text)

    db.session.commit()
    return jsonify(student.to_dict()), 200


@students_bp.post('/upload-cv')
@jwt_required()
def upload_cv():
    user_id = int(get_jwt_identity())

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF and DOCX files allowed"}), 400

    filename = secure_filename(f"cv_{user_id}_{file.filename}")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    parsed = parse_cv(filepath)

    student = Student.query.filter_by(user_id=user_id).first()
    student.cv_path = filepath
    student.full_name = parsed.get('name') or student.full_name
    student.phone = parsed.get('phone') or student.phone
    student.skills = parsed.get('skills') or student.skills

    embed_input = " ".join(parsed.get('skills', [])) + " " + parsed.get('raw_text', '')[:500]
    student.profile_embedding = embed_text(embed_input)

    db.session.commit()

    return jsonify({
        "message": "CV uploaded and parsed successfully",
        "parsed_data": {
            "name": parsed.get('name'),
            "email": parsed.get('email'),
            "phone": parsed.get('phone'),
            "skills": parsed.get('skills'),
        },
        "profile": student.to_dict()
    }), 200
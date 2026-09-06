from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import unicodedata
from datetime import datetime
from app import db
from app.models import Student, User, Certificate, Employer, Internship, Application
from app.services.cv_parser import parse_cv
from app.services.embedder import embed_text
from app.schemas import UpdateProfileSchema
from app.utils.validation import validate_request

students_bp = Blueprint('students', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}
ALLOWED_CERT_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_cert_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_CERT_EXTENSIONS


def _clean_email(email):
    """Normalize an email string for comparison. PDF text extraction
    (pdfminer, mammoth, etc.) frequently injects invisible formatting
    characters — zero-width spaces, control chars, non-breaking spaces —
    around text runs depending on how the source PDF was generated.
    Two emails can look identical to the eye and still fail a strict `==`
    without this cleanup."""
    if not email:
        return ''
    # Cf = "format" characters (zero-width space/joiner, etc.),
    # Cc = control characters. Strip both.
    cleaned = ''.join(
        ch for ch in email
        if unicodedata.category(ch) not in ('Cf', 'Cc')
    )
    # Collapse any remaining whitespace (regular or non-breaking) and trim.
    cleaned = ''.join(cleaned.split())
    return cleaned.strip().lower()


def _names_overlap(name_a, name_b):
    """Loose match: True if the two names share at least one token.
    Avoids hard-failing on formatting differences (middle names,
    initials, ordering) while still catching a clearly different name."""
    if not name_a or not name_b:
        return True  # nothing to compare against — don't warn on missing data
    tokens_a = set(name_a.lower().split())
    tokens_b = set(name_b.lower().split())
    return len(tokens_a & tokens_b) > 0


def _can_access_student_file(user_id, student):
    """True if the requester is the student who owns the file, or an
    employer who has received at least one application from them."""
    if not student:
        return False
    if student.user_id == user_id:
        return True

    employer = Employer.query.filter_by(user_id=user_id).first()
    if not employer:
        return False

    has_application = db.session.query(Application.id).join(
        Internship, Application.internship_id == Internship.id
    ).filter(
        Application.student_id == student.id,
        Internship.employer_id == employer.id
    ).first()

    return has_application is not None


@students_bp.get('/cv/<path:filename>')
# @jwt_required()
def serve_cv(filename):
    """
    Serves uploaded CV files to authenticated users.
    Only employers and the student who owns the CV should access this.
    """
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)


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
    user = User.query.get(user_id)

    # --- Identity verification ---
    cv_email = _clean_email(parsed.get('email'))
    account_email = _clean_email(user.email)
    email_mismatch = bool(cv_email) and cv_email != account_email

    # Temporary diagnostic — remove once the mismatch cause is confirmed.
    # repr() surfaces any invisible characters that wouldn't otherwise
    # show up in a normal print.
    print(f"[CV email check] raw_extracted={parsed.get('email')!r} "
          f"cleaned_cv={cv_email!r} cleaned_account={account_email!r} "
          f"mismatch={email_mismatch}")

    if email_mismatch:
        try:
            os.remove(filepath)
        except OSError:
            pass

        return jsonify({
            "error": (
                "The email on this CV doesn't match your account email. "
                "Please upload your own CV, or update your account email first "
                "if it's out of date."
            ),
            "detected_email": parsed.get('email'),
            "account_email": user.email,
        }), 422

    name_mismatch = not _names_overlap(student.full_name, parsed.get('name'))

    student.cv_path = filepath
    student.full_name = parsed.get('name') or student.full_name
    student.phone = parsed.get('phone') or student.phone
    student.skills = parsed.get('skills') or student.skills

    # Degree and university follow the same "keep existing value if
    # nothing was extracted" rule as name/phone/skills above. GPA is
    # handled separately with `is not None` rather than `or`, because a
    # real extracted GPA of 0.0 is falsy in Python and would otherwise be
    # discarded in favor of whatever value was already on the record.
    student.degree = parsed.get('degree') or student.degree
    student.university = parsed.get('university') or student.university
    student.gpa = parsed.get('gpa') if parsed.get('gpa') is not None else student.gpa
    raw_text = parsed.get('raw_text') or ''
    student.raw_text = raw_text[:3000] if raw_text else student.raw_text

    embed_input = " ".join(parsed.get('skills', [])) + " " + parsed.get('raw_text', '')[:500]
    student.profile_embedding = embed_text(embed_input)

    db.session.commit()

    response = {
        "message": "CV uploaded and parsed successfully",
        "parsed_data": {
            "name": parsed.get('name'),
            "email": parsed.get('email'),
            "phone": parsed.get('phone'),
            "skills": parsed.get('skills'),
            "certifications": parsed.get('certifications'),
            "degree": parsed.get('degree'),
            "university": parsed.get('university'),
            "gpa": parsed.get('gpa'),
        },
        "profile": student.to_dict()
    }

    if name_mismatch:
        response["warning"] = (
            "The name on this CV doesn't closely match your profile name — "
            "please double-check your profile after upload."
        )

    return jsonify(response), 200


#  Certificates 

@students_bp.post('/certificates')
@jwt_required()
def upload_certificate():
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_cert_file(file.filename):
        return jsonify({"error": "Only PDF, DOCX, JPG, and PNG files allowed"}), 400

    # Timestamp in the filename keeps multiple certificates from the same
    # student from colliding on disk if they share an original filename.
    unique_prefix = int(datetime.utcnow().timestamp())
    filename = secure_filename(f"cert_{student.id}_{unique_prefix}_{file.filename}")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    certificate = Certificate(
        student_id=student.id,
        original_filename=file.filename,
        file_path=filepath
    )
    db.session.add(certificate)
    db.session.commit()

    return jsonify({
        "message": "Certificate uploaded successfully",
        "certificate": certificate.to_dict()
    }), 201


@students_bp.get('/certificates')
@jwt_required()
def list_certificates():
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    certs = Certificate.query.filter_by(student_id=student.id) \
        .order_by(Certificate.uploaded_at.desc()).all()

    return jsonify({"certificates": [c.to_dict() for c in certs]}), 200


@students_bp.delete('/certificates/<int:certificate_id>')
@jwt_required()
def delete_certificate(certificate_id):
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    certificate = Certificate.query.get_or_404(certificate_id)
    if certificate.student_id != student.id:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        if certificate.file_path and os.path.exists(certificate.file_path):
            os.remove(certificate.file_path)
    except OSError:
        pass

    db.session.delete(certificate)
    db.session.commit()

    return jsonify({"message": "Certificate deleted"}), 200


@students_bp.get('/certificates/<int:certificate_id>/file')
@jwt_required()
def serve_certificate(certificate_id):
    user_id = int(get_jwt_identity())
    certificate = Certificate.query.get_or_404(certificate_id)
    student = Student.query.get(certificate.student_id)

    if not _can_access_student_file(user_id, student):
        return jsonify({"error": "Unauthorized"}), 403

    directory = os.path.dirname(certificate.file_path)
    filename = os.path.basename(certificate.file_path)
    return send_from_directory(directory, filename)
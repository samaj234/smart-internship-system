from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import or_
import os
from app import db
from app.models import Internship, Employer
from app.services.embedder import embed_text
from app.services.job_parser import parse_job_description
from app.schemas import CreateInternshipSchema, UpdateInternshipSchema
from app.utils.validation import validate_request

ALLOWED_JOB_DESC_EXTENSIONS = {'pdf', 'docx'}

internships_bp = Blueprint('internships', __name__)


@internships_bp.post('/parse')
@jwt_required()
def parse_job_description_route():
    """
    Lets an employer upload a job description file (PDF/DOCX) instead of
    typing the posting by hand. Returns best-effort parsed fields for the
    employer to review/edit in the form — it does NOT create an
    internship itself; PostInternshipForm still submits via the normal
    create_internship route afterward, same as CV upload pre-fills a
    student profile without silently overwriting it.
    """
    user_id = int(get_jwt_identity())
    employer = Employer.query.filter_by(user_id=user_id).first()

    if not employer:
        return jsonify({"error": "Employer profile not found"}), 404

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_JOB_DESC_EXTENSIONS:
        return jsonify({"error": "Only PDF and DOCX files allowed"}), 400

    filename = secure_filename(f"jobdesc_{employer.id}_{file.filename}")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        parsed = parse_job_description(filepath)
    finally:
        # Nothing references this file afterward — it's only needed long
        # enough to extract text from it, unlike a CV or certificate.
        try:
            os.remove(filepath)
        except OSError:
            pass

    return jsonify({"parsed": parsed}), 200

@internships_bp.get('/')
def get_all_internships():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 12, type=int)
    search = request.args.get('search', '', type=str).strip()
    location = request.args.get('location', '', type=str).strip()

    # Clamp to sane bounds so a malicious or buggy client can't request page=-1 or limit=10000
    page = max(page, 1)
    limit = min(max(limit, 1), 50)

    # An internship with no deadline never expires; one with a deadline
    # in the past is hidden from students automatically, without needing
    # a background job to flip is_active — the query stays the single
    # source of truth for "currently applyable."
    query = Internship.query.filter(
        Internship.is_active == True,
        or_(Internship.deadline.is_(None), Internship.deadline >= datetime.utcnow())
    )

    if search:
        query = query.filter(Internship.title.ilike(f"%{search}%"))

    if location:
        query = query.filter(Internship.location.ilike(f"%{location}%"))

    query = query.order_by(Internship.created_at.desc())

    paginated = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        "internships": [i.to_dict() for i in paginated.items],
        "page": paginated.page,
        "total_pages": paginated.pages,
        "total_results": paginated.total,
        "has_next": paginated.has_next,
        "has_prev": paginated.has_prev
    }), 200


@internships_bp.get('/my-internships')
@jwt_required()
def get_my_internships():
    """Employer sees all their own internships, including inactive ones"""
    user_id = int(get_jwt_identity())
    employer = Employer.query.filter_by(user_id=user_id).first()

    if not employer:
        return jsonify({"error": "Employer profile not found"}), 404

    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 12, type=int)
    page = max(page, 1)
    limit = min(max(limit, 1), 50)

    query = Internship.query.filter_by(employer_id=employer.id).order_by(Internship.created_at.desc())
    paginated = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        "internships": [i.to_dict() for i in paginated.items],
        "page": paginated.page,
        "total_pages": paginated.pages,
        "total_results": paginated.total
    }), 200


@internships_bp.get('/<int:internship_id>')
def get_internship(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    return jsonify(internship.to_dict()), 200


@internships_bp.post('/')
@jwt_required()
def create_internship():
    user_id = int(get_jwt_identity())
    employer = Employer.query.filter_by(user_id=user_id).first()

    if not employer:
        return jsonify({"error": "Employer profile not found"}), 404

    data, error = validate_request(CreateInternshipSchema(), request.get_json() or {})
    if error:
        return jsonify(error), 400

    # Generate SBERT embedding from job description + skills
    embed_input = data['description']
    if data.get('required_skills'):
        embed_input += " " + " ".join(data['required_skills'])

    internship = Internship(
        employer_id=employer.id,
        title=data['title'],
        description=data['description'],
        required_skills=data.get('required_skills', []),
        location=data.get('location', ''),
        duration=data.get('duration', ''),
        stipend=data.get('stipend', ''),
        deadline=data.get('deadline'),
        requires_cover_letter=data.get('requires_cover_letter', False),
        requires_recommendation_letter=data.get('requires_recommendation_letter', False),
        description_embedding=embed_text(embed_input)
    )

    db.session.add(internship)
    db.session.commit()

    return jsonify({
        "message": "Internship created successfully",
        "internship": internship.to_dict()
    }), 201


@internships_bp.put('/<int:internship_id>')
@jwt_required()
def update_internship(internship_id):
    user_id = int(get_jwt_identity())
    employer = Employer.query.filter_by(user_id=user_id).first()
    internship = Internship.query.get_or_404(internship_id)

    if internship.employer_id != employer.id:
        return jsonify({"error": "Unauthorized"}), 403

    data, error = validate_request(UpdateInternshipSchema(), request.get_json() or {})
    if error:
        return jsonify(error), 400

    internship.title = data.get('title', internship.title)
    internship.description = data.get('description', internship.description)
    internship.required_skills = data.get('required_skills', internship.required_skills)
    internship.location = data.get('location', internship.location)
    internship.duration = data.get('duration', internship.duration)
    internship.stipend = data.get('stipend', internship.stipend)
    internship.is_active = data.get('is_active', internship.is_active)
    internship.requires_cover_letter = data.get('requires_cover_letter', internship.requires_cover_letter)
    internship.requires_recommendation_letter = data.get('requires_recommendation_letter', internship.requires_recommendation_letter)

    if 'deadline' in data:
        internship.deadline = data['deadline']

    # Regenerate embedding
    embed_input = internship.description + " " + " ".join(internship.required_skills or [])
    internship.description_embedding = embed_text(embed_input)

    db.session.commit()
    return jsonify(internship.to_dict()), 200


@internships_bp.delete('/<int:internship_id>')
@jwt_required()
def delete_internship(internship_id):
    user_id = int(get_jwt_identity())
    employer = Employer.query.filter_by(user_id=user_id).first()
    internship = Internship.query.get_or_404(internship_id)

    if internship.employer_id != employer.id:
        return jsonify({"error": "Unauthorized"}), 403

    internship.is_active = False
    db.session.commit()
    return jsonify({"message": "Internship deactivated"}), 200
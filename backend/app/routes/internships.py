from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Internship, Employer
from app.services.embedder import embed_text
from app.schemas import CreateInternshipSchema, UpdateInternshipSchema
from app.utils.validation import validate_request

internships_bp = Blueprint('internships', __name__)

@internships_bp.get('/')
def get_all_internships():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 12, type=int)
    search = request.args.get('search', '', type=str).strip()
    location = request.args.get('location', '', type=str).strip()

    # Clamp to sane bounds so a malicious or buggy client can't request page=-1 or limit=10000
    page = max(page, 1)
    limit = min(max(limit, 1), 50)

    query = Internship.query.filter_by(is_active=True)

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
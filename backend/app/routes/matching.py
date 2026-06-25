from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Student, Internship, Application, Employer
from app.services.embedder import cosine_similarity
from app import db
from app.schemas import UpdateApplicationStatusSchema
from app.utils.validation import validate_request

matching_bp = Blueprint('matching', __name__)


@matching_bp.get('/recommendations')
@jwt_required()
def get_recommendations():
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()

    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    if not student.profile_embedding:
        return jsonify({"error": "Please upload your CV first to get recommendations"}), 400

    internships = Internship.query.filter_by(is_active=True).all()

    scores = []
    for job in internships:
        if job.description_embedding:
            score = cosine_similarity(
                student.profile_embedding,
                job.description_embedding
            )
            scores.append({
                "internship": job.to_dict(),
                "match_score": round(score, 4),
                "match_percentage": f"{round(score * 100, 1)}%"
            })

    ranked = sorted(scores, key=lambda x: x["match_score"], reverse=True)

    return jsonify({
        "student": student.full_name,
        "total_matches": len(ranked),
        "recommendations": ranked[:10]
    }), 200


@matching_bp.post('/apply/<int:internship_id>')
@jwt_required()
def apply(internship_id):
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()

    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    internship = Internship.query.get_or_404(internship_id)

    existing = Application.query.filter_by(
        student_id=student.id,
        internship_id=internship_id
    ).first()

    if existing:
        return jsonify({"error": "Already applied to this internship"}), 409

    score = 0.0
    if student.profile_embedding and internship.description_embedding:
        score = cosine_similarity(
            student.profile_embedding,
            internship.description_embedding
        )

    application = Application(
        student_id=student.id,
        internship_id=internship_id,
        match_score=round(score, 4)
    )

    db.session.add(application)
    db.session.commit()

    return jsonify({
        "message": "Application submitted successfully",
        "application": application.to_dict(),
        "match_score": f"{round(score * 100, 1)}%"
    }), 201


@matching_bp.get('/applicants/<int:internship_id>')
@jwt_required()
def get_applicants(internship_id):
    """Employer sees ranked applicants for their job"""
    applicants = Application.query.filter_by(
        internship_id=internship_id
    ).order_by(Application.match_score.desc()).all()

    result = []
    for app in applicants:
        student = Student.query.get(app.student_id)
        result.append({
            "application_id": app.id,
            "student": student.to_dict(),
            "match_score": app.match_score,
            "match_percentage": f"{round(app.match_score * 100, 1)}%",
            "status": app.status,
            "applied_at": app.applied_at.isoformat()
        })

    return jsonify({
        "internship_id": internship_id,
        "total_applicants": len(result),
        "applicants": result
    }), 200


@matching_bp.get('/my-applications')
@jwt_required()
def get_my_applications():
    """Student sees their own applications with internship details"""
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()

    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    applications = Application.query.filter_by(
        student_id=student.id
    ).order_by(Application.applied_at.desc()).all()

    result = []
    for app in applications:
        internship = Internship.query.get(app.internship_id)
        result.append({
            "id": app.id,
            "status": app.status,
            "match_score": app.match_score,
            "match_percentage": f"{round(app.match_score * 100, 1)}%" if app.match_score is not None else None,
            "applied_at": app.applied_at.isoformat(),
            "internship": internship.to_dict() if internship else None
        })

    return jsonify({
        "total_applications": len(result),
        "applications": result
    }), 200


@matching_bp.patch('/applications/<int:application_id>/status')
@jwt_required()
def update_application_status(application_id):
    """Employer accepts or rejects an applicant"""
    user_id = int(get_jwt_identity())
    employer = Employer.query.filter_by(user_id=user_id).first()

    if not employer:
        return jsonify({"error": "Employer profile not found"}), 404

    application = Application.query.get_or_404(application_id)
    internship = Internship.query.get(application.internship_id)

    if not internship or internship.employer_id != employer.id:
        return jsonify({"error": "Unauthorized"}), 403

    data, error = validate_request(UpdateApplicationStatusSchema(), request.get_json() or {})
    if error:
        return jsonify(error), 400

    application.status = data['status']
    db.session.commit()

    return jsonify({
        "message": f"Application {data['status']}",
        "application": application.to_dict()
    }), 200
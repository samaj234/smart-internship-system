from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import or_
import os
from app.models import Student, Internship, Application, Employer, Certificate, Notification
from app.services.embedder import cosine_similarity, embed_text
from app.services.tfidf_matcher import TFIDFMatcher
from app.services.preprocessing import preprocess_for_tfidf, preprocess_for_sbert, build_sbert_text
from app import db
from app.schemas import UpdateApplicationStatusSchema, UpdateApplicationFeedbackSchema
from app.utils.validation import validate_request
from app.services.skill_synonyms import skills_match, normalize_skill
import numpy as np


matching_bp = Blueprint('matching', __name__)

ALLOWED_APPLICATION_DOC_EXTENSIONS = {'pdf', 'docx', 'doc'}

# Weights for the three-way hybrid score: SBERT (semantic similarity),
# TF-IDF (keyword overlap), and skill match percentage (explicit ESCO
# skill overlap). Skills weighted highest since it's the most
# interpretable signal to show a student — an SBERT-dominant score can
# look low even with strong skill overlap, which is confusing without
# visibility into the semantic-similarity math. Re-tune using
# rjdb_evaluator.py results. They must sum to 1.0.
WEIGHT_SBERT = 0.3
WEIGHT_TFIDF = 0.2
WEIGHT_SKILLS = 0.5


def _allowed_doc(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_APPLICATION_DOC_EXTENSIONS


def _save_application_doc(file_storage, user_id, field_name):
    """Saves an uploaded application document (cover letter, certificate,
    or recommendation letter) and returns its stored filepath, or None if
    no file was provided."""
    if not file_storage or file_storage.filename == '':
        return None
    if not _allowed_doc(file_storage.filename):
        return None
    filename = secure_filename(f"{field_name}_{user_id}_{file_storage.filename}")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file_storage.save(filepath)
    return filepath


def compute_skill_gap(student_skills: list, required_skills: list) -> dict:
    """
    Computes skill gap between student skills and job requirements,
    using synonym-aware matching so that equivalent terms
    (JS/JavaScript, ML/Machine Learning, etc.) are correctly
    recognized as matches rather than gaps.
    """
    if not student_skills or not required_skills:
        return {
            "matched_skills": [],
            "missing_skills": required_skills or [],
            "extra_skills": student_skills or [],
            "gap_percentage": 100.0,
            "match_percentage": 0.0
        }

    def student_has_skill(required_skill: str) -> bool:
        for student_skill in student_skills:
            if skills_match(student_skill, required_skill):
                return True
        return False

    def job_needs_skill(student_skill: str) -> bool:
        for required_skill in required_skills:
            if skills_match(student_skill, required_skill):
                return True
        return False

    matched = [s for s in required_skills if student_has_skill(s)]
    missing = [s for s in required_skills if not student_has_skill(s)]
    extra = [s for s in student_skills if not job_needs_skill(s)]

    match_pct = (len(matched) / len(required_skills)) * 100 if required_skills else 0
    gap_pct = 100 - match_pct

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra,
        "gap_percentage": round(gap_pct, 1),
        "match_percentage": round(match_pct, 1)
    }


def compute_hybrid_score(
    student_text: str,
    job_text: str,
    skill_match_percentage: float,
    sbert_embedding_student=None,
    sbert_embedding_job=None,
) -> dict:
    """
    Computes three-way hybrid match score combining SBERT (semantic
    similarity), TF-IDF (keyword overlap), and explicit ESCO skill
    match percentage. Skill match is included as its own weighted
    term rather than relying on TF-IDF to implicitly approximate it.
    """
    if sbert_embedding_student is not None and sbert_embedding_job is not None:
        sbert_score = float(cosine_similarity(
            sbert_embedding_student,
            sbert_embedding_job
        ))
    else:
        student_emb = embed_text(preprocess_for_sbert(student_text))
        job_emb = embed_text(preprocess_for_sbert(job_text))
        sbert_score = float(cosine_similarity(student_emb, job_emb))

    matcher = TFIDFMatcher()
    matcher.fit([student_text, job_text])
    tfidf_score = float(matcher.similarity(
        preprocess_for_tfidf(student_text),
        preprocess_for_tfidf(job_text)
    ))

    skill_score = skill_match_percentage / 100

    final_score = (
        WEIGHT_SBERT * sbert_score +
        WEIGHT_TFIDF * tfidf_score +
        WEIGHT_SKILLS * skill_score
    )

    return {
        "sbert_score": round(sbert_score, 4),
        "tfidf_score": round(tfidf_score, 4),
        "skill_score": round(skill_score, 4),
        "hybrid_score": round(final_score, 4),
        "weights": {"sbert": WEIGHT_SBERT, "tfidf": WEIGHT_TFIDF, "skills": WEIGHT_SKILLS}
    }


def get_learning_recommendations(missing_skills: list) -> list:
    """
    Maps missing skills to learning resources across multiple types:
    curated courses, generated YouTube search links, and generated
    PDF/guide search links. Every missing skill returns at least one
    resource of each available type.
    """
    LEARNING_MAP = {
        "python": [{"type": "course", "resource": "Python for Everybody", "provider": "Coursera (University of Michigan)", "url": "https://www.coursera.org/specializations/python"}],
        "javascript": [{"type": "course", "resource": "The Complete JavaScript Course", "provider": "Udemy", "url": "https://www.udemy.com/course/the-complete-javascript-course/"}],
        "sql": [{"type": "course", "resource": "SQL for Data Science", "provider": "Coursera (UC Davis)", "url": "https://www.coursera.org/learn/sql-for-data-science"}],
        "react": [{"type": "course", "resource": "React - The Complete Guide", "provider": "Udemy", "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/"}],
        "machine learning": [{"type": "course", "resource": "Machine Learning Specialization", "provider": "Coursera (Andrew Ng)", "url": "https://www.coursera.org/specializations/machine-learning-introduction"}],
        "deep learning": [{"type": "course", "resource": "Deep Learning Specialization", "provider": "Coursera (deeplearning.ai)", "url": "https://www.coursera.org/specializations/deep-learning"}],
        "data analysis": [{"type": "course", "resource": "Google Data Analytics Certificate", "provider": "Coursera", "url": "https://www.coursera.org/professional-certificates/google-data-analytics"}],
        "data science": [{"type": "course", "resource": "IBM Data Science Professional Certificate", "provider": "Coursera", "url": "https://www.coursera.org/professional-certificates/ibm-data-science"}],
        "tensorflow": [{"type": "course", "resource": "TensorFlow Developer Certificate", "provider": "Coursera (deeplearning.ai)", "url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice"}],
        "aws": [{"type": "course", "resource": "AWS Certified Cloud Practitioner", "provider": "AWS Training", "url": "https://aws.amazon.com/certification/certified-cloud-practitioner/"}],
        "azure": [{"type": "course", "resource": "Microsoft Azure Fundamentals (AZ-900)", "provider": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/certifications/azure-fundamentals/"}],
        "docker": [{"type": "course", "resource": "Docker and Kubernetes: The Complete Guide", "provider": "Udemy", "url": "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/"}],
        "project management": [{"type": "course", "resource": "Google Project Management Certificate", "provider": "Coursera", "url": "https://www.coursera.org/professional-certificates/google-project-management"}],
        "financial analysis": [{"type": "course", "resource": "Financial Analysis and Valuation", "provider": "Coursera (Wharton)", "url": "https://www.coursera.org/learn/wharton-financial-analysis"}],
        "digital marketing": [{"type": "course", "resource": "Google Digital Marketing Certificate", "provider": "Google", "url": "https://grow.google/certificates/digital-marketing-ecommerce/"}],
        "tableau": [{"type": "course", "resource": "Tableau Desktop Specialist", "provider": "Tableau", "url": "https://www.tableau.com/learn/certification/desktop-specialist"}],
        "power bi": [{"type": "course", "resource": "Microsoft Power BI Data Analyst", "provider": "Microsoft Learn", "url": "https://learn.microsoft.com/en-us/certifications/power-bi-data-analyst-associate/"}],
        "excel": [{"type": "course", "resource": "Microsoft Excel - Excel from Beginner to Advanced", "provider": "Udemy", "url": "https://www.udemy.com/course/microsoft-excel-2013-from-beginner-to-advanced-and-beyond/"}],
        "cybersecurity": [{"type": "course", "resource": "Google Cybersecurity Certificate", "provider": "Coursera", "url": "https://www.coursera.org/professional-certificates/google-cybersecurity"}],
        "graphic design": [{"type": "course", "resource": "Graphic Design Specialization", "provider": "Coursera (CalArts)", "url": "https://www.coursera.org/specializations/graphic-design"}],
        "supply chain": [{"type": "course", "resource": "Supply Chain Management Specialization", "provider": "Coursera (Rutgers)", "url": "https://www.coursera.org/specializations/supply-chain-management"}],
        "erp": [{"type": "course", "resource": "SAP ERP Essential Training", "provider": "LinkedIn Learning", "url": "https://www.linkedin.com/learning/sap-erp-essential-training"}],
        "flask": [{"type": "course", "resource": "REST APIs with Flask and Python", "provider": "Udemy", "url": "https://www.udemy.com/course/rest-api-flask-and-python/"}],
        "postgresql": [{"type": "course", "resource": "The Complete SQL Bootcamp", "provider": "Udemy", "url": "https://www.udemy.com/course/the-complete-sql-bootcamp/"}],
        "node.js": [{"type": "course", "resource": "The Complete Node.js Developer Course", "provider": "Udemy", "url": "https://www.udemy.com/course/the-complete-nodejs-developer-course-2/"}],
        "java": [{"type": "course", "resource": "Java Programming Masterclass", "provider": "Udemy", "url": "https://www.udemy.com/course/java-the-complete-java-developer-course/"}],
        "accounting": [{"type": "course", "resource": "Accounting Fundamentals", "provider": "Coursera (University of Virginia)", "url": "https://www.coursera.org/learn/uva-darden-financial-accounting"}],
        "communication": [{"type": "course", "resource": "Improve Your English Communication Skills", "provider": "Coursera (Georgia Tech)", "url": "https://www.coursera.org/specializations/improve-english"}],
        "leadership": [{"type": "course", "resource": "Leading People and Teams Specialization", "provider": "Coursera (University of Michigan)", "url": "https://www.coursera.org/specializations/leading-teams"}],
    }

    import urllib.parse

    def _generated_extras(skill: str) -> list:
        yt_query = urllib.parse.quote_plus(f"{skill} tutorial for beginners")
        pdf_query = urllib.parse.quote_plus(f"{skill} filetype:pdf guide")
        return [
            {
                "type": "video",
                "resource": f"{skill.title()} — video tutorials",
                "provider": "YouTube",
                "url": f"https://www.youtube.com/results?search_query={yt_query}",
            },
            {
                "type": "pdf",
                "resource": f"{skill.title()} — PDF guides",
                "provider": "Google Search",
                "url": f"https://www.google.com/search?q={pdf_query}",
            },
        ]

    recommendations = []
    for skill in missing_skills:
        skill_lower = skill.lower().strip()

        curated = LEARNING_MAP.get(skill_lower)
        if not curated:
            for key in LEARNING_MAP:
                if key in skill_lower or skill_lower in key:
                    curated = LEARNING_MAP[key]
                    break

        resources = list(curated) if curated else [{
            "type": "course",
            "resource": f"Search for '{skill}' courses",
            "provider": "Coursera / Udemy / LinkedIn Learning",
            "url": f"https://www.coursera.org/search?query={urllib.parse.quote_plus(skill)}"
        }]

        resources.extend(_generated_extras(skill))

        for res in resources:
            recommendations.append({
                "skill": skill,
                "type": res["type"],
                "resource": res["resource"],
                "provider": res["provider"],
                "url": res["url"]
            })

    return recommendations


@matching_bp.get('/recommendations')
@jwt_required()
def get_recommendations():
    """
    Returns hybrid ranked recommendations for the logged-in student
    with XAI explanations and skill gap analysis.
    """
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()

    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    if not student.profile_embedding:
        return jsonify({
            "error": "Please upload your CV first to get recommendations"
        }), 400

    # Explicit ORDER BY gives a stable base ordering for the internships
    # list before ranking — without it, ties in match_score below could
    # appear in an arbitrary (and potentially different, request to
    # request) relative order, since SQL doesn't guarantee row order
    # absent an ORDER BY clause.
    internships = Internship.query.filter(
        Internship.is_active == True,
        or_(Internship.deadline.is_(None), Internship.deadline >= datetime.utcnow())
    ).order_by(Internship.id).all()

    if not internships:
        return jsonify({
            "student": student.full_name,
            "total_matches": 0,
            "recommendations": []
        }), 200

    # raw_text gives SBERT actual sentence-level CV context to compare
    # against the job description, instead of just a bag of skill
    # labels — this raises baseline semantic-similarity scores for
    # genuinely relevant matches, not just the skill-weighted portion
    # of the hybrid score.
    student_text = build_sbert_text(
        skills=student.skills or [],
        raw_text=student.raw_text or "",
        role=student.full_name or ""
    )

    results = []
    for job in internships:
        if not job.description_embedding:
            continue

        job_text = build_sbert_text(
            skills=job.required_skills or [],
            raw_text=job.description,
            role=job.title
        )

        skill_gap = compute_skill_gap(
            student_skills=student.skills or [],
            required_skills=job.required_skills or []
        )

        scores = compute_hybrid_score(
            student_text=student_text,
            job_text=job_text,
            skill_match_percentage=skill_gap["match_percentage"],
            sbert_embedding_student=student.profile_embedding,
            sbert_embedding_job=job.description_embedding,
        )

        learning = get_learning_recommendations(skill_gap["missing_skills"])

        results.append({
            "internship": job.to_dict(),
            "match_score": scores["hybrid_score"],
            "match_percentage": f"{round(scores['hybrid_score'] * 100, 1)}%",
            "score_breakdown": {
                "sbert_score": scores["sbert_score"],
                "tfidf_score": scores["tfidf_score"],
                "skill_score": scores["skill_score"],
                "hybrid_score": scores["hybrid_score"],
                "weights": scores["weights"]
            },
            "explanation": {
                "matched_skills": skill_gap["matched_skills"],
                "missing_skills": skill_gap["missing_skills"],
                "extra_skills": skill_gap["extra_skills"],
                "skill_match_percentage": skill_gap["match_percentage"],
                "skill_gap_percentage": skill_gap["gap_percentage"]
            },
            "learning_recommendations": learning
        })

    # Sort by hybrid match_score, with internship id as a deterministic
    # tiebreaker — otherwise two internships landing on the same (or
    # floating-point-identical) score could swap places between requests
    # depending on the internships list's incoming order.
    ranked = sorted(
        results,
        key=lambda x: (x["match_score"], x["internship"]["id"]),
        reverse=True
    )

    return jsonify({
        "student": student.full_name,
        "total_matches": len(ranked),
        "matching_method": f"Hybrid (SBERT={WEIGHT_SBERT}, TF-IDF={WEIGHT_TFIDF}, Skills={WEIGHT_SKILLS})",
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

    # A withdrawn application doesn't block reapplying — only an active
    # (non-withdrawn) one does.
    existing = Application.query.filter(
        Application.student_id == student.id,
        Application.internship_id == internship_id,
        Application.status != 'withdrawn'
    ).first()

    if existing:
        return jsonify({"error": "Already applied to this internship"}), 409

    # Validate required documents before touching the filesystem
    missing = []
    if internship.requires_cover_letter and not request.files.get('cover_letter'):
        missing.append('cover letter')
    if internship.requires_recommendation_letter and not request.files.get('recommendation_letter'):
        missing.append('recommendation letter')
    if missing:
        return jsonify({"error": f"This internship requires a {' and '.join(missing)}"}), 400

    cover_letter_path = _save_application_doc(request.files.get('cover_letter'), user_id, 'cover_letter')
    recommendation_letter_path = _save_application_doc(request.files.get('recommendation_letter'), user_id, 'recommendation_letter')

    score = 0.0
    if student.profile_embedding and internship.description_embedding:
        score = float(cosine_similarity(
            student.profile_embedding,
            internship.description_embedding
        ))

    application = Application(
        student_id=student.id,
        internship_id=internship_id,
        match_score=round(score, 4),
        cover_letter_path=cover_letter_path,
        recommendation_letter_path=recommendation_letter_path,
    )

    db.session.add(application)
    db.session.commit()

    return jsonify({
        "message": "Application submitted successfully",
        "application": application.to_dict(),
        "match_score": f"{round(score * 100, 1)}%"
    }), 201


@matching_bp.delete('/apply/<int:internship_id>')
@jwt_required()
def withdraw_application(internship_id):
    """Student withdraws an application they mistakenly submitted.
    Soft-deletes by marking status='withdrawn' rather than removing the
    row, so the employer's history and any feedback already given stays
    intact — and so the student can re-apply afterwards if they want to."""
    user_id = int(get_jwt_identity())
    student = Student.query.filter_by(user_id=user_id).first()

    if not student:
        return jsonify({"error": "Student profile not found"}), 404

    application = Application.query.filter(
        Application.student_id == student.id,
        Application.internship_id == internship_id,
        Application.status != 'withdrawn'
    ).first()

    if not application:
        return jsonify({"error": "Application not found"}), 404

    application.status = 'withdrawn'
    db.session.commit()

    return jsonify({"message": "Application withdrawn"}), 200


@matching_bp.get('/applications/documents/<path:filename>')
@jwt_required()
def serve_application_document(filename):
    """
    Serves an uploaded application document (cover letter, certificate,
    or recommendation letter). Follows the same storage convention as
    student CV files.
    """
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)


@matching_bp.get('/applicants/<int:internship_id>')
@jwt_required()
def get_applicants(internship_id):
    """Employer sees ranked applicants for their job"""
    applicants = Application.query.filter(
        Application.internship_id == internship_id,
        Application.status != 'withdrawn'
    ).order_by(Application.match_score.desc()).all()

    result = []
    for app in applicants:
        student = Student.query.get(app.student_id)
        internship = Internship.query.get(internship_id)

        required_skills = internship.required_skills if internship else []
        skill_gap = compute_skill_gap(
            student_skills=student.skills or [] if student else [],
            required_skills=required_skills or []
        )

        certificates = Certificate.query.filter_by(student_id=app.student_id) \
            .order_by(Certificate.uploaded_at.desc()).all() if student else []

        result.append({
            "application_id": app.id,
            "student": student.to_dict() if student else None,
            "match_score": app.match_score,
            "match_percentage": f"{round(app.match_score * 100, 1)}%",
            "status": app.status,
            "applied_at": app.applied_at.isoformat(),
            "skill_gap": skill_gap,
            "feedback_message": app.feedback_message,
            "interview_date": app.interview_date.isoformat() if app.interview_date else None,
            "start_date": app.start_date.isoformat() if app.start_date else None,
            "cover_letter_path": app.cover_letter_path,
            "certificate_path": app.certificate_path,
            "recommendation_letter_path": app.recommendation_letter_path,
            "certificates": [c.to_dict() for c in certificates],
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

        required_skills = internship.required_skills if internship else []
        skill_gap = compute_skill_gap(
            student_skills=student.skills or [],
            required_skills=required_skills or []
        )

        learning = get_learning_recommendations(skill_gap["missing_skills"])

        result.append({
            "id": app.id,
            "status": app.status,
            "match_score": app.match_score,
            "match_percentage": f"{round(app.match_score * 100, 1)}%" if app.match_score else None,
            "applied_at": app.applied_at.isoformat(),
            "internship": internship.to_dict() if internship else None,
            "skill_gap": skill_gap,
            "learning_recommendations": learning,
            "feedback_message": app.feedback_message,
            "interview_date": app.interview_date.isoformat() if app.interview_date else None,
            "start_date": app.start_date.isoformat() if app.start_date else None,
            "cover_letter_path": app.cover_letter_path,
            "certificate_path": app.certificate_path,
            "recommendation_letter_path": app.recommendation_letter_path,
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

    data, error = validate_request(
        UpdateApplicationStatusSchema(), request.get_json() or {}
    )
    if error:
        return jsonify(error), 400

    application.status = data['status']

    student = Student.query.get(application.student_id)
    if student:
        notification = Notification(
            user_id=student.user_id,
            type='status',
            message=f"Your application to {internship.title} at {employer.company_name} was {data['status']}.",
            application_id=application.id
        )
        db.session.add(notification)

    db.session.commit()

    return jsonify({
        "message": f"Application {data['status']}",
        "application": application.to_dict()
    }), 200


@matching_bp.patch('/applications/<int:application_id>/feedback')
@jwt_required()
def update_application_feedback(application_id):
    """Employer sends/updates feedback for an applicant, independent of status"""
    user_id = int(get_jwt_identity())
    employer = Employer.query.filter_by(user_id=user_id).first()

    if not employer:
        return jsonify({"error": "Employer profile not found"}), 404

    application = Application.query.get_or_404(application_id)
    internship = Internship.query.get(application.internship_id)

    if not internship or internship.employer_id != employer.id:
        return jsonify({"error": "Unauthorized"}), 403

    data, error = validate_request(
        UpdateApplicationFeedbackSchema(), request.get_json() or {}
    )
    if error:
        return jsonify(error), 400

    if 'feedback_message' in data:
        application.feedback_message = data['feedback_message']
    if 'interview_date' in data:
        application.interview_date = data['interview_date']
    if 'start_date' in data:
        application.start_date = data['start_date']

    # Build a readable notification out of whatever was actually set —
    # an employer might set only an interview date with no message text,
    # so fall back to a generic line rather than an empty notification.
    # Every feedback notification is prefixed with which internship and
    # company it's about, since the raw employer text alone (or the
    # generic fallback) never states that on its own.
    def _format_dt(value, fmt):
        # data values come through marshmallow as real datetime/date
        # objects, but fall back to plain str() if that's ever not
        # true rather than let notification creation crash.
        try:
            return value.strftime(fmt)
        except AttributeError:
            return str(value)

    student = Student.query.get(application.student_id)
    if student:
        parts = []
        if data.get('feedback_message'):
            parts.append(data['feedback_message'])
        if data.get('interview_date'):
            when = _format_dt(data['interview_date'], '%b %d, %Y at %I:%M %p')
            parts.append(f"An interview has been scheduled for {when}.")
        if data.get('start_date'):
            when = _format_dt(data['start_date'], '%b %d, %Y')
            parts.append(f"A start date has been proposed: {when}.")
        detail = " ".join(parts) or "You have a new update on your application."
        message = f"{internship.title} at {employer.company_name}: {detail}"

        notification = Notification(
            user_id=student.user_id,
            type='feedback',
            message=message,
            application_id=application.id
        )
        db.session.add(notification)

    db.session.commit()

    return jsonify({
        "message": "Feedback saved",
        "application": application.to_dict()
    }), 200
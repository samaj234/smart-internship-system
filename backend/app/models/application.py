from app import db
from datetime import datetime

class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    internship_id = db.Column(db.Integer, db.ForeignKey('internships.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/accepted/rejected
    match_score = db.Column(db.Float)            # SBERT cosine similarity score
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    feedback_message = db.Column(db.Text)
    interview_date = db.Column(db.DateTime)
    start_date = db.Column(db.Date)
    cover_letter_path = db.Column(db.String(255))
    certificate_path = db.Column(db.String(255))
    recommendation_letter_path = db.Column(db.String(255))

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "internship_id": self.internship_id,
            "status": self.status,
            "match_score": self.match_score,
            "applied_at": self.applied_at.isoformat(),
            "cover_letter_path": self.cover_letter_path,
            "certificate_path": self.certificate_path,
            "recommendation_letter_path": self.recommendation_letter_path,
        }
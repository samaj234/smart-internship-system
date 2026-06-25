from app import db
from datetime import datetime

class Internship(db.Model):
    __tablename__ = 'internships'

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employers.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.JSON)        # ["Python", "SQL", ...]
    location = db.Column(db.String(100))
    duration = db.Column(db.String(50))          # e.g. "3 months"
    stipend = db.Column(db.String(50))           # e.g. "GHS 500/month"
    deadline = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    description_embedding = db.Column(db.JSON)   # SBERT vector stored as list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    applications = db.relationship('Application', backref='internship')

    def to_dict(self):
        return {
            "id": self.id,
            "employer_id": self.employer_id,
            "title": self.title,
            "description": self.description,
            "required_skills": self.required_skills,
            "location": self.location,
            "duration": self.duration,
            "stipend": self.stipend,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "is_active": self.is_active,
        }
    
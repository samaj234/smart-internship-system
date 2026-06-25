from app import db
from datetime import datetime

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    university = db.Column(db.String(150))
    degree = db.Column(db.String(100))
    gpa = db.Column(db.Float)
    skills = db.Column(db.JSON)               # ["Python", "React", ...]
    cv_path = db.Column(db.String(255))        # path to uploaded CV file
    profile_embedding = db.Column(db.JSON)     # SBERT vector stored as list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    applications = db.relationship('Application', backref='student')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "full_name": self.full_name,
            "phone": self.phone,
            "university": self.university,
            "degree": self.degree,
            "gpa": self.gpa,
            "skills": self.skills,
            "cv_path": self.cv_path,
        }
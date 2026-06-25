from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'employer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False)
    employer_profile = db.relationship('Employer', backref='user', uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat()
        }
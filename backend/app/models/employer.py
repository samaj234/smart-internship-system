from app import db
from datetime import datetime

class Employer(db.Model):
    __tablename__ = 'employers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    industry = db.Column(db.String(100))
    location = db.Column(db.String(100))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    internships = db.relationship('Internship', backref='employer')

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "industry": self.industry,
            "location": self.location,
            "website": self.website,
            "description": self.description,
        }
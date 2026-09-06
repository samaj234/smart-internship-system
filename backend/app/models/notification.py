from app import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'status' or 'feedback'
    message = db.Column(db.Text, nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "message": self.message,
            "application_id": self.application_id,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat()
        }
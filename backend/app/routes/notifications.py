from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Notification

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.get('/')
@jwt_required()
def get_notifications():
    user_id = int(get_jwt_identity())
    notifications = Notification.query.filter_by(user_id=user_id) \
        .order_by(Notification.created_at.desc()).all()
    return jsonify({"notifications": [n.to_dict() for n in notifications]}), 200


@notifications_bp.get('/unread-count')
@jwt_required()
def get_unread_count():
    user_id = int(get_jwt_identity())
    count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({"unread_count": count}), 200


@notifications_bp.patch('/<int:notification_id>/read')
@jwt_required()
def mark_read(notification_id):
    user_id = int(get_jwt_identity())
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    notification.is_read = True
    db.session.commit()
    return jsonify({"message": "Marked as read"}), 200


@notifications_bp.patch('/read-all')
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "All notifications marked as read"}), 200


@notifications_bp.delete('/<int:notification_id>')
@jwt_required()
def delete_notification(notification_id):
    user_id = int(get_jwt_identity())
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    db.session.delete(notification)
    db.session.commit()
    return jsonify({"message": "Notification deleted"}), 200


@notifications_bp.delete('/')
@jwt_required()
def delete_all_notifications():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({"message": "All notifications cleared"}), 200
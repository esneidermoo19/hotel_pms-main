from app import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False)
    username = db.Column(db.String(80), nullable=True)
    success = db.Column(db.Boolean, default=False)
    details = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<AuditLog {self.event_type} - {self.ip_address} - {'Success' if self.success else 'Failed'}>"

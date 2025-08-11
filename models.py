from app import db
from datetime import datetime
from sqlalchemy import func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # User preferences
    location_sharing = db.Column(db.Boolean, default=True)
    sos_enabled = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            'location_sharing': self.location_sharing,
            'sos_enabled': self.sos_enabled,
            'created_at': self.created_at.isoformat()
        }

class CrimeData(db.Model):
    __tablename__ = 'crime_data'
    
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    crime_type = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    severity = db.Column(db.Integer, nullable=False, default=1)  # 1-5 scale
    area_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<CrimeData {self.crime_type} at ({self.latitude}, {self.longitude})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'crime_type': self.crime_type,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity,
            'area_name': self.area_name,
            'description': self.description
        }

class SafeRoute(db.Model):
    __tablename__ = 'safe_routes'
    
    id = db.Column(db.Integer, primary_key=True)
    start_lat = db.Column(db.Float, nullable=False)
    start_lng = db.Column(db.Float, nullable=False)
    end_lat = db.Column(db.Float, nullable=False)
    end_lng = db.Column(db.Float, nullable=False)
    route_points = db.Column(db.Text)  # JSON string of route coordinates
    risk_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'start_lat': self.start_lat,
            'start_lng': self.start_lng,
            'end_lat': self.end_lat,
            'end_lng': self.end_lng,
            'route_points': self.route_points,
            'risk_score': self.risk_score,
            'created_at': self.created_at.isoformat()
        }

class SOSAlert(db.Model):
    __tablename__ = 'sos_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, resolved, false_alarm
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('sos_alerts', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

class SafePlace(db.Model):
    __tablename__ = 'safe_places'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    place_type = db.Column(db.String(50), nullable=False)  # police_station, hospital, fire_station, etc.
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    hours = db.Column(db.String(100))
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'place_type': self.place_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'phone': self.phone,
            'hours': self.hours,
            'verified': self.verified,
            'created_at': self.created_at.isoformat()
        }

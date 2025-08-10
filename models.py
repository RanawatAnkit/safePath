from app import db
from datetime import datetime
from sqlalchemy import func

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

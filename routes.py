import json
import os

from werkzeug.utils import secure_filename
import logging
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
import requests
from app import app, db
from models import CrimeData, SafeRoute, User, SOSAlert, SafePlace
from crime_predictor import crime_predictor
import numpy as np
import math
from twilio.rest import Client

ACCOUNT_SID = "ACdc27b89880dc60cfbf4f53bc18c6dcda"  # Your Account SID from Twilio
AUTH_TOKEN = "f28770e1ac335eea85cb02316b86156c"    # Your Auth Token from Twilio
TWILIO_PHONE_NUMBER = "+12182202974" 
client = Client(ACCOUNT_SID, AUTH_TOKEN)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/login')
def login():
    """Login page"""
    if current_user.is_authenticated:
        print("alredy login")
        return redirect(url_for('index'))
    return render_template('auth/login.html')

@app.route('/register')
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('auth/register.html')

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html')

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login API endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password are required'}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            return jsonify({
                'success': True,
                'message': 'Logged in successfully',
                'user': user.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Registration API endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone')
        emergency_contact = data.get('emergency_contact')
        emergency_phone = data.get('emergency_phone')
        
        # Validate required fields
        if not all([username, email, password]):
            return jsonify({'success': False, 'error': 'Username, email, and password are required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
            
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=username,
            email=email,
            phone=phone,
            emergency_contact=emergency_contact,
            emergency_phone=emergency_phone
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user, remember=True)
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Registration error: {e}")
        return jsonify({'success': False, 'error': 'Registration failed'}), 500

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    """Logout API endpoint"""
    logout_user()
    return render_template("index.html")

@app.route('/api/auth/status')
def auth_status():
    """Check if the user is logged in and return their info"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        })
    else:
        return jsonify({
            'authenticated': False,
            'user': None
        })
    
@app.route('/api/auth/get_current_user')
def get_current_user():
    if current_user.is_authenticated:
        return jsonify({
            'is_authenticated': True,
            'user':current_user.to_dict()
        })
    else:
        return jsonify({'is_authenticated': False})

@app.route('/api/current-location-risk', methods=['POST'])
def get_current_location_risk():
    """Get crime risk assessment for current location"""
    try:
        data = request.get_json()
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        
        # Get crime risk prediction
        risk_score = crime_predictor.predict_crime_risk(latitude, longitude)
        
        # Get area crime statistics
        crime_stats = crime_predictor.get_area_crime_stats(latitude, longitude)
        
        # Determine risk level
        risk_level = "Low"
        if risk_score >= 7:
            risk_level = "High"
        elif risk_score >= 4:
            risk_level = "Medium"
        
        return jsonify({
            'success': True,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'crime_stats': crime_stats
        })
        
    except Exception as e:
        logging.error(f"Error getting location risk: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to assess location risk'
        }), 500

@app.route('/api/crime-data')
def get_crime_data():
    """Get crime data for map visualization"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 500, type=int)
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', 10, type=float)  # km
        
        query = CrimeData.query
        
        # Filter by location if provided
        if lat and lng:
            lat_delta = radius / 111.0
            lng_delta = radius / (111.0 * np.cos(np.radians(lat)))
            
            query = query.filter(
                CrimeData.latitude.between(lat - lat_delta, lat + lat_delta),
                CrimeData.longitude.between(lng - lng_delta, lng + lng_delta)
            )
        
        # Get recent crimes first
        crimes = query.order_by(CrimeData.timestamp.desc()).limit(limit).all()
        
        # Convert to JSON
        crime_data = [crime.to_dict() for crime in crimes]
        
        return jsonify({
            'success': True,
            'crimes': crime_data,
            'total': len(crime_data)
        })
        
    except Exception as e:
        logging.error(f"Error getting crime data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch crime data'
        }), 500

@app.route('/api/safe-route', methods=['POST'])
def get_safe_route():
    """Calculate safe route between two points"""
    try:
        data = request.get_json()
        start_lat = float(data.get('start_lat'))
        start_lng = float(data.get('start_lng'))
        end_lat = float(data.get('end_lat'))
        end_lng = float(data.get('end_lng'))
        
        # Simple safe routing algorithm
        route_points = calculate_safe_route(start_lat, start_lng, end_lat, end_lng)
        
        # Calculate overall risk score for the route
        total_risk = 0
        for point in route_points:
            risk = crime_predictor.predict_crime_risk(point['lat'], point['lng'])
            total_risk += risk
        
        avg_risk = total_risk / len(route_points) if route_points else 5.0
        
        # Save route to database
        safe_route = SafeRoute(
            start_lat=start_lat,
            start_lng=start_lng,
            end_lat=end_lat,
            end_lng=end_lng,
            route_points=json.dumps(route_points),
            risk_score=avg_risk
        )
        
        db.session.add(safe_route)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'route_points': route_points,
            'risk_score': round(avg_risk, 2),
            'distance_km': calculate_route_distance(route_points)
        })
        
    except Exception as e:
        logging.error(f"Error calculating safe route: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to calculate safe route'
        }), 500

@app.route('/api/crime-stats')
def get_crime_statistics():
    """Get overall crime statistics"""
    try:
        # Get total crimes by type
        crime_type_stats = db.session.query(
            CrimeData.crime_type,
            db.func.count(CrimeData.id).label('count'),
            db.func.avg(CrimeData.severity).label('avg_severity')
        ).group_by(CrimeData.crime_type).all()
        
        # Get crimes by time of day
        hourly_stats = db.session.query(
            db.func.extract('hour', CrimeData.timestamp).label('hour'),
            db.func.count(CrimeData.id).label('count')
        ).group_by(db.func.extract('hour', CrimeData.timestamp)).all()
        
        # Get recent crime trend (last 30 days)
        recent_date = datetime.now() - timedelta(days=30)
        recent_crimes = CrimeData.query.filter(
            CrimeData.timestamp > recent_date
        ).count()
        
        total_crimes = CrimeData.query.count()
        print(total_crimes,recent_crimes)
        return jsonify({
            'success': True,
            'total_crimes': total_crimes,
            'recent_crimes': recent_crimes,
            'crime_types': [
                {
                    'type': stat.crime_type,
                    'count': stat.count,
                    'avg_severity': round(stat.avg_severity, 2)
                }
                for stat in crime_type_stats
            ],
            'hourly_distribution': [
                {
                    'hour': int(stat.hour),
                    'count': stat.count
                }
                for stat in hourly_stats
            ]
        })
        
    except Exception as e:
        logging.error(f"Error getting crime statistics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch crime statistics'
        }), 500

def calculate_safe_route(start_lat, start_lng, end_lat, end_lng):
    """Calculate a safe route avoiding high-crime areas"""
    try:
        # Simple routing algorithm - create waypoints and avoid high-crime areas
        route_points = []
        
        # Number of intermediate points
        num_points = 10
        
        for i in range(num_points + 1):
            progress = i / num_points
            
            # Linear interpolation between start and end
            lat = start_lat + (end_lat - start_lat) * progress
            lng = start_lng + (end_lng - start_lng) * progress
            
            # Check if this point is in a high-crime area
            risk_score = crime_predictor.predict_crime_risk(lat, lng)
            
            # If high risk, try to find a safer alternative nearby
            if risk_score > 7 and i > 0 and i < num_points:
                # Try some alternative points in a small radius
                best_lat, best_lng = lat, lng
                best_risk = risk_score
                
                for offset in [0.001, -0.001]:  # Small offset (~100m)
                    for alt_lat in [lat + offset, lat]:
                        for alt_lng in [lng + offset, lng]:
                            alt_risk = crime_predictor.predict_crime_risk(alt_lat, alt_lng)
                            if alt_risk < best_risk:
                                best_lat, best_lng = alt_lat, alt_lng
                                best_risk = alt_risk
                
                lat, lng = best_lat, best_lng
            
            route_points.append({
                'lat': round(lat, 6),
                'lng': round(lng, 6),
                'risk_score': round(crime_predictor.predict_crime_risk(lat, lng), 2)
            })
        
        return route_points
        
    except Exception as e:
        logging.error(f"Error calculating safe route: {e}")
        # Return simple direct route as fallback
        return [
            {'lat': start_lat, 'lng': start_lng, 'risk_score': 5.0},
            {'lat': end_lat, 'lng': end_lng, 'risk_score': 5.0}
        ]

def calculate_route_distance(route_points):
    """Calculate total distance of route in kilometers"""
    if len(route_points) < 2:
        return 0
    
    total_distance = 0
    for i in range(1, len(route_points)):
        # Haversine formula for distance between two points
        lat1, lng1 = route_points[i-1]['lat'], route_points[i-1]['lng']
        lat2, lng2 = route_points[i]['lat'], route_points[i]['lng']
        
        dlat = np.radians(lat2 - lat1)
        dlng = np.radians(lng2 - lng1)
        
        a = (np.sin(dlat/2)**2 + 
             np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlng/2)**2)
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        # Earth's radius in kilometers
        distance = 6371 * c
        total_distance += distance
    
    return round(total_distance, 2)

# SOS and Safe Places APIs
@app.route('/api/sos/alert', methods=['POST'])
@login_required
def create_sos_alert():
    """Create an SOS alert"""
    try:
        data = request.get_json()
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        message_text = data.get('message', 'Emergency help needed!')
        number = data.get('number', '').strip()

        # Ensure phone number is in proper format
        if not number.startswith('+'):
            number = f'+91{number}'

        print(data)

        # Send SOS SMS via Twilio
        twilio_message = client.messages.create(
            to=number,
            from_=TWILIO_PHONE_NUMBER,
            body=f"{message_text}\nLocation: https://www.google.com/maps?q={latitude},{longitude}"
        )

        # ✅ Store only Twilio message SID (string) in DB
        sos_alert = SOSAlert(
            user_id=current_user.id,
            latitude=latitude,
            longitude=longitude,
            message=twilio_message.sid,   # <-- Fix here
            status='active'
        )

        db.session.add(sos_alert)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'SOS alert sent successfully',
            'alert': sos_alert.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating SOS alert: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating SOS alert: {e}")
        return jsonify({'success': False, 'error': 'Failed to send SOS alert'}), 500

@app.route('/api/sos/alerts')
@login_required
def get_user_sos_alerts():
    """Get user's SOS alerts"""
    try:
        alerts = SOSAlert.query.filter_by(user_id=current_user.id).order_by(SOSAlert.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts]
        })
        
    except Exception as e:
        logging.error(f"Error getting SOS alerts: {e}")
        return jsonify({'success': False, 'error': 'Failed to get SOS alerts'}), 500

@app.route('/api/sos/alert/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_sos_alert(alert_id):
    """Resolve an SOS alert"""
    try:
        alert = SOSAlert.query.filter_by(id=alert_id, user_id=current_user.id).first()
        
        if not alert:
            return jsonify({'success': False, 'error': 'Alert not found'}), 404
        
        alert.status = 'resolved'
        alert.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'SOS alert resolved',
            'alert': alert.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error resolving SOS alert: {e}")
        return jsonify({'success': False, 'error': 'Failed to resolve SOS alert'}), 500

@app.route('/api/safe-places')
def get_safe_places():
    """Get safe places around a location"""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', 5, type=float)  # km
        place_type = request.args.get('type')  # optional filter
        limit = request.args.get('limit', 50, type=int)
        
        query = SafePlace.query
        
        # Filter by location if provided
        if lat and lng:
            lat_delta = radius / 111.0
            lng_delta = radius / (111.0 * np.cos(np.radians(lat)))
            
            query = query.filter(
                SafePlace.latitude.between(lat - lat_delta, lat + lat_delta),
                SafePlace.longitude.between(lng - lng_delta, lng + lng_delta)
            )
        
        # Filter by place type if provided
        if place_type:
            query = query.filter_by(place_type=place_type)
        
        # Prioritize verified places and order by creation date
        safe_places = query.order_by(SafePlace.verified.desc(), SafePlace.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'places': [place.to_dict() for place in safe_places],
            'total': len(safe_places)
        })
        
    except Exception as e:
        logging.error(f"Error getting safe places: {e}")
        return jsonify({'success': False, 'error': 'Failed to get safe places'}), 500

@app.route('/api/safe-places/types')
def get_safe_place_types():
    """Get available safe place types"""
    types = [
        {'value': 'police_station', 'label': 'Police Stations', 'icon': 'fas fa-shield-alt'},
        {'value': 'hospital', 'label': 'Hospitals', 'icon': 'fas fa-hospital'},
        {'value': 'fire_station', 'label': 'Fire Stations', 'icon': 'fas fa-fire-extinguisher'},
        {'value': 'government_office', 'label': 'Government Offices', 'icon': 'fas fa-university'},
        {'value': 'bank', 'label': 'Banks', 'icon': 'fas fa-university'},
        {'value': 'school', 'label': 'Schools', 'icon': 'fas fa-school'}
    ]
    
    return jsonify({
        'success': True,
        'types': types
    })

def haversine(coord1, coord2):
    R = 6371000  # radius of Earth in meters
    lat1, lon1 = math.radians(coord1[1]), math.radians(coord1[0])
    lat2, lon2 = math.radians(coord2[1]), math.radians(coord2[0])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Calculate risk for a single point
def calculate_point_risk(point, crimes, radius=200):
    risk = 0
    for crime in crimes:
        distance = haversine(point, [crime['lon'], crime['lat']])
        if distance <= radius:
            risk += crime['weight'] / (distance + 1)
    return risk

# Calculate risk for a route
def calculate_route_risk(route_geometry, crimes):
    points = route_geometry['coordinates']
    total_risk = 0
    for point in points:
        total_risk += calculate_point_risk(point, crimes)
    return total_risk / len(points) if points else 0

@app.route('/get_routes', methods=['POST'])
def get_routes():
    data = request.json
    start = data['srcLatLng']  # [lat, lon]
    end = data['destLatLng']      # [lat, lon]

    # ✅ Load crime data from DB
    crimes = []
    with app.app_context():
        crime_records = CrimeData.query.all()
        for c in crime_records:
            crimes.append({
                "lat": c.latitude,
                "lon": c.longitude,
                "weight": c.severity  # use severity as risk weight
            })
    print(start,end)
    # OSRM route request (public demo server)
    url = f"http://router.project-osrm.org/route/v1/driving/{start['lng']},{start['lat']};{end['lng']},{end['lat']}?overview=full&geometries=geojson&alternatives=true"

    response = requests.get(url).json()

    routes = []
    for r in response['routes']:
        risk = calculate_route_risk(r['geometry'], crimes)
        if risk==0.00448984908395163:
            risk==100
        print("risk")
        print(risk)
        routes.append({
            'geometry': r['geometry'],
            'duration': r['duration'],
            'distance': r['distance'],
            'risk': risk
        })
    print(routes)
    return jsonify(routes)
    
'''def add_crime_record(latitude, longitude, crime_type, timestamp, severity, area_name, description):
    """Add a new crime record to the database"""

    try:
        # Convert timestamp to datetime if it's a string
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)

        crime = CrimeData(
            latitude=latitude,
            longitude=longitude,
            crime_type=crime_type,
            timestamp=timestamp,
            severity=int(severity),
            area_name=area_name,
            description=description
        )

        db.session.add(crime)
        db.session.commit()

        logging.info(f"Crime record added successfully: {crime}")
        return True

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding crime record: {e}")
        return False
'''

from datetime import timedelta

#<------------------------------------New changes from Here---------------------------------------->
# Add this route to your routes.py file

@app.route('/api/report-crime', methods=['POST'])
def report_crime():
    """Handle user crime report submission"""
    try:
        # Get form data
        crime_type = request.form.get('crimeType')
        description = request.form.get('description')
        location = request.form.get('location')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        # Validate required fields
        if not all([crime_type, description, location, latitude, longitude]):
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400
        
        # Convert coordinates to float
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid coordinates'
            }), 400
        
        # Handle file upload
        evidence_file_path = None
        if 'evidence' in request.files:
            file = request.files['evidence']
            
            if file and file.filename:
                # Secure the filename
                filename = secure_filename(file.filename)
                
                # Add timestamp to filename to make it unique
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                name, ext = os.path.splitext(filename)
                unique_filename = f"{name}_{timestamp}{ext}"
                
                # Ensure upload directory exists
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Save the file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # Store relative path
                evidence_file_path = f"evidence/{unique_filename}"
        
        # Map crime type to severity (you can adjust this mapping)
        severity_mapping = {
            'Assault': 4,
            'Cyber Crime': 3,
            'Drug Abuse': 3,
            'Fraud': 3,
            'Murder': 5,
            'Robbery': 4,
            'Theft': 2,
            'Vandalism': 2
        }
        
        severity = severity_mapping.get(crime_type, 3)  # Default to 3 if not found
        
        # Create new crime report
        crime_report = CrimeData(
            latitude=latitude,
            longitude=longitude,
            crime_type=crime_type,
            description=description,
            area_name=location,
            severity=severity,
            evidence_file=evidence_file_path,
            is_user_report=True,
            verified=False,
            reported_by=current_user.id if current_user.is_authenticated else None,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(crime_report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Crime report submitted successfully',
            'report_id': crime_report.id,
            'crime_data': crime_report.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error submitting crime report: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit crime report'
        }), 500

# Optional: Route to get user's submitted reports
@app.route('/api/my-reports')
@login_required
def get_my_reports():
    """Get current user's crime reports"""
    try:
        reports = CrimeData.query.filter_by(
            reported_by=current_user.id,
            is_user_report=True
        ).order_by(CrimeData.timestamp.desc()).all()
        
        return jsonify({
            'success': True,
            'reports': [report.to_dict() for report in reports],
            'total': len(reports)
        })
        
    except Exception as e:
        logging.error(f"Error getting user reports: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get reports'
        }), 500
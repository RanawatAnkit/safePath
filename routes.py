import json
import logging
from datetime import datetime
from flask import render_template, request, jsonify
from app import app, db
from models import CrimeData, SafeRoute
from crime_predictor import crime_predictor
import numpy as np

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

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

from datetime import timedelta

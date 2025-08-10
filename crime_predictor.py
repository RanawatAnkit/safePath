import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
import joblib
import os
import logging
from app import db
from models import CrimeData

class CrimePredictor:
    def __init__(self):
        self.model = None
        self.crime_type_encoder = LabelEncoder()
        self.is_trained = False
        self.model_path = 'crime_model.pkl'
        self.encoder_path = 'crime_encoder.pkl'
        
    def prepare_features(self, data):
        """Prepare features for the ML model"""
        features = []
        
        for _, row in data.iterrows():
            timestamp = pd.to_datetime(row['timestamp'])
            
            feature_vector = [
                row['latitude'],
                row['longitude'],
                timestamp.hour,
                timestamp.dayofweek,
                timestamp.month,
                timestamp.day,
                row['crime_type_encoded'],
                row['severity']
            ]
            features.append(feature_vector)
            
        return np.array(features)
    
    def train_model(self):
        """Train the crime prediction model"""
        try:
            # Fetch crime data from database
            crimes = CrimeData.query.all()
            if not crimes:
                logging.warning("No crime data available for training")
                return False
            
            # Convert to DataFrame
            data = []
            for crime in crimes:
                data.append({
                    'latitude': crime.latitude,
                    'longitude': crime.longitude,
                    'timestamp': crime.timestamp,
                    'crime_type': crime.crime_type,
                    'severity': crime.severity
                })
            
            df = pd.DataFrame(data)
            
            # Encode crime types
            df['crime_type_encoded'] = self.crime_type_encoder.fit_transform(df['crime_type'])
            
            # Prepare features
            X = self.prepare_features(df)
            
            # Create target variable (risk score based on frequency and severity)
            # Group by location (rounded to 3 decimal places) and calculate risk
            df['lat_rounded'] = df['latitude'].round(3)
            df['lng_rounded'] = df['longitude'].round(3)
            
            location_risk = df.groupby(['lat_rounded', 'lng_rounded']).agg({
                'severity': 'mean',
                'crime_type': 'count'
            }).reset_index()
            
            # Normalize risk score (0-10 scale)
            location_risk['risk_score'] = (
                location_risk['severity'] * 0.7 + 
                (location_risk['crime_type'] / location_risk['crime_type'].max()) * 10 * 0.3
            )
            
            # Map risk scores back to original data
            df = df.merge(
                location_risk[['lat_rounded', 'lng_rounded', 'risk_score']], 
                on=['lat_rounded', 'lng_rounded'], 
                how='left'
            )
            
            y = df['risk_score'].values
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train model
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(X_train, y_train)
            
            # Save model
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.crime_type_encoder, self.encoder_path)
            
            # Test accuracy
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            logging.info(f"Model trained successfully. Train score: {train_score:.3f}, Test score: {test_score:.3f}")
            
            self.is_trained = True
            return True
            
        except Exception as e:
            logging.error(f"Error training model: {e}")
            return False
    
    def load_model(self):
        """Load pre-trained model"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.encoder_path):
                self.model = joblib.load(self.model_path)
                self.crime_type_encoder = joblib.load(self.encoder_path)
                self.is_trained = True
                logging.info("Model loaded successfully")
                return True
            return False
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            return False
    
    def predict_crime_risk(self, latitude, longitude, time_of_day=None):
        """Predict crime risk for a given location and time"""
        if not self.is_trained:
            if not self.load_model():
                if not self.train_model():
                    return 5.0  # Default medium risk if model fails
        
        try:
            # Use current time if not provided
            if time_of_day is None:
                time_of_day = datetime.now()
            
            # Use most common crime type for prediction
            most_common_crime = 'Theft'
            crime_type_encoded = 0
            
            try:
                crime_type_encoded = self.crime_type_encoder.transform([most_common_crime])[0]
            except:
                crime_type_encoded = 0
            
            # Prepare feature vector
            features = np.array([[
                latitude,
                longitude,
                time_of_day.hour,
                time_of_day.weekday(),
                time_of_day.month,
                time_of_day.day,
                crime_type_encoded,
                3  # Average severity
            ]])
            
            # Predict risk
            risk_score = self.model.predict(features)[0]
            
            # Ensure risk score is within bounds
            risk_score = max(0, min(10, risk_score))
            
            return round(risk_score, 2)
            
        except Exception as e:
            logging.error(f"Error predicting crime risk: {e}")
            return 5.0  # Default medium risk
    
    def get_area_crime_stats(self, latitude, longitude, radius_km=1):
        """Get crime statistics for an area around the given coordinates"""
        try:
            # Calculate coordinate bounds for the radius
            lat_delta = radius_km / 111.0  # Roughly 1 degree = 111 km
            lng_delta = radius_km / (111.0 * np.cos(np.radians(latitude)))
            
            # Query crimes within the area
            crimes = CrimeData.query.filter(
                CrimeData.latitude.between(latitude - lat_delta, latitude + lat_delta),
                CrimeData.longitude.between(longitude - lng_delta, longitude + lng_delta)
            ).all()
            
            if not crimes:
                return {
                    'total_crimes': 0,
                    'crime_types': {},
                    'avg_severity': 0,
                    'recent_crimes': 0
                }
            
            # Calculate statistics
            crime_types = {}
            severities = []
            recent_crimes = 0
            recent_date = datetime.now() - timedelta(days=30)
            
            for crime in crimes:
                # Count crime types
                if crime.crime_type not in crime_types:
                    crime_types[crime.crime_type] = 0
                crime_types[crime.crime_type] += 1
                
                # Collect severities
                severities.append(crime.severity)
                
                # Count recent crimes
                if crime.timestamp > recent_date:
                    recent_crimes += 1
            
            return {
                'total_crimes': len(crimes),
                'crime_types': crime_types,
                'avg_severity': round(np.mean(severities), 2) if severities else 0,
                'recent_crimes': recent_crimes
            }
            
        except Exception as e:
            logging.error(f"Error getting area crime stats: {e}")
            return {
                'total_crimes': 0,
                'crime_types': {},
                'avg_severity': 0,
                'recent_crimes': 0
            }

# Global predictor instance
crime_predictor = CrimePredictor()

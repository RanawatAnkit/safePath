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

    # -----------------------------
    # Train Model
    # -----------------------------
    def train_model(self):
        """Train the crime prediction model"""
        try:
            crimes = CrimeData.query.all()
            if not crimes:
                logging.warning("No crime data available for training")
                return False
            
            # Convert to DataFrame
            data = [{
                'latitude': c.latitude,
                'longitude': c.longitude,
                'timestamp': c.timestamp,
                'crime_type': c.crime_type,
                'severity': c.severity
            } for c in crimes]

            df = pd.DataFrame(data)

            # Encode crime types
            df['crime_type_encoded'] = self.crime_type_encoder.fit_transform(df['crime_type'])

            # Prepare features
            X = self.prepare_features(df)

            # Create target variable (risk score)
            df['lat_rounded'] = df['latitude'].round(3)
            df['lng_rounded'] = df['longitude'].round(3)

            location_risk = df.groupby(['lat_rounded', 'lng_rounded']).agg({
                'severity': 'mean',
                'crime_type': 'count'
            }).reset_index()

            # Normalize risk (0-10 scale)
            location_risk['risk_score'] = (
                location_risk['severity'] * 0.7 +
                (location_risk['crime_type'] / location_risk['crime_type'].max()) * 10 * 0.3
            )

            # Map back to df
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

            # Log performance
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            logging.info(f"Model trained. Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")

            self.is_trained = True
            return True

        except Exception as e:
            logging.error(f"Error training model: {e}")
            return False

    # -----------------------------
    # Load Model
    # -----------------------------
    def load_model(self):
        """Load pre-trained model"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.encoder_path):
                self.model = joblib.load(self.model_path)
                self.crime_type_encoder = joblib.load(self.encoder_path)
                self.is_trained = True
                logging.info("Crime risk model loaded successfully")
                return True
            return False
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            return False

    # -----------------------------
    # Area Stats Helper
    # -----------------------------
    def get_area_crime_stats(self, latitude, longitude, radius_km=1):
        """Get crime statistics around given coordinates"""
        try:
            lat_delta = radius_km / 111.0
            lng_delta = radius_km / (111.0 * np.cos(np.radians(latitude)))

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

            crime_types = {}
            severities = []
            recent_crimes = 0
            recent_date = datetime.now() - timedelta(days=30)

            for crime in crimes:
                crime_types[crime.crime_type] = crime_types.get(crime.crime_type, 0) + 1
                severities.append(crime.severity)
                if crime.timestamp > recent_date:
                    recent_crimes += 1

            avg_severity = np.mean(severities) if severities else 0

            return {
                'total_crimes': len(crimes),
                'crime_types': crime_types,
                'avg_severity': round(avg_severity, 2),
                'recent_crimes': recent_crimes
            }

        except Exception as e:
            logging.error(f"Error getting area crime stats: {e}")
            return {'total_crimes': 0, 'crime_types': {}, 'avg_severity': 0, 'recent_crimes': 0}

    # -----------------------------
    # Predict Risk
    # -----------------------------
    def predict_crime_risk(self, latitude, longitude, time_of_day=None):
        """Predict crime risk for a given location and time"""
        if not self.is_trained:
            if not self.load_model():
                if not self.train_model():
                    return 5.0  # default medium risk

        try:
            if time_of_day is None:
                time_of_day = datetime.now()

            # Get local crime context
            area_stats = self.get_area_crime_stats(latitude, longitude, radius_km=1)
            avg_severity = area_stats['avg_severity']
            total_crimes = area_stats['total_crimes']
            recent_crimes = area_stats['recent_crimes']

            # Use real most common crime
            if area_stats['crime_types']:
                most_common_crime = max(area_stats['crime_types'], key=area_stats['crime_types'].get)
            else:
                most_common_crime = 'Theft'

            try:
                crime_type_encoded = self.crime_type_encoder.transform([most_common_crime])[0]
            except:
                crime_type_encoded = 0

            # Prepare feature vector (now meaningful!)
            features = np.array([[
                latitude,
                longitude,
                time_of_day.hour,
                time_of_day.weekday(),
                time_of_day.month,
                time_of_day.day,
                crime_type_encoded,
                avg_severity
            ]])

            # Predict risk
            risk_score = float(self.model.predict(features)[0])
            risk_score = max(0, min(10, risk_score))
            return round(risk_score, 2)

        except Exception as e:
            logging.error(f"Error predicting crime risk: {e}")
            return 5.0
    
    def get_area_crime_stats(self, latitude, longitude, radius_km=1):
        """Get crime statistics for an area around the given coordinates"""
        try:
            lat_delta = radius_km / 111.0
            lng_delta = radius_km / (111.0 * np.cos(np.radians(latitude)))

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

            crime_stats = {}
            severities = []
            recent_crimes = 0
            recent_date = datetime.now() - timedelta(days=30)

            for crime in crimes:
                ctype = crime.crime_type
                if ctype not in crime_stats:
                    crime_stats[ctype] = {'count': 0, 'total_severity': 0}
                crime_stats[ctype]['count'] += 1
                crime_stats[ctype]['total_severity'] += crime.severity
                severities.append(crime.severity)

                if crime.timestamp > recent_date:
                    recent_crimes += 1

            # Weighted logic: emphasize severe crimes and frequency
            total_crimes = sum(data['count'] for data in crime_stats.values())
            max_severity = max(severities) if severities else 0
            mean_severity = np.mean(severities) if severities else 0

            # Adjusted severity = 70% mean + 30% max influence + crime frequency scaling
            adjusted_severity = (0.7 * mean_severity + 0.3 * max_severity)
            adjusted_severity += min(total_crimes / 10, 2)  # small boost for more crimes
            adjusted_severity = round(min(5, adjusted_severity), 2)  # keep within 0–5 range

            crime_types = {k: v['count'] for k, v in crime_stats.items()}

            return {
                'total_crimes': total_crimes,
                'crime_types': crime_types,
                'avg_severity': adjusted_severity,
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

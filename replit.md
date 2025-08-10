# SafePath - Crime Prediction & Safe Routing

## Overview

SafePath is a Flask-based web application that uses machine learning to predict crime risks and provide safe routing recommendations across India. The system analyzes historical crime data to assess risk levels for specific locations and suggests optimal routes with minimal crime exposure. Built with a focus on public safety, it provides real-time risk assessments and interactive mapping capabilities for users to make informed decisions about their travel routes.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Single Page Application (SPA)**: Uses vanilla JavaScript with Bootstrap for responsive design
- **Interactive Mapping**: Leaflet.js integration for displaying crime data and route visualization
- **Chart Visualization**: Built-in charting capabilities for crime statistics display
- **Responsive Design**: Bootstrap-based dark theme optimized for mobile and desktop

### Backend Architecture
- **Web Framework**: Flask with SQLAlchemy ORM for database operations
- **Database Layer**: SQLite for development with PostgreSQL compatibility built-in
- **Machine Learning Pipeline**: Custom CrimePredictor class using scikit-learn RandomForestRegressor
- **API Design**: RESTful endpoints for crime data retrieval and risk assessment
- **Data Generation**: Automated sample data generation for Indian metropolitan areas

### Data Models
- **CrimeData**: Stores crime incidents with location coordinates, type, timestamp, severity, and area information
- **SafeRoute**: Manages calculated safe routes with risk scores and waypoint data
- **Feature Engineering**: Temporal features (hour, day, month) combined with spatial coordinates for ML model training

### Machine Learning Components
- **Risk Prediction**: RandomForest model trained on historical crime patterns
- **Feature Processing**: LabelEncoder for categorical crime types, spatial-temporal feature extraction
- **Model Persistence**: Joblib-based model serialization for production deployment
- **Training Pipeline**: Automated retraining capability when new crime data becomes available

### Security & Configuration
- **Environment-Based Config**: Database URLs and secrets managed via environment variables
- **Session Management**: Flask session handling with configurable secret keys
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxies
- **Connection Pooling**: SQLAlchemy engine optimization with connection recycling

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework with SQLAlchemy integration
- **SQLAlchemy**: ORM for database operations with declarative base models
- **scikit-learn**: Machine learning library for crime prediction algorithms
- **pandas/numpy**: Data processing and numerical computation

### Frontend Libraries
- **Bootstrap**: CSS framework with dark theme support
- **Leaflet.js**: Interactive mapping library for geospatial visualization
- **Font Awesome**: Icon library for UI components
- **OpenStreetMap**: Tile service for map rendering

### Data & ML Dependencies
- **joblib**: Model serialization and persistence
- **LabelEncoder**: Categorical data encoding for machine learning
- **RandomForestRegressor**: Primary algorithm for crime risk prediction

### Development & Deployment
- **Werkzeug ProxyFix**: WSGI middleware for production deployment
- **Python Logging**: Built-in logging system for debugging and monitoring
- **SQLite/PostgreSQL**: Database flexibility for different environments
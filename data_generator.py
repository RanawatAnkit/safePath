import random
from datetime import datetime, timedelta
from app import db
from models import CrimeData
import logging

def generate_sample_data():
    """Generate sample crime data for Indian cities if database is empty"""
    
    # Check if data already exists
    if CrimeData.query.first():
        logging.info("Crime data already exists, skipping generation")
        return
    
    logging.info("Generating sample crime data...")
    
    # Major Indian cities with their approximate coordinates
    indian_cities = [
        {'name': 'Mumbai', 'lat': 19.0760, 'lng': 72.8777},
        {'name': 'Delhi', 'lat': 28.7041, 'lng': 77.1025},
        {'name': 'Bangalore', 'lat': 12.9716, 'lng': 77.5946},
        {'name': 'Hyderabad', 'lat': 17.3850, 'lng': 78.4867},
        {'name': 'Chennai', 'lat': 13.0827, 'lng': 80.2707},
        {'name': 'Kolkata', 'lat': 22.5726, 'lng': 88.3639},
        {'name': 'Pune', 'lat': 18.5204, 'lng': 73.8567},
        {'name': 'Ahmedabad', 'lat': 23.0225, 'lng': 72.5714},
        {'name': 'Jaipur', 'lat': 26.9124, 'lng': 75.7873},
        {'name': 'Lucknow', 'lat': 26.8467, 'lng': 80.9462}
    ]
    
    crime_types = [
        'Theft', 'Burglary', 'Assault', 'Robbery', 'Vandalism',
        'Fraud', 'Drug Offense', 'Vehicle Theft', 'Domestic Violence',
        'Cyber Crime', 'Chain Snatching', 'Pickpocketing'
    ]
    
    # Generate crime data for the past 2 years
    start_date = datetime.now() - timedelta(days=730)
    end_date = datetime.now()
    
    crimes_generated = 0
    
    for city in indian_cities:
        # Generate 200-500 crimes per city
        num_crimes = random.randint(200, 500)
        
        for _ in range(num_crimes):
            # Random location within ~10km radius of city center
            lat_offset = random.uniform(-0.1, 0.1)  # roughly 10km
            lng_offset = random.uniform(-0.1, 0.1)
            
            # Random timestamp within the date range
            random_days = random.randint(0, 730)
            crime_date = start_date + timedelta(days=random_days)
            
            # Add some time patterns (more crimes at night for certain types)
            crime_type = random.choice(crime_types)
            hour = random.randint(0, 23)
            
            # Adjust hour based on crime type
            if crime_type in ['Burglary', 'Theft', 'Chain Snatching']:
                hour = random.choices(range(24), weights=[
                    3, 2, 1, 1, 1, 1, 2, 3, 4, 5, 6, 7,  # 0-11
                    8, 9, 8, 7, 6, 5, 4, 6, 8, 7, 5, 4   # 12-23
                ])[0]
            
            crime_date = crime_date.replace(
                hour=hour,
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            # Severity based on crime type
            severity_mapping = {
                'Assault': random.randint(3, 5),
                'Robbery': random.randint(3, 5),
                'Domestic Violence': random.randint(4, 5),
                'Drug Offense': random.randint(2, 4),
                'Theft': random.randint(1, 3),
                'Pickpocketing': random.randint(1, 2),
                'Fraud': random.randint(2, 4),
                'Cyber Crime': random.randint(2, 3),
                'Vandalism': random.randint(1, 2),
                'Vehicle Theft': random.randint(2, 4),
                'Chain Snatching': random.randint(2, 3),
                'Burglary': random.randint(2, 4)
            }
            
            crime = CrimeData(
                latitude=city['lat'] + lat_offset,
                longitude=city['lng'] + lng_offset,
                crime_type=crime_type,
                timestamp=crime_date,
                severity=severity_mapping.get(crime_type, random.randint(1, 3)),
                area_name=city['name'],
                description=f"{crime_type} reported in {city['name']}"
            )
            
            db.session.add(crime)
            crimes_generated += 1
    
    try:
        db.session.commit()
        logging.info(f"Successfully generated {crimes_generated} crime records")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error generating crime data: {e}")

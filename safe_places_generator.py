import random
import logging
from app import db
from models import SafePlace

def generate_safe_places_data():
    """Generate sample safe places data for Indian cities if database is empty"""
    
    # Check if data already exists
    if SafePlace.query.first():
        logging.info("Safe places data already exists, skipping generation")
        return
    
    logging.info("Generating sample safe places data...")
    
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
    
    # Safe place types with their typical names
    place_templates = {
        'police_station': [
            'City Police Station', 'Metro Police Station', 'Central Police Station',
            'District Police Station', 'Traffic Police Station', 'Railway Police Station'
        ],
        'hospital': [
            'Government Hospital', 'Medical College Hospital', 'District Hospital',
            'General Hospital', 'Emergency Medical Center', 'Primary Health Center'
        ],
        'fire_station': [
            'Fire Station', 'Fire Brigade', 'Emergency Fire Services',
            'Municipal Fire Station', 'City Fire Department'
        ],
        'government_office': [
            'Municipal Corporation', 'Collector Office', 'Tehsil Office',
            'Block Development Office', 'District Magistrate Office'
        ],
        'bank': [
            'State Bank Branch', 'Central Bank', 'National Bank',
            'Commercial Bank', 'Cooperative Bank'
        ],
        'school': [
            'Government School', 'Municipal School', 'Higher Secondary School',
            'Primary School', 'Model School'
        ]
    }
    
    places_generated = 0
    
    for city in indian_cities:
        for place_type, templates in place_templates.items():
            # Generate 3-8 places of each type per city
            num_places = random.randint(3, 8)
            
            for i in range(num_places):
                # Random location within ~15km radius of city center
                lat_offset = random.uniform(-0.15, 0.15)
                lng_offset = random.uniform(-0.15, 0.15)
                
                # Pick a template and customize it
                template = random.choice(templates)
                place_name = f"{template} - {city['name']}"
                if i > 0:
                    place_name += f" {['North', 'South', 'East', 'West', 'Central'][i % 5]}"
                
                # Generate realistic address
                areas = [
                    'Sector', 'Block', 'Colony', 'Nagar', 'Puram', 'Ganj', 
                    'Chowk', 'Road', 'Market', 'Plaza'
                ]
                area_name = random.choice(areas)
                area_num = random.randint(1, 50)
                address = f"{area_name} {area_num}, {city['name']}"
                
                # Generate phone number (Indian format)
                phone = f"+91-{random.randint(7000, 9999)}-{random.randint(100000, 999999)}"
                
                # Generate hours based on place type
                hours_mapping = {
                    'police_station': '24 Hours',
                    'hospital': '24 Hours',
                    'fire_station': '24 Hours',
                    'government_office': '9:00 AM - 6:00 PM',
                    'bank': '10:00 AM - 4:00 PM',
                    'school': '8:00 AM - 4:00 PM'
                }
                
                safe_place = SafePlace(
                    name=place_name,
                    place_type=place_type,
                    latitude=city['lat'] + lat_offset,
                    longitude=city['lng'] + lng_offset,
                    address=address,
                    phone=phone,
                    hours=hours_mapping.get(place_type, '9:00 AM - 6:00 PM'),
                    verified=random.choice([True, True, True, False])  # 75% verified
                )
                
                db.session.add(safe_place)
                places_generated += 1
    
    try:
        db.session.commit()
        logging.info(f"Successfully generated {places_generated} safe places")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error generating safe places data: {e}")
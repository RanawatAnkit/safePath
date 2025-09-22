import pandas as pd
import logging
from app import db
from models import CrimeData

def load_data_from_csv(csv_file="crime_data.csv"):
    """Load crime data from CSV and insert into database if empty"""

    # Check if data already exists
    if CrimeData.query.first():
        logging.info("Crime data already exists, skipping CSV import")
        return
    
    logging.info(f"Loading crime data from {csv_file}...")

    try:
        df = pd.read_csv(csv_file)

        # Expected columns in CSV:
        # latitude, longitude, crime_type, timestamp, severity, area_name, description
        required_columns = ["latitude", "longitude", "crime_type", "timestamp", "severity", "area_name", "description"]
        for col in required_columns:
            if col not in df.columns:
                logging.error(f"Missing required column: {col}")
                return

        records = []
        for _, row in df.iterrows():
            try:
                crime = CrimeData(
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    crime_type=row["crime_type"],
                    timestamp=pd.to_datetime(row["timestamp"]),
                    severity=int(row["severity"]),
                    area_name=row["area_name"],
                    description=row["description"]
                )
                records.append(crime)
            except Exception as e:
                logging.warning(f"Skipping invalid row: {row.to_dict()} | Error: {e}")

        db.session.bulk_save_objects(records)
        db.session.commit()
        logging.info(f"Successfully inserted {len(records)} crime records from CSV")

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error loading data from CSV: {e}")

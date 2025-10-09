#<------------------------------------New changes from Here---------------------------------------->
from app import app, db

def migrate_database():
    with app.app_context():
        try:
            # Add new columns to crime_data table
            with db.engine.connect() as conn:
                # Check if columns already exist before adding
                result = conn.execute(db.text("PRAGMA table_info(crime_data)"))
                existing_columns = [row[1] for row in result]
                
                if 'evidence_file' not in existing_columns:
                    print("Adding evidence_file column...")
                    conn.execute(db.text('ALTER TABLE crime_data ADD COLUMN evidence_file VARCHAR(500)'))
                    conn.commit()
                    print("✓ evidence_file column added")
                else:
                    print("✓ evidence_file column already exists")
                
                if 'reported_by' not in existing_columns:
                    print("Adding reported_by column...")
                    conn.execute(db.text('ALTER TABLE crime_data ADD COLUMN reported_by INTEGER'))
                    conn.commit()
                    print("✓ reported_by column added")
                else:
                    print("✓ reported_by column already exists")
                
                if 'is_user_report' not in existing_columns:
                    print("Adding is_user_report column...")
                    conn.execute(db.text('ALTER TABLE crime_data ADD COLUMN is_user_report BOOLEAN DEFAULT 0'))
                    conn.commit()
                    print("✓ is_user_report column added")
                else:
                    print("✓ is_user_report column already exists")
                
                if 'verified' not in existing_columns:
                    print("Adding verified column...")
                    conn.execute(db.text('ALTER TABLE crime_data ADD COLUMN verified BOOLEAN DEFAULT 0'))
                    conn.commit()
                    print("✓ verified column added")
                else:
                    print("✓ verified column already exists")
                
            print("\n✓ Database migration completed successfully!")
            
        except Exception as e:
            print(f"✗ Error during migration: {e}")
            raise

if __name__ == '__main__':
    migrate_database()
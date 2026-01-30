"""
Helper script to create PostgreSQL database
This script attempts to create the database if it doesn't exist.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings

def create_database():
    # Parse DATABASE_URL to get connection details
    db_url = settings.DATABASE_URL
    # Format: postgresql://user:password@host:port/dbname
    parts = db_url.replace('postgresql://', '').split('/')
    db_name = parts[1] if len(parts) > 1 else 'jp_secure_staff'
    conn_string = parts[0]
    
    try:
        # Connect to PostgreSQL server (not to specific database)
        conn = psycopg2.connect(f"postgresql://{conn_string}/postgres")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if exists:
            print(f"Database '{db_name}' already exists.")
        else:
            # Create database
            cursor.execute(f'CREATE DATABASE {db_name}')
            print(f"Database '{db_name}' created successfully!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"Error connecting to PostgreSQL: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is installed and running")
        print("2. Connection details in .env are correct")
        print("3. You can manually create the database using:")
        print(f"   CREATE DATABASE {db_name};")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_database()


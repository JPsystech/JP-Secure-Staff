"""Simple script to create the database"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    # Connect to PostgreSQL server
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/postgres')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Check if database exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'jp_secure_staff'")
    exists = cur.fetchone()
    
    if exists:
        print("✓ Database 'jp_secure_staff' already exists")
    else:
        # Create database
        cur.execute('CREATE DATABASE jp_secure_staff')
        print("✓ Database 'jp_secure_staff' created successfully!")
    
    cur.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"✗ Error connecting to PostgreSQL: {e}")
    print("\nPlease ensure:")
    print("1. PostgreSQL is running")
    print("2. Connection details are correct (postgres:postgres@localhost:5432)")
    print("3. Or manually create: CREATE DATABASE jp_secure_staff;")
except Exception as e:
    print(f"✗ Error: {e}")


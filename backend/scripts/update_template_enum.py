"""Update template enum type directly in PostgreSQL"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import psycopg2
from app.core.config import settings

def update_enum():
    # Parse DATABASE_URL
    # Format: postgresql://user:password@host:port/dbname
    db_url = settings.DATABASE_URL.replace('postgresql://', '')
    
    if '@' in db_url:
        auth, rest = db_url.split('@', 1)
        if ':' in auth:
            user, password = auth.split(':', 1)
        else:
            user = auth
            password = ''
        
        if ':' in rest:
            host_port, dbname = rest.rsplit('/', 1)
            if ':' in host_port:
                host, port = host_port.split(':', 1)
            else:
                host = host_port
                port = '5432'
        else:
            host = rest.split('/')[0]
            port = '5432'
            dbname = rest.split('/')[1]
    else:
        # Fallback parsing
        parts = db_url.split('/')
        dbname = parts[-1]
        host_port = parts[0] if len(parts) > 1 else 'localhost'
        if ':' in host_port:
            host, port = host_port.split(':', 1)
        else:
            host = host_port
            port = '5432'
        user = 'postgres'
        password = ''
    
    try:
        # Connect without transaction for enum changes
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=dbname,
            user=user,
            password=password
        )
        conn.autocommit = True  # Important: enum changes can't be in transaction
        
        cursor = conn.cursor()
        
        print("Adding new enum values...")
        try:
            cursor.execute("ALTER TYPE templatetype ADD VALUE 'APPOINTMENT_PERMANENT'")
            print("✓ Added APPOINTMENT_PERMANENT")
        except psycopg2.errors.DuplicateObject:
            print("  APPOINTMENT_PERMANENT already exists")
        
        try:
            cursor.execute("ALTER TYPE templatetype ADD VALUE 'APPOINTMENT_FREELANCER'")
            print("✓ Added APPOINTMENT_FREELANCER")
        except psycopg2.errors.DuplicateObject:
            print("  APPOINTMENT_FREELANCER already exists")
        
        try:
            cursor.execute("ALTER TYPE templatetype ADD VALUE 'APPOINTMENT_CONTRACTUAL'")
            print("✓ Added APPOINTMENT_CONTRACTUAL")
        except psycopg2.errors.DuplicateObject:
            print("  APPOINTMENT_CONTRACTUAL already exists")
        
        print("\nUpdating existing template records...")
        cursor.execute("""
            UPDATE templates 
            SET type = 'APPOINTMENT_PERMANENT'::templatetype
            WHERE type = 'APPOINTMENT_PERM'::templatetype
        """)
        print(f"  Updated {cursor.rowcount} records: APPOINTMENT_PERM -> APPOINTMENT_PERMANENT")
        
        cursor.execute("""
            UPDATE templates 
            SET type = 'APPOINTMENT_FREELANCER'::templatetype
            WHERE type = 'APPOINTMENT_FREEL'::templatetype
        """)
        print(f"  Updated {cursor.rowcount} records: APPOINTMENT_FREEL -> APPOINTMENT_FREELANCER")
        
        cursor.execute("""
            UPDATE templates 
            SET type = 'APPOINTMENT_CONTRACTUAL'::templatetype
            WHERE type = 'APPOINTMENT_CONT'::templatetype
        """)
        print(f"  Updated {cursor.rowcount} records: APPOINTMENT_CONT -> APPOINTMENT_CONTRACTUAL")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Enum update completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error updating enum: {str(e)}")
        return False

if __name__ == "__main__":
    update_enum()


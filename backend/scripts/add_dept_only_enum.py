"""Add DEPT_ONLY value to documentvisibilityscope enum in PostgreSQL"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import psycopg2
from app.core.config import settings

def add_dept_only_enum():
    """Add DEPT_ONLY value to documentvisibilityscope enum"""
    # Parse DATABASE_URL
    database_url = settings.DATABASE_URL
    
    # Extract connection details
    if database_url.startswith('postgresql://'):
        url_parts = database_url.replace('postgresql://', '').split('/')
        if len(url_parts) < 2:
            print("Invalid DATABASE_URL format")
            return
        
        auth_part = url_parts[0]
        dbname = url_parts[1]
        
        if '@' in auth_part:
            user_pass, host_port = auth_part.split('@')
            if ':' in user_pass:
                user, password = user_pass.split(':', 1)
            else:
                user = user_pass
                password = ''
            
            if ':' in host_port:
                host, port = host_port.split(':')
                port = int(port)
            else:
                host = host_port
                port = 5432
        else:
            host = 'localhost'
            port = 5432
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
        
        print("Checking current enum values...")
        cursor.execute("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid FROM pg_type WHERE typname = 'documentvisibilityscope'
            )
            ORDER BY enumsortorder;
        """)
        existing_values = [row[0] for row in cursor.fetchall()]
        print(f"Current enum values: {existing_values}")
        
        if 'DEPT_ONLY' in existing_values:
            print("✓ DEPT_ONLY already exists in enum")
        else:
            print("Adding DEPT_ONLY to enum...")
            try:
                cursor.execute("ALTER TYPE documentvisibilityscope ADD VALUE 'DEPT_ONLY'")
                print("✓ Added DEPT_ONLY to documentvisibilityscope enum")
            except psycopg2.errors.DuplicateObject:
                print("  DEPT_ONLY already exists")
            except Exception as e:
                print(f"  Error adding DEPT_ONLY: {e}")
        
        # Verify
        cursor.execute("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid FROM pg_type WHERE typname = 'documentvisibilityscope'
            )
            ORDER BY enumsortorder;
        """)
        final_values = [row[0] for row in cursor.fetchall()]
        print(f"\nFinal enum values: {final_values}")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Enum update completed!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_dept_only_enum()


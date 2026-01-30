"""Create Phase 3 enum types manually"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import psycopg2
from app.core.config import settings

def create_enums():
    # Parse DATABASE_URL
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
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=dbname,
            user=user,
            password=password
        )
        conn.autocommit = True
        
        cursor = conn.cursor()
        
        enums = [
            ("documentownerdept", "('OPERATIONS', 'FINANCE', 'HR')"),
            ("documentcategory", "('STAGE_A', 'FINANCE_KYC', 'HR_SIGNED', 'APPOINTMENT', 'ID_CARD', 'OTHER')"),
            ("ticketcategory", "('DOCUMENT_REQUEST', 'DATA_CORRECTION', 'CLARIFICATION', 'OTHER')"),
            ("ticketpriority", "('LOW', 'NORMAL', 'HIGH')"),
            ("ticketstatus", "('OPEN', 'IN_PROGRESS', 'WAITING', 'RESOLVED', 'CLOSED')"),
            ("grantscopetype", "('DOCUMENTS', 'CATEGORY')"),
        ]
        
        for enum_name, enum_values in enums:
            try:
                cursor.execute(f"CREATE TYPE {enum_name} AS ENUM {enum_values}")
                print(f"✓ Created {enum_name}")
            except psycopg2.errors.DuplicateObject:
                print(f"  {enum_name} already exists")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Enum types ready!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error creating enums: {str(e)}")
        return False

if __name__ == "__main__":
    create_enums()


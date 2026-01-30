"""Migration script to update AccessGrant table to use scope_value instead of document_ids/doc_category"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate_access_grant():
    """Migrate AccessGrant table to use scope_value"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Check if scope_value column exists
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'access_grants' AND column_name = 'scope_value'
        """))
        
        if result.fetchone():
            print("✓ scope_value column already exists")
        else:
            # Add scope_value column
            connection.execute(text("ALTER TABLE access_grants ADD COLUMN scope_value VARCHAR"))
            connection.commit()
            print("✓ Added scope_value column")
        
        # Migrate data from document_ids/doc_category to scope_value
        # For DOCUMENTS scope: use first document_id as scope_value
        # For CATEGORY scope: use doc_category as scope_value
        connection.execute(text("""
            UPDATE access_grants 
            SET scope_value = (
                CASE 
                    WHEN scope_type = 'DOCUMENTS' AND document_ids IS NOT NULL 
                    THEN (document_ids->>0)::text
                    WHEN scope_type = 'CATEGORY' AND doc_category IS NOT NULL 
                    THEN doc_category
                    ELSE NULL
                END
            )
            WHERE scope_value IS NULL
        """))
        connection.commit()
        print("✓ Migrated data to scope_value")
        
        # Add revoked_at column if it doesn't exist
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'access_grants' AND column_name = 'revoked_at'
        """))
        
        if result.fetchone():
            print("✓ revoked_at column already exists")
        else:
            connection.execute(text("ALTER TABLE access_grants ADD COLUMN revoked_at TIMESTAMP WITH TIME ZONE"))
            connection.commit()
            print("✓ Added revoked_at column")
        
        # Update granted_by_dept_id if it doesn't exist (rename from granted_dept_id)
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'access_grants' AND column_name = 'granted_by_dept_id'
        """))
        
        if not result.fetchone():
            # Check if granted_dept_id exists
            result2 = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'access_grants' AND column_name = 'granted_dept_id'
            """))
            if result2.fetchone():
                connection.execute(text("ALTER TABLE access_grants RENAME COLUMN granted_dept_id TO granted_by_dept_id"))
                connection.commit()
                print("✓ Renamed granted_dept_id to granted_by_dept_id")
            else:
                connection.execute(text("ALTER TABLE access_grants ADD COLUMN granted_by_dept_id INTEGER REFERENCES departments(id)"))
                connection.commit()
                print("✓ Added granted_by_dept_id column")
        else:
            print("✓ granted_by_dept_id column already exists")
        
        print("\n✓ Migration complete!")

if __name__ == "__main__":
    migrate_access_grant()


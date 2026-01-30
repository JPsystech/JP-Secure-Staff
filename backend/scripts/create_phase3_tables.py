"""Create Phase 3 tables manually (after enums are created)"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import psycopg2
from app.core.config import settings

def create_tables():
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
        
        # Create ticket_counter
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_counter (
                id INTEGER PRIMARY KEY DEFAULT 1,
                last_number INTEGER NOT NULL DEFAULT 0
            )
        """)
        print("✓ Created ticket_counter")
        
        # Initialize counter if empty
        cursor.execute("INSERT INTO ticket_counter (id, last_number) VALUES (1, 0) ON CONFLICT (id) DO NOTHING")
        
        # Create audit_logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id UUID PRIMARY KEY,
                actor_user_id INTEGER REFERENCES users(id),
                action_type VARCHAR NOT NULL,
                entity_type VARCHAR NOT NULL,
                entity_id VARCHAR,
                action_metadata JSONB,
                ip_address VARCHAR,
                user_agent TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_action_type ON audit_logs(action_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_id ON audit_logs(entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_type ON audit_logs(entity_type)")
        print("✓ Created audit_logs")
        
        # Create tickets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id UUID PRIMARY KEY,
                ticket_no VARCHAR NOT NULL UNIQUE,
                from_dept_id INTEGER NOT NULL REFERENCES departments(id),
                to_dept_id INTEGER NOT NULL REFERENCES departments(id),
                created_by_user_id INTEGER NOT NULL REFERENCES users(id),
                assigned_to_user_id INTEGER REFERENCES users(id),
                person_id UUID REFERENCES persons(id),
                category ticketcategory NOT NULL,
                priority ticketpriority NOT NULL DEFAULT 'NORMAL',
                subject VARCHAR NOT NULL,
                description TEXT NOT NULL,
                status ticketstatus NOT NULL DEFAULT 'OPEN',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE,
                closed_at TIMESTAMP WITH TIME ZONE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_tickets_ticket_no ON tickets(ticket_no)")
        print("✓ Created tickets")
        
        # Create access_grants
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_grants (
                id UUID PRIMARY KEY,
                ticket_id UUID NOT NULL REFERENCES tickets(id),
                person_id UUID NOT NULL REFERENCES persons(id),
                granted_by_user_id INTEGER NOT NULL REFERENCES users(id),
                granted_to_user_id INTEGER NOT NULL REFERENCES users(id),
                granted_dept_id INTEGER NOT NULL REFERENCES departments(id),
                scope_type grantscopetype NOT NULL,
                document_ids JSONB,
                doc_category VARCHAR,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("✓ Created access_grants")
        
        # Create ticket_comments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_comments (
                id UUID PRIMARY KEY,
                ticket_id UUID NOT NULL REFERENCES tickets(id),
                author_user_id INTEGER NOT NULL REFERENCES users(id),
                message TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("✓ Created ticket_comments")
        
        # Create ticket_attachments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_attachments (
                id UUID PRIMARY KEY,
                ticket_id UUID NOT NULL REFERENCES tickets(id),
                uploaded_by_user_id INTEGER NOT NULL REFERENCES users(id),
                file_name VARCHAR NOT NULL,
                file_key VARCHAR NOT NULL,
                mime_type VARCHAR NOT NULL,
                size_bytes INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("✓ Created ticket_attachments")
        
        # Add columns to documents if they don't exist
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='documents' AND column_name='owner_dept') THEN
                    ALTER TABLE documents ADD COLUMN owner_dept documentownerdept;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='documents' AND column_name='doc_category') THEN
                    ALTER TABLE documents ADD COLUMN doc_category documentcategory;
                END IF;
            END $$;
        """)
        print("✓ Updated documents table")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Phase 3 tables created successfully!")
        print("\nNext step: Mark migration as applied:")
        print("  alembic stamp a31038410342")
        return True
        
    except Exception as e:
        print(f"\n✗ Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_tables()


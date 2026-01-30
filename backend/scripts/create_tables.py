"""Create all tables directly using SQLAlchemy"""
from app.core.database import Base, engine
from app.models import (
    User, Department, Role, Permission, UserRole,
    CompanyMaster, DocumentNameMaster, LocationMaster, ProjectMaster,
    Policy, Template, TemplateRevision
)

if __name__ == "__main__":
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully!")


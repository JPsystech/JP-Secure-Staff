from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.master_data import (
    CompanyMaster, DocumentNameMaster, LocationMaster, ProjectMaster
)
from app.schemas.master_data import (
    CompanyMasterCreate, CompanyMasterUpdate, CompanyMasterResponse,
    DocumentNameMasterCreate, DocumentNameMasterUpdate, DocumentNameMasterResponse,
    LocationMasterCreate, LocationMasterUpdate, LocationMasterResponse,
    ProjectMasterCreate, ProjectMasterUpdate, ProjectMasterResponse
)
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()

# Company Master endpoints
@router.get("/companies", response_model=List[CompanyMasterResponse])
async def get_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    companies = db.query(CompanyMaster).all()
    return companies

@router.post("/companies", response_model=CompanyMasterResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company: CompanyMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(CompanyMaster).filter(CompanyMaster.short_code == company.short_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company code already exists")
    
    db_company = CompanyMaster(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.patch("/companies/{id}", response_model=CompanyMasterResponse)
async def update_company(
    id: int,
    company: CompanyMasterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_company = db.query(CompanyMaster).filter(CompanyMaster.id == id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = company.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company

# Document Name Master endpoints
@router.get("/documents", response_model=List[DocumentNameMasterResponse])
async def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    documents = db.query(DocumentNameMaster).all()
    return documents

@router.post("/documents", response_model=DocumentNameMasterResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentNameMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_document = DocumentNameMaster(**document.dict())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

@router.patch("/documents/{id}", response_model=DocumentNameMasterResponse)
async def update_document(
    id: int,
    document: DocumentNameMasterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_document = db.query(DocumentNameMaster).filter(DocumentNameMaster.id == id).first()
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    update_data = document.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_document, field, value)
    
    db.commit()
    db.refresh(db_document)
    return db_document

# Location Master endpoints
@router.get("/locations", response_model=List[LocationMasterResponse])
async def get_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    locations = db.query(LocationMaster).all()
    return locations

@router.post("/locations", response_model=LocationMasterResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location: LocationMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_location = LocationMaster(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

@router.patch("/locations/{id}", response_model=LocationMasterResponse)
async def update_location(
    id: int,
    location: LocationMasterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_location = db.query(LocationMaster).filter(LocationMaster.id == id).first()
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    update_data = location.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_location, field, value)
    
    db.commit()
    db.refresh(db_location)
    return db_location

# Project Master endpoints
@router.get("/projects", response_model=List[ProjectMasterResponse])
async def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects = db.query(ProjectMaster).all()
    return projects

@router.post("/projects", response_model=ProjectMasterResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_project = ProjectMaster(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.patch("/projects/{id}", response_model=ProjectMasterResponse)
async def update_project(
    id: int,
    project: ProjectMasterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_project = db.query(ProjectMaster).filter(ProjectMaster.id == id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project


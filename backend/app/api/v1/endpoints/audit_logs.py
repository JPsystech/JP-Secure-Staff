"""Audit Log API Endpoints (Master Admin + Sub-Admin with permissions)"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, desc, asc
from typing import Optional, List
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.department import Department
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse, AuditLogFilter
from app.api.v1.dependencies.permissions import require_permission
from app.core.permissions import PermissionCode
from app.services.audit_sanitizer import sanitize_audit_metadata
from datetime import datetime
from uuid import UUID
import csv
import io
import json
from typing import Generator

router = APIRouter()


@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    date_from: Optional[datetime] = Query(None, description="Start date (ISO datetime)"),
    date_to: Optional[datetime] = Query(None, description="End date (ISO datetime)"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    actor_user_id: Optional[int] = Query(None, description="Filter by actor user ID"),
    dept_id: Optional[int] = Query(None, description="Filter by actor's department ID"),
    search: Optional[str] = Query(None, description="Search in entity_id or metadata text"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Page size"),
    sort: str = Query("-created_at", description="Sort order (-created_at for desc, created_at for asc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.AUDIT_VIEW))
):
    """
    Get audit logs with filtering, pagination, and sorting.
    Requires AUDIT_VIEW permission.
    Master Admin sees all logs with full metadata.
    Sub-Admin sees logs with masked sensitive Finance/KYC metadata.
    """
    
    # Build query with joins for user and department
    query = db.query(AuditLog).outerjoin(User, AuditLog.actor_user_id == User.id)
    
    # Apply filters
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if actor_user_id:
        query = query.filter(AuditLog.actor_user_id == actor_user_id)
    if dept_id:
        query = query.filter(User.dept_id == dept_id)
    if search:
        # Search in entity_id or metadata (as JSON text)
        search_filter = or_(
            AuditLog.entity_id.ilike(f"%{search}%"),
            func.cast(AuditLog.action_metadata, db.String).ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting
    if sort.startswith("-"):
        sort_field = sort[1:]
        if sort_field == "created_at":
            query = query.order_by(desc(AuditLog.created_at))
        else:
            query = query.order_by(desc(AuditLog.created_at))  # Default
    else:
        if sort == "created_at":
            query = query.order_by(asc(AuditLog.created_at))
        else:
            query = query.order_by(desc(AuditLog.created_at))  # Default
    
    # Apply pagination
    offset = (page - 1) * page_size
    logs = query.offset(offset).limit(page_size).all()
    
    # Build response with sanitized metadata
    result = []
    for log in logs:
        actor = db.query(User).options(
            joinedload(User.department)
        ).filter(User.id == log.actor_user_id).first() if log.actor_user_id else None
        
        # Sanitize metadata for Sub-Admin
        sanitized_metadata = sanitize_audit_metadata(
            db, current_user, log.action_type, log.entity_type, log.action_metadata
        )
        
        response = AuditLogResponse(
            id=log.id,
            actor_user_id=log.actor_user_id,
            action_type=log.action_type,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            action_metadata=sanitized_metadata,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
            actor_name=actor.full_name if actor else "System",
            actor_email=actor.email if actor else None,
            actor_dept_id=actor.dept_id if actor else None,
            actor_dept_name=actor.department.name if actor and actor.department else None
        )
        result.append(response)
    
    return AuditLogListResponse(
        items=result,
        page=page,
        page_size=page_size,
        total=total
    )


@router.get("/logs/export")
async def export_audit_logs(
    date_from: Optional[datetime] = Query(None, description="Start date (ISO datetime)"),
    date_to: Optional[datetime] = Query(None, description="End date (ISO datetime)"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    actor_user_id: Optional[int] = Query(None, description="Filter by actor user ID"),
    dept_id: Optional[int] = Query(None, description="Filter by actor's department ID"),
    search: Optional[str] = Query(None, description="Search in entity_id or metadata text"),
    format: str = Query("csv", description="Export format: csv or xlsx"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.AUDIT_EXPORT))
):
    """
    Export audit logs to CSV or Excel.
    Requires AUDIT_EXPORT permission.
    Applies same filtering as GET /logs endpoint.
    For large datasets (>20k rows), CSV is recommended.
    """
    
    # Build query (same as get_audit_logs)
    query = db.query(AuditLog).outerjoin(User, AuditLog.actor_user_id == User.id)
    
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if actor_user_id:
        query = query.filter(AuditLog.actor_user_id == actor_user_id)
    if dept_id:
        query = query.filter(User.dept_id == dept_id)
    if search:
        search_filter = or_(
            AuditLog.entity_id.ilike(f"%{search}%"),
            func.cast(AuditLog.action_metadata, db.String).ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    query = query.order_by(desc(AuditLog.created_at))
    
    # Check row count for XLSX (limit to 20k for performance)
    total_rows = query.count()
    if format.lower() == "xlsx" and total_rows > 20000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many rows ({total_rows}) for Excel export. Please use CSV format or apply more filters to reduce results to under 20,000 rows."
        )
    
    # Fetch all matching logs
    logs = query.all()
    
    if format.lower() == "csv":
        return _generate_csv_export(logs, db, current_user)
    elif format.lower() == "xlsx":
        return _generate_xlsx_export(logs, db, current_user)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Use 'csv' or 'xlsx'"
        )


def _generate_csv_export(logs: List[AuditLog], db: Session, current_user: User) -> StreamingResponse:
    """Generate CSV export with streaming"""
    
    def generate_csv_rows() -> Generator[str, None, None]:
        # Header
        yield "Date/Time,Action Type,Entity Type,Entity ID,Actor Name,Actor Email,Department,IP Address,User Agent,Metadata\n"
        
        # Rows
        for log in logs:
            actor = db.query(User).options(
                joinedload(User.department)
            ).filter(User.id == log.actor_user_id).first() if log.actor_user_id else None
            
            # Sanitize metadata
            sanitized_metadata = sanitize_audit_metadata(
                db, current_user, log.action_type, log.entity_type, log.action_metadata
            )
            
            # Format values for CSV
            created_at = log.created_at.isoformat() if log.created_at else ""
            action_type = log.action_type or ""
            entity_type = log.entity_type or ""
            entity_id = log.entity_id or ""
            actor_name = (actor.full_name if actor else "System") or ""
            actor_email = (actor.email if actor else "") or ""
            dept_name = (actor.department.name if actor and actor.department else "") or ""
            ip_address = log.ip_address or ""
            user_agent = (log.user_agent or "").replace("\n", " ").replace("\r", " ")
            metadata = json.dumps(sanitized_metadata) if sanitized_metadata else ""
            
            # Escape CSV values
            def escape_csv(value: str) -> str:
                if '"' in value or ',' in value or '\n' in value:
                    return f'"{value.replace('"', '""')}"'
                return value
            
            row = ",".join([
                escape_csv(created_at),
                escape_csv(action_type),
                escape_csv(entity_type),
                escape_csv(entity_id),
                escape_csv(actor_name),
                escape_csv(actor_email),
                escape_csv(dept_name),
                escape_csv(ip_address),
                escape_csv(user_agent),
                escape_csv(metadata)
            ]) + "\n"
            
            yield row
    
    filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        generate_csv_rows(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


def _generate_xlsx_export(logs: List[AuditLog], db: Session, current_user: User) -> Response:
    """Generate Excel export"""
    try:
        import openpyxl
        from openpyxl.styles import Font
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Excel export requires openpyxl. Install with: pip install openpyxl"
        )
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Audit Logs"
    
    # Headers
    headers = [
        "Date/Time", "Action Type", "Entity Type", "Entity ID",
        "Actor Name", "Actor Email", "Department", "IP Address",
        "User Agent", "Metadata"
    ]
    ws.append(headers)
    
    # Style header row
    for cell in ws[1]:
        cell.font = Font(bold=True)
    
    # Data rows
    for log in logs:
        actor = db.query(User).options(
            joinedload(User.department)
        ).filter(User.id == log.actor_user_id).first() if log.actor_user_id else None
        
        # Sanitize metadata
        sanitized_metadata = sanitize_audit_metadata(
            db, current_user, log.action_type, log.entity_type, log.action_metadata
        )
        
        row = [
            log.created_at.isoformat() if log.created_at else "",
            log.action_type or "",
            log.entity_type or "",
            log.entity_id or "",
            actor.full_name if actor else "System",
            actor.email if actor else "",
            actor.department.name if actor and actor.department else "",
            log.ip_address or "",
            log.user_agent or "",
            json.dumps(sanitized_metadata) if sanitized_metadata else ""
        ]
        ws.append(row)
    
    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return Response(
        content=output.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionCode.AUDIT_VIEW))
):
    """
    Get a specific audit log by ID.
    Requires AUDIT_VIEW permission.
    """
    try:
        log_uuid = UUID(log_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid log ID format")
    
    log = db.query(AuditLog).filter(AuditLog.id == log_uuid).first()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    actor = db.query(User).options(
        joinedload(User.department)
    ).filter(User.id == log.actor_user_id).first() if log.actor_user_id else None
    
    # Sanitize metadata
    sanitized_metadata = sanitize_audit_metadata(
        db, current_user, log.action_type, log.entity_type, log.action_metadata
    )
    
    response = AuditLogResponse(
        id=log.id,
        actor_user_id=log.actor_user_id,
        action_type=log.action_type,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        action_metadata=sanitized_metadata,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        created_at=log.created_at,
        actor_name=actor.full_name if actor else "System",
        actor_email=actor.email if actor else None,
        actor_dept_id=actor.dept_id if actor else None,
        actor_dept_name=actor.department.name if actor and actor.department else None
    )
    
    return response

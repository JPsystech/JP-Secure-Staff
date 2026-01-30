"""Audit Logging Service"""
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def log_audit_event(
    db: Session,
    action_type: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    actor_user_id: Optional[int] = None,
    action_metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Log an audit event to the database.
    
    Args:
        db: Database session
        action_type: Type of action (e.g., "TICKET_CREATED", "DOC_DOWNLOADED")
        entity_type: Type of entity (e.g., "Ticket", "Person", "Document")
        entity_id: ID of the entity (UUID or string)
        actor_user_id: User who performed the action (None for system actions)
        action_metadata: Additional metadata as dictionary
        ip_address: IP address of the request
        user_agent: User agent string
    """
    try:
        audit_log = AuditLog(
            actor_user_id=actor_user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            action_metadata=action_metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log audit event: {str(e)}")
        db.rollback()
        # Don't raise - audit logging should not break the main flow

def get_client_ip(request) -> Optional[str]:
    """Extract client IP from request"""
    if hasattr(request, 'client') and request.client:
        return request.client.host
    # Try common headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return None

def get_user_agent(request) -> Optional[str]:
    """Extract user agent from request"""
    return request.headers.get("User-Agent")


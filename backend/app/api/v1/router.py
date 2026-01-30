from fastapi import APIRouter, Request, Depends
from app.api.v1.endpoints import (
    auth, departments, roles, users, master_data, policies, templates,
    persons, finance, hr, hr_documents, cv_wallet, tickets, access_grants, audit_logs, debug, files, documents, admin,
    admin_persons, admin_documents, health
)

api_router = APIRouter()

# Debug ping endpoint (before auth router to allow unauthenticated access)
@api_router.get("/debug/ping")
async def debug_ping(request: Request):
    """
    Debug endpoint to verify cookie reception and user resolution.
    Returns auth headers/cookie presence, not secrets.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    auth_header = request.headers.get("Authorization", "Not present")
    cookies = dict(request.cookies)
    has_token_cookie = "access_token" in cookies or "token" in cookies
    
    # Try to get user if token exists (safely)
    user_info = None
    try:
        from app.core.database import get_db
        from app.core.security import decode_access_token
        from app.models.user import User
        
        # Extract token
        token = None
        if auth_header != "Not present":
            scheme, token = auth_header.split(" ", 1) if " " in auth_header else (None, None)
            if scheme and scheme.lower() != "bearer":
                token = None
        
        if not token:
            token = cookies.get("access_token") or cookies.get("token")
        
        if token:
            # Try to decode and get user
            try:
                payload = decode_access_token(token)
                if payload and payload.get("sub"):
                    db = next(get_db())
                    try:
                        user = db.query(User).filter(User.email == payload.get("sub")).first()
                        if user:
                            user_info = {
                                "id": user.id,
                                "email": user.email,
                                "full_name": user.full_name
                            }
                    finally:
                        db.close()
            except Exception as e:
                logger.debug(f"Could not resolve user from token: {str(e)}")
    except Exception as e:
        logger.debug(f"Error in debug ping: {str(e)}")
    
    return {
        "status": "ok",
        "auth_header_present": auth_header != "Not present",
        "auth_header_preview": auth_header[:20] + "..." if len(auth_header) > 20 and auth_header != "Not present" else auth_header,
        "has_token_cookie": has_token_cookie,
        "cookie_names": list(cookies.keys()),
        "user_resolved": user_info is not None,
        "user_info": user_info,
        "request_method": request.method,
        "request_path": request.url.path
    }

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(master_data.router, prefix="/master-data", tags=["master-data"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(persons.router, prefix="/persons", tags=["persons"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(hr.router, prefix="/hr", tags=["hr"])
api_router.include_router(hr_documents.router, prefix="/hr", tags=["hr-documents"])
api_router.include_router(cv_wallet.router, prefix="/cv-wallet", tags=["cv-wallet"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(access_grants.router, prefix="/access-grants", tags=["access-grants"])
api_router.include_router(audit_logs.router, prefix="/audit", tags=["audit"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_persons.router, prefix="/admin/persons", tags=["admin-persons"])
api_router.include_router(admin_documents.router, prefix="/admin/documents", tags=["admin-documents"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])


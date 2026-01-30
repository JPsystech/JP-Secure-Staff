"""
Permission Code Definitions

All permissions are defined here as an enum. These are auto-seeded into the database
on startup. Permissions cannot be created/deleted via UI - only code defines them.
"""
from enum import Enum
from typing import Dict, Tuple


class PermissionCode(str, Enum):
    """Permission codes - these are the source of truth for all permissions"""
    
    # Document Stage-A permissions
    DOC_STAGEA_VIEW = "DOC_STAGEA_VIEW"
    DOC_STAGEA_DOWNLOAD = "DOC_STAGEA_DOWNLOAD"
    DOC_UPLOAD_STAGEA = "DOC_UPLOAD_STAGEA"
    
    # Document Finance permissions
    DOC_FINANCE_VIEW = "DOC_FINANCE_VIEW"
    DOC_FINANCE_DOWNLOAD = "DOC_FINANCE_DOWNLOAD"
    DOC_UPLOAD_FINANCE = "DOC_UPLOAD_FINANCE"
    
    # Document HR permissions
    DOC_HR_VIEW = "DOC_HR_VIEW"
    DOC_HR_DOWNLOAD = "DOC_HR_DOWNLOAD"
    DOC_UPLOAD_HR = "DOC_UPLOAD_HR"
    
    # Ticket permissions
    TICKET_CREATE = "TICKET_CREATE"
    TICKET_VIEW = "TICKET_VIEW"
    
    # Access Grant permissions
    GRANT_CREATE = "GRANT_CREATE"
    GRANT_REVOKE = "GRANT_REVOKE"
    
    # Template permissions
    TEMPLATE_VIEW = "TEMPLATE_VIEW"
    TEMPLATE_EDIT = "TEMPLATE_EDIT"
    TEMPLATE_PUBLISH = "TEMPLATE_PUBLISH"
    
    # Audit permissions
    AUDIT_VIEW = "AUDIT_VIEW"
    AUDIT_EXPORT = "AUDIT_EXPORT"
    
    # Admin permissions
    USER_MANAGE = "USER_MANAGE"
    ROLE_MANAGE = "ROLE_MANAGE"
    DEPARTMENT_MANAGE = "DEPARTMENT_MANAGE"

    # HR / Email
    HR_IDCARD_SEND = "HR_IDCARD_SEND"
    ADMIN_EMAIL_LOG_VIEW = "ADMIN_EMAIL_LOG_VIEW"

    # Admin Person Viewer (Step-14): global read-only person + document download
    ADMIN_PERSON_VIEW_ALL = "ADMIN_PERSON_VIEW_ALL"
    ADMIN_DOCUMENT_DOWNLOAD_ALL = "ADMIN_DOCUMENT_DOWNLOAD_ALL"


# Permission metadata: (label, description, module, action)
PERMISSION_METADATA: Dict[PermissionCode, Tuple[str, str, str, str]] = {
    PermissionCode.DOC_STAGEA_VIEW: (
        "View Stage-A Documents",
        "View Stage-A documents (CV, Qualification, Certificates) in CV Wallet",
        "documents",
        "view_stagea"
    ),
    PermissionCode.DOC_STAGEA_DOWNLOAD: (
        "Download Stage-A Documents",
        "Download Stage-A documents from CV Wallet",
        "documents",
        "download_stagea"
    ),
    PermissionCode.DOC_UPLOAD_STAGEA: (
        "Upload Stage-A Documents",
        "Upload Stage-A documents during person intake",
        "documents",
        "upload_stagea"
    ),
    PermissionCode.DOC_FINANCE_VIEW: (
        "View Finance Documents",
        "View Finance KYC and other Finance documents",
        "documents",
        "view_finance"
    ),
    PermissionCode.DOC_FINANCE_DOWNLOAD: (
        "Download Finance Documents",
        "Download Finance KYC and other Finance documents",
        "documents",
        "download_finance"
    ),
    PermissionCode.DOC_UPLOAD_FINANCE: (
        "Upload Finance Documents",
        "Upload Finance KYC documents",
        "documents",
        "upload_finance"
    ),
    PermissionCode.DOC_HR_VIEW: (
        "View HR Documents",
        "View HR documents (Appointment Letters, Declarations, etc.)",
        "documents",
        "view_hr"
    ),
    PermissionCode.DOC_HR_DOWNLOAD: (
        "Download HR Documents",
        "Download HR documents (Appointment Letters, Declarations, etc.)",
        "documents",
        "download_hr"
    ),
    PermissionCode.DOC_UPLOAD_HR: (
        "Upload HR Documents",
        "Upload HR documents (Signed appointment letters, etc.)",
        "documents",
        "upload_hr"
    ),
    PermissionCode.TICKET_CREATE: (
        "Create Tickets",
        "Create new access request tickets",
        "tickets",
        "create"
    ),
    PermissionCode.TICKET_VIEW: (
        "View Tickets",
        "View tickets in inbox and own tickets",
        "tickets",
        "view"
    ),
    PermissionCode.GRANT_CREATE: (
        "Create Access Grants",
        "Create temporary access grants for documents",
        "grants",
        "create"
    ),
    PermissionCode.GRANT_REVOKE: (
        "Revoke Access Grants",
        "Revoke active access grants",
        "grants",
        "revoke"
    ),
    PermissionCode.TEMPLATE_VIEW: (
        "View Templates",
        "View document templates",
        "templates",
        "view"
    ),
    PermissionCode.TEMPLATE_EDIT: (
        "Edit Templates",
        "Edit document templates",
        "templates",
        "edit"
    ),
    PermissionCode.TEMPLATE_PUBLISH: (
        "Publish Templates",
        "Publish template revisions",
        "templates",
        "publish"
    ),
    PermissionCode.AUDIT_VIEW: (
        "View Audit Logs",
        "View system audit logs",
        "audit",
        "view"
    ),
    PermissionCode.AUDIT_EXPORT: (
        "Export Audit Logs",
        "Export audit logs to file",
        "audit",
        "export"
    ),
    PermissionCode.USER_MANAGE: (
        "Manage Users",
        "Create, update, and manage user accounts",
        "users",
        "manage"
    ),
    PermissionCode.ROLE_MANAGE: (
        "Manage Roles",
        "Create, update roles and assign permissions",
        "roles",
        "manage"
    ),
    PermissionCode.DEPARTMENT_MANAGE: (
        "Manage Departments",
        "Create, update, and manage departments",
        "departments",
        "manage"
    ),
    PermissionCode.HR_IDCARD_SEND: (
        "Send ID Card",
        "Send ID card email to employee",
        "hr",
        "send_id_card"
    ),
    PermissionCode.ADMIN_EMAIL_LOG_VIEW: (
        "View Email Logs",
        "View email send logs (admin)",
        "admin",
        "email_log_view"
    ),
    PermissionCode.ADMIN_PERSON_VIEW_ALL: (
        "View All Persons (Admin)",
        "View all persons across departments in admin (read-only)",
        "admin",
        "person_view_all"
    ),
    PermissionCode.ADMIN_DOCUMENT_DOWNLOAD_ALL: (
        "Download Any Document (Admin)",
        "Download any person document from admin view (bypass department checks)",
        "admin",
        "document_download_all"
    ),
}


def get_all_permission_codes() -> list[PermissionCode]:
    """Get all permission codes"""
    return list(PermissionCode)


def get_permission_metadata(code: PermissionCode) -> Tuple[str, str, str, str]:
    """Get metadata for a permission code: (label, description, module, action)"""
    return PERMISSION_METADATA.get(code, (code.value, "", "unknown", "unknown"))

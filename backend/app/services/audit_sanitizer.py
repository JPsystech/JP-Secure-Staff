"""
Audit Metadata Sanitization Service

Masks sensitive Finance/KYC data for Sub-Admin users while preserving
audit trail structure for Master Admin.
"""
from typing import Dict, Any, Optional
from app.models.user import User
from app.services.permission_checker import is_master_admin
from sqlalchemy.orm import Session


# Sensitive keys that should be masked for Sub-Admin
SENSITIVE_KEYS = {
    # Personal identifiers
    'aadhaar', 'aadhar', 'pan', 'passport', 'voter_id', 'driving_license',
    # Financial information
    'bank_account', 'account_number', 'ifsc', 'bank_name', 'branch',
    'salary', 'ctc', 'gross_salary', 'net_salary', 'basic_salary',
    # Employment identifiers
    'uan', 'esi', 'pf_number', 'employee_code',
    # Personal information
    'dob', 'date_of_birth', 'address', 'permanent_address', 'current_address',
    'phone', 'mobile', 'alternate_phone',
    # KYC related
    'kyc_aadhaar', 'kyc_pan', 'kyc_bank', 'kyc_address', 'kyc_dob',
    'kyc_salary', 'kyc_uan', 'kyc_esi',
    # Other sensitive
    'password', 'pin', 'otp', 'token'
}


def sanitize_audit_metadata(
    db: Session,
    current_user: User,
    action_type: str,
    entity_type: str,
    action_metadata: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Sanitize audit metadata by masking sensitive values for Sub-Admin users.
    
    Master Admin sees full metadata.
    Sub-Admin sees masked values (****) for sensitive keys.
    
    Args:
        db: Database session
        current_user: Current user requesting the audit log
        action_type: Type of action (e.g., "FINANCE_KYC_UPDATED")
        entity_type: Type of entity (e.g., "FinanceKYC", "Person")
        action_metadata: Original metadata dictionary
    
    Returns:
        Sanitized metadata dictionary (or None if input was None)
    """
    if action_metadata is None:
        return None
    
    # Master Admin sees everything
    if is_master_admin(current_user, db):
        return action_metadata
    
    # For Sub-Admin, mask sensitive values
    sanitized = {}
    
    def mask_value(value: Any) -> Any:
        """Recursively mask sensitive values"""
        if isinstance(value, dict):
            return {k: mask_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [mask_value(item) for item in value]
        elif isinstance(value, str) and value.strip():
            return "****"
        elif value is not None:
            return "****"
        return value
    
    for key, value in action_metadata.items():
        key_lower = key.lower()
        
        # Check if this key should be masked
        should_mask = any(sensitive in key_lower for sensitive in SENSITIVE_KEYS)
        
        if should_mask:
            # Mask the value but keep the key
            if isinstance(value, (dict, list)):
                sanitized[key] = mask_value(value)
            else:
                sanitized[key] = "****"
        else:
            # For non-sensitive keys, recursively check nested structures
            if isinstance(value, dict):
                sanitized[key] = sanitize_audit_metadata(
                    db, current_user, action_type, entity_type, value
                )
            elif isinstance(value, list):
                # For lists, check each item
                sanitized[key] = [
                    sanitize_audit_metadata(
                        db, current_user, action_type, entity_type,
                        item if isinstance(item, dict) else None
                    ) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
    
    return sanitized

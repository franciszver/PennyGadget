"""
Standardized API Response Helpers
"""

from typing import Any, Optional
from datetime import datetime
import uuid


def success_response(
    data: Any,
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> dict:
    """Create a standardized success response"""
    return {
        "success": True,
        "data": data,
        "message": message,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid.uuid4())
        }
    }


def error_response(
    code: str,
    message: str,
    details: Optional[dict] = None,
    request_id: Optional[str] = None
) -> dict:
    """Create a standardized error response"""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details
        },
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id or str(uuid.uuid4())
        }
    }


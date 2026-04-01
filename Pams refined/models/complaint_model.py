from datetime import datetime

COMPLAINT_STATUS = ["open", "under_review", "resolved", "closed"]
COMPLAINT_TYPES = ["noise", "neighbour_dispute", "facility", "staff", "billing", "other"]

def complaint_schema(tenant_id, tenant_name, apartment_id, apartment_number,
                     location, complaint_type, subject, description, reported_by):
    return {
        "tenant_id": str(tenant_id),
        "tenant_name": tenant_name,
        "apartment_id": str(apartment_id),
        "apartment_number": apartment_number,
        "location": location,
        "complaint_type": complaint_type,
        "subject": subject,
        "description": description,
        "status": "open",
        "resolution_notes": None,
        "reported_by": reported_by,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "resolved_at": None
    }

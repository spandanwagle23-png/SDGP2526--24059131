from datetime import datetime

PRIORITY_LEVELS = ["Low", "Medium", "High", "Emergency"]
MAINTENANCE_STATUS = ["submitted", "investigating", "scheduled", "in_progress", "resolved", "cancelled"]

def maintenance_schema(tenant_id, tenant_name, apartment_id, apartment_number,
                       location, issue_title, issue_description, priority, reported_by):
    return {
        "tenant_id": str(tenant_id),
        "tenant_name": tenant_name,
        "apartment_id": str(apartment_id),
        "apartment_number": apartment_number,
        "location": location,
        "issue_title": issue_title,
        "issue_description": issue_description,
        "priority": priority,
        "status": "submitted",
        "assigned_to": None,
        "scheduled_date": None,
        "scheduled_time": None,
        "resolution_notes": None,
        "time_taken_hours": None,
        "cost": 0,
        "reported_by": reported_by,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "resolved_at": None
    }

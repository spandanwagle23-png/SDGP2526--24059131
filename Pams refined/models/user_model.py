from datetime import datetime

ROLES = ["admin", "front_desk", "finance_manager", "maintenance_staff", "manager", "tenant"]

def user_schema(username, password_hash, role, full_name, email, phone, location, created_by=None):
    return {
        "username": username,
        "password_hash": password_hash,
        "role": role,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "location": location,  # city/branch
        "is_active": True,
        "created_by": created_by,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

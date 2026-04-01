from datetime import datetime

def tenant_schema(ni_number, full_name, phone, email, occupation,
                  references, apartment_requirements, lease_period,
                  date_of_birth, emergency_contact, location, registered_by):
    return {
        "ni_number": ni_number,
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "occupation": occupation,
        "references": references,
        "apartment_requirements": apartment_requirements,
        "lease_period": lease_period,
        "date_of_birth": date_of_birth,
        "emergency_contact": emergency_contact,
        "location": location,
        "status": "active",
        "registered_by": registered_by,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

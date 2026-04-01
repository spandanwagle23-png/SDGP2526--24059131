from datetime import datetime

def lease_schema(tenant_id, tenant_name, apartment_id, apartment_number,
                 location, start_date, end_date, monthly_rent, deposit_amount, created_by):
    return {
        "tenant_id": str(tenant_id),
        "tenant_name": tenant_name,
        "apartment_id": str(apartment_id),
        "apartment_number": apartment_number,
        "location": location,
        "start_date": start_date,
        "end_date": end_date,
        "monthly_rent": monthly_rent,
        "deposit_amount": deposit_amount,
        "status": "active",   # active, expired, terminated
        "early_termination": None,
        "created_by": created_by,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

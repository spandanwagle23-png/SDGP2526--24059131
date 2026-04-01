from datetime import datetime

PAYMENT_STATUS = ["paid", "pending", "overdue", "partial"]
PAYMENT_TYPES = ["rent", "deposit", "early_termination_penalty", "maintenance_charge", "late_fee"]

def payment_schema(tenant_id, tenant_name, apartment_id, apartment_number,
                   lease_id, amount, due_date, payment_type, location, created_by):
    return {
        "tenant_id": str(tenant_id),
        "tenant_name": tenant_name,
        "apartment_id": str(apartment_id),
        "apartment_number": apartment_number,
        "lease_id": str(lease_id),
        "amount": amount,
        "amount_paid": 0,
        "due_date": due_date,
        "paid_date": None,
        "payment_type": payment_type,
        "status": "pending",
        "invoice_number": None,
        "card_last4": None,
        "location": location,
        "late_fee": 0,
        "notes": "",
        "created_by": created_by,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

def invoice_schema(payment_id, tenant_id, tenant_name, apartment_number,
                   amount, due_date, invoice_number, location):
    return {
        "invoice_number": invoice_number,
        "payment_id": str(payment_id),
        "tenant_id": str(tenant_id),
        "tenant_name": tenant_name,
        "apartment_number": apartment_number,
        "amount": amount,
        "due_date": due_date,
        "location": location,
        "issued_date": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }

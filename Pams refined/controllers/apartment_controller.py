from datetime import datetime, timedelta
from bson import ObjectId
import random
import string
from config.database import DatabaseConnection
from models.apartment_model import apartment_schema
from models.lease_model import lease_schema

class ApartmentController:
    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        self.apartments = self.db["apartments"]
        self.leases = self.db["leases"]
        self.tenants = self.db["tenants"]
        self.users = self.db["users"]

    def register_apartment(self, apartment_number, location, apartment_type, monthly_rent,
                           num_rooms, floor, size_sqft, amenities, created_by):
        if self.apartments.find_one({"apartment_number": apartment_number, "location": location}):
            return None, "Apartment already exists at this location."
        doc = apartment_schema(apartment_number, location, apartment_type, monthly_rent,
                               num_rooms, floor, size_sqft, amenities, created_by)
        result = self.apartments.insert_one(doc)
        return str(result.inserted_id), None

    def get_all_apartments(self, location=None, status=None):
        query = {}
        if location:
            query["location"] = location
        if status:
            query["status"] = status
        return list(self.apartments.find(query))

    def get_apartment_by_id(self, apt_id):
        return self.apartments.find_one({"_id": ObjectId(apt_id)})

    def update_apartment(self, apt_id, updates):
        updates["updated_at"] = datetime.utcnow()
        self.apartments.update_one({"_id": ObjectId(apt_id)}, {"$set": updates})
        return True, "Apartment updated."

    def assign_tenant(self, apt_id, tenant_id, tenant_name, start_date, end_date,
                      monthly_rent, deposit_amount, created_by):
        apt = self.apartments.find_one({"_id": ObjectId(apt_id)})
        if not apt:
            return None, "Apartment not found."
        if apt["status"] == "occupied":
            return None, "Apartment is already occupied."

        # Create lease
        doc = lease_schema(tenant_id, tenant_name, apt_id, apt["apartment_number"],
                           apt["location"], start_date, end_date, monthly_rent, deposit_amount, created_by)
        lease_result = self.leases.insert_one(doc)
        lease_id = str(lease_result.inserted_id)

        # Update apartment
        self.apartments.update_one({"_id": ObjectId(apt_id)}, {
            "$set": {"status": "occupied", "current_tenant_id": str(tenant_id), "updated_at": datetime.utcnow()}
        })
        # Update tenant
        self.tenants.update_one({"_id": ObjectId(tenant_id)}, {
            "$set": {"status": "active", "updated_at": datetime.utcnow()}
        })
        # Update user document (tenant login account)
        self.users.update_one(
            {"tenant_id": str(tenant_id)},
            {"$set": {"apartment_id": str(apt_id), "lease_id": lease_id, "updated_at": datetime.utcnow()}}
        )
        
        # Auto-generate monthly payment records for the lease period
        current_date = start_date
        while current_date < end_date:
            due_date = current_date + timedelta(days=30)
            if due_date > end_date:
                due_date = end_date
            
            # Generate invoice number
            inv_num = "INV-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Create payment record
            payment_doc = {
                "tenant_id": str(tenant_id),
                "tenant_name": tenant_name,
                "apartment_id": str(apt_id),
                "apartment_number": apt["apartment_number"],
                "lease_id": lease_id,
                "amount": monthly_rent,
                "amount_paid": 0,
                "due_date": due_date,
                "paid_date": None,
                "payment_type": "rent",
                "status": "pending",
                "invoice_number": inv_num,
                "card_last4": None,
                "location": apt["location"],
                "late_fee": 0,
                "notes": "",
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            self.db["payments"].insert_one(payment_doc)
            
            # Create invoice record
            invoice_doc = {
                "invoice_number": inv_num,
                "payment_id": None,
                "tenant_id": str(tenant_id),
                "tenant_name": tenant_name,
                "apartment_number": apt["apartment_number"],
                "amount": monthly_rent,
                "due_date": due_date,
                "location": apt["location"],
                "issued_date": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            self.db["invoices"].insert_one(invoice_doc)
            
            current_date = due_date
        
        return lease_id, None

    def vacate_apartment(self, apt_id):
        apt = self.apartments.find_one({"_id": ObjectId(apt_id)})
        if not apt:
            return False, "Apartment not found."
        tenant_id = apt.get("current_tenant_id")
        if tenant_id:
            self.tenants.update_one({"_id": ObjectId(tenant_id)}, {"$set": {"status": "inactive", "updated_at": datetime.utcnow()}})
            self.leases.update_one(
                {"apartment_id": str(apt_id), "status": "active"},
                {"$set": {"status": "expired", "updated_at": datetime.utcnow()}}
            )
        self.apartments.update_one({"_id": ObjectId(apt_id)}, {
            "$set": {"status": "available", "current_tenant_id": None, "updated_at": datetime.utcnow()}
        })
        return True, "Apartment vacated."

    def get_all_leases(self, location=None, status=None):
        query = {}
        if location:
            query["location"] = location
        if status:
            query["status"] = status
        return list(self.leases.find(query))

    def get_tenant_lease(self, tenant_id):
        return self.leases.find_one({"tenant_id": str(tenant_id), "status": {"$in": ["active", "terminating"]}})

    def get_occupancy_stats(self, location=None):
        query = {}
        if location:
            query["location"] = location
        total = self.apartments.count_documents(query)
        occupied = self.apartments.count_documents({**query, "status": "occupied"})
        available = self.apartments.count_documents({**query, "status": "available"})
        maintenance = self.apartments.count_documents({**query, "status": "maintenance"})
        return {"total": total, "occupied": occupied, "available": available, "maintenance": maintenance}

from datetime import datetime
from bson import ObjectId
import bcrypt
import random
import string
from config.database import DatabaseConnection
from models.tenant_model import tenant_schema

class TenantController:
    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        self.tenants = self.db["tenants"]
        self.leases = self.db["leases"]
        self.users = self.db["users"]

    def register_tenant(self, ni_number, full_name, phone, email, occupation,
                        references, apartment_requirements, lease_period,
                        date_of_birth, emergency_contact, location, registered_by):
        if self.tenants.find_one({"ni_number": ni_number}):
            return None, None, None, "A tenant with this NI number already exists."
        
        # Create tenant document
        doc = tenant_schema(ni_number, full_name, phone, email, occupation,
                            references, apartment_requirements, lease_period,
                            date_of_birth, emergency_contact, location, registered_by)
        result = self.tenants.insert_one(doc)
        tenant_id = str(result.inserted_id)
        
        # Generate username: firstname.lastinitial + random 3 digits
        names = full_name.strip().split()
        first_name = names[0].lower()
        last_initial = names[-1][0].lower() if len(names) > 1 else ""
        base_username = f"{first_name}.{last_initial}" if last_initial else first_name
        
        # Make username unique by adding random digits
        random_suffix = "".join(random.choices(string.digits, k=3))
        username = f"{base_username}{random_suffix}"
        
        # Check if username already exists
        counter = 0
        original_username = username
        while self.users.find_one({"username": username}) and counter < 100:
            random_suffix = "".join(random.choices(string.digits, k=3))
            username = f"{original_username}{random_suffix}"
            counter += 1
        
        # Generate temporary password
        temp_password = "Tenant@1"
        pw_hash = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt())
        
        # Create user document for tenant login
        user_doc = {
            "username": username,
            "password_hash": pw_hash,
            "role": "tenant",
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "location": location,
            "tenant_id": tenant_id,
            "apartment_id": None,
            "lease_id": None,
            "is_active": True,
            "created_by": registered_by,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        self.users.insert_one(user_doc)
        
        return tenant_id, username, temp_password, None

    def get_all_tenants(self, location=None, status=None):
        query = {}
        if location:
            query["location"] = location
        if status:
            query["status"] = status
        return list(self.tenants.find(query))

    def get_tenant_by_id(self, tenant_id):
        return self.tenants.find_one({"_id": ObjectId(tenant_id)})

    def get_tenant_by_ni(self, ni_number):
        return self.tenants.find_one({"ni_number": ni_number})

    def update_tenant(self, tenant_id, updates):
        updates["updated_at"] = datetime.utcnow()
        self.tenants.update_one({"_id": ObjectId(tenant_id)}, {"$set": updates})
        return True, "Tenant updated successfully."

    def remove_tenant(self, tenant_id):
        self.tenants.update_one({"_id": ObjectId(tenant_id)}, {"$set": {"status": "inactive", "updated_at": datetime.utcnow()}})
        return True, "Tenant record set to inactive."

    def request_early_termination(self, tenant_id, notice_date):
        """Tenant gives 1 month notice + 5% monthly rent penalty"""
        lease = self.leases.find_one({"tenant_id": str(tenant_id), "status": "active"})
        if not lease:
            return None, "No active lease found."
        penalty = lease["monthly_rent"] * 0.05
        self.leases.update_one(
            {"_id": lease["_id"]},
            {"$set": {
                "early_termination": {"notice_date": notice_date, "penalty": penalty},
                "status": "terminating",
                "updated_at": datetime.utcnow()
            }}
        )
        self.tenants.update_one({"_id": ObjectId(tenant_id)}, {"$set": {"status": "terminating", "updated_at": datetime.utcnow()}})
        return penalty, None

    def search_tenants(self, query_str, location=None):
        query = {
            "$or": [
                {"full_name": {"$regex": query_str, "$options": "i"}},
                {"email": {"$regex": query_str, "$options": "i"}},
                {"ni_number": {"$regex": query_str, "$options": "i"}},
                {"phone": {"$regex": query_str, "$options": "i"}}
            ]
        }
        if location:
            query["location"] = location
        return list(self.tenants.find(query))

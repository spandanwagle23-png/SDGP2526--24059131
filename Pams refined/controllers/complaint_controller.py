from datetime import datetime
from bson import ObjectId
from config.database import DatabaseConnection
from models.complaint_model import complaint_schema

class ComplaintController:
    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        self.complaints = self.db["complaints"]

    def submit_complaint(self, tenant_id, tenant_name, apartment_id, apartment_number,
                         location, complaint_type, subject, description, reported_by):
        doc = complaint_schema(tenant_id, tenant_name, apartment_id, apartment_number,
                               location, complaint_type, subject, description, reported_by)
        result = self.complaints.insert_one(doc)
        return str(result.inserted_id), None

    def get_all_complaints(self, location=None, status=None, tenant_id=None):
        query = {}
        if location:
            query["location"] = location
        if status:
            query["status"] = status
        if tenant_id:
            query["tenant_id"] = str(tenant_id)
        return list(self.complaints.find(query).sort("created_at", -1))

    def update_complaint_status(self, complaint_id, status, resolution_notes=None):
        updates = {"status": status, "updated_at": datetime.utcnow()}
        if resolution_notes:
            updates["resolution_notes"] = resolution_notes
        if status in ["resolved", "closed"]:
            updates["resolved_at"] = datetime.utcnow()
        self.complaints.update_one({"_id": ObjectId(complaint_id)}, {"$set": updates})
        return True, "Complaint updated."

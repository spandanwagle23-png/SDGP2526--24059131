from datetime import datetime
from bson import ObjectId
from config.database import DatabaseConnection
from models.maintenance_model import maintenance_schema

class MaintenanceController:
    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        self.requests = self.db["maintenance_requests"]

    def submit_request(self, tenant_id, tenant_name, apartment_id, apartment_number,
                       location, issue_title, issue_description, priority, reported_by):
        doc = maintenance_schema(tenant_id, tenant_name, apartment_id, apartment_number,
                                 location, issue_title, issue_description, priority, reported_by)
        result = self.requests.insert_one(doc)
        return str(result.inserted_id), None

    def get_all_requests(self, location=None, status=None, priority=None, tenant_id=None):
        query = {}
        if location:
            query["location"] = location
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if tenant_id:
            query["tenant_id"] = str(tenant_id)
        return list(self.requests.find(query).sort("created_at", -1))

    def get_request_by_id(self, req_id):
        return self.requests.find_one({"_id": ObjectId(req_id)})

    def assign_request(self, req_id, assigned_to, scheduled_date, scheduled_time):
        self.requests.update_one({"_id": ObjectId(req_id)}, {"$set": {
            "assigned_to": assigned_to,
            "scheduled_date": scheduled_date,
            "scheduled_time": scheduled_time,
            "status": "scheduled",
            "updated_at": datetime.utcnow()
        }})
        return True, "Request assigned and scheduled."

    def update_status(self, req_id, status):
        self.requests.update_one({"_id": ObjectId(req_id)}, {"$set": {
            "status": status,
            "updated_at": datetime.utcnow()
        }})
        return True, f"Status updated to {status}."

    def resolve_request(self, req_id, resolution_notes, time_taken_hours, cost):
        self.requests.update_one({"_id": ObjectId(req_id)}, {"$set": {
            "status": "resolved",
            "resolution_notes": resolution_notes,
            "time_taken_hours": time_taken_hours,
            "cost": cost,
            "resolved_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }})
        return True, "Maintenance request resolved."

    def get_maintenance_cost_report(self, location=None):
        query = {"status": "resolved"}
        if location:
            query["location"] = location
        resolved = list(self.requests.find(query))
        total_cost = sum(r.get("cost", 0) for r in resolved)
        total_hours = sum(r.get("time_taken_hours", 0) for r in resolved if r.get("time_taken_hours"))
        by_priority = {}
        for r in resolved:
            p = r.get("priority", "Unknown")
            by_priority[p] = by_priority.get(p, 0) + r.get("cost", 0)
        return {
            "total_resolved": len(resolved),
            "total_cost": round(total_cost, 2),
            "total_hours": round(total_hours, 2),
            "by_priority": by_priority
        }

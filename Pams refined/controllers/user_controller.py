from datetime import datetime
from bson import ObjectId
import bcrypt
from config.database import DatabaseConnection
from models.user_model import user_schema

class UserController:
    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        self.users = self.db["users"]

    def create_user(self, username, password, role, full_name, email, phone, location, created_by):
        if self.users.find_one({"username": username}):
            return None, "Username already exists."
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        doc = user_schema(username, pw_hash, role, full_name, email, phone, location, created_by)
        result = self.users.insert_one(doc)
        return str(result.inserted_id), None

    def get_all_users(self, location=None, role=None):
        query = {}
        if location:
            query["location"] = location
        if role:
            query["role"] = role
        return list(self.users.find(query, {"password_hash": 0}))

    def get_user_by_id(self, user_id):
        return self.users.find_one({"_id": ObjectId(user_id)}, {"password_hash": 0})

    def update_user(self, user_id, updates):
        updates["updated_at"] = datetime.utcnow()
        self.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
        return True, "User updated."

    def deactivate_user(self, user_id):
        self.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_active": False, "updated_at": datetime.utcnow()}})
        return True, "User deactivated."

    def activate_user(self, user_id):
        self.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_active": True, "updated_at": datetime.utcnow()}})
        return True, "User activated."

    def get_locations(self):
        return self.db["locations"].find({})

    def add_location(self, city, address, created_by):
        if self.db["locations"].find_one({"city": city}):
            return None, "Location already exists."
        doc = {"city": city, "address": address, "created_by": created_by, "created_at": datetime.utcnow()}
        result = self.db["locations"].insert_one(doc)
        return str(result.inserted_id), None

    def change_password(self, user_id, old_password, new_password):
        """User changes their own password with old password verification"""
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return False, "User not found."
        
        # Verify old password
        if not bcrypt.checkpw(old_password.encode(), user["password_hash"]):
            return False, "Current password is incorrect."
        
        # Hash new password
        new_pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
        
        # Update password
        self.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password_hash": new_pw_hash, "updated_at": datetime.utcnow()}}
        )
        return True, "Password changed successfully."

    def admin_reset_password(self, user_id, new_password):
        """Admin resets another user's password"""
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return False, "User not found."
        
        # Hash new password
        new_pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
        
        # Update password
        self.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password_hash": new_pw_hash, "updated_at": datetime.utcnow()}}
        )
        return True, f"Password reset for {user['full_name']}."
